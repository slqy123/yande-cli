import datetime
import json
import os
import time

import tqdm

from database import ss, Image, Tag
from settings import CLEAR, STATUS, YANDE_ALL_UPDATE_SIZE, UPDATE_FREQ, TAGTYPE, RATING, PROXIES
from utils import LazyImport
from yandecli.state_info import data

grequests = LazyImport('grequests')


# TODO 不依靠json文件，可以选择使用pickle来存储
class BaseYandeSpider:
    proxies = PROXIES
    METHOD = 'BASE'
    INFO_KEY = ['id', 'tags', 'file_url', 'author', 'creator_id', 'rating']  # file_ext 删去，因为好像只有yande才会有这个信息
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36"}
    request_interval = 3
    failed_urls = []

    def __init__(self, tags=None):
        """mode 可选择 refresh, 定时更新  以及all, 下载全部"""

        # self.original_url = "https://oreno.imouto.us"
        self.failed_urls = []
        self.img_result = []
        self.urls = None

        self.total_count = 0
        self.created_img_count = 0
        self.updated_img_count = 0
        self.deleted_img_count = 0
        self.download_img_count = 0
        self.no_update_img_count = 0

        self.instances2add = []

        self.status_data = data
        self.tags = tags or self.status_data.tags
        self.original_url = self.status_data.data.domain.URL
        self.post_url = f"{self.original_url}/post.json"

        self.today = str(datetime.date.today())
        self.timestamp = int(datetime.datetime.now().timestamp())
        self.log_fp = open(f'download_log/{self.METHOD}-{self.today}-{self.timestamp}.txt', 'w', encoding='utf8')

    def refresh(self):
        return []

    @classmethod
    def request_infos(cls, urls, failed=False):
        if failed:
            print("waiting to download failed urls")
            for i in range(cls.request_interval):
                print(f"{CLEAR}{cls.request_interval - i}", end='')
                time.sleep(1)
            print('')
        img_infos = []
        cls.failed_urls = []
        rs = (grequests.get(url, headers=cls.headers, proxies=cls.proxies,
                            callback=cls.request_callback) for url in urls)
        for res in grequests.map(rs, size=3, exception_handler=cls.handle):
            try:
                resJson = json.loads(res.text)
            except Exception as _:
                if res is None:
                    print('response is None')
                    continue
                print(f"请求{res.request.url}失败")
                cls.failed_urls.append(res.request.url)
                continue
            if len(resJson) == 0 and cls.METHOD == 'ID' and isinstance(resJson, list):
                id_ = int(res.request.url.split('id:')[1])
                img_infos.append({
                    'id': id_,
                    'status': 'deleted',
                    'flag_detail': {'reason': 'disappear'}
                })
                continue
            for item in resJson:
                img_infos.append({key: item.get(key, None) for key in cls.INFO_KEY})
                if item.get('status', None) == 'deleted':
                    img_infos[-1]['status'] = 'deleted'
                    img_infos[-1]['flag_detail'] = {'reason': item["flag_detail"]["reason"]}
                    print(f'deleted image id:{item["id"]} for reason: {item["flag_detail"]["reason"]}')

        if cls.failed_urls:
            return img_infos + cls.request_infos(cls.failed_urls, failed=True)
        else:
            return img_infos

    def run(self):
        self.urls = set(self.refresh())
        self.img_result = self.request_infos(self.urls)
        if not self.img_result:
            return False  # no image to download
        self.img_result = {item['id']: item for item in self.img_result}.values()
        self.total_count += len(self.img_result)

        with tqdm.trange(len(self.img_result)) as progress:
            for i, info in zip(progress, self.img_result):
                progress.set_description(f"id={info['id']}")
                self.process_update_info(info)

        ss.add_all(self.instances2add)
        self.instances2add = []
        ss.commit()

        print(
            "total: %d, create: %d, deleted: %d, downloading: "
            "%d, update: %d, %d no need to update" %
            (self.total_count, self.created_img_count, self.deleted_img_count,
             self.download_img_count, self.updated_img_count, self.no_update_img_count))
        return True

    def process_update_info(self, info):
        def update_one(image):
            if self.METHOD == 'DAILY' and (not (set(info['tags'].split(' ')) & self.status_data.tags)):
                image.held = True

            file_ext = info['file_url'].rsplit('.', 1)[1]
            image.name = f'{info["id"]}.{file_ext}'

            for key in ('author', 'creator_id', 'file_url'):
                setattr(image, key, info.get(key, None))
            setattr(image, "rating", RATING(info.get("rating", None)))
            image.last_update_date = datetime.date.today()

            # 更新多对多表的tag_refs，在考虑要不一要加入这个表
            if image.tags != info.get('tags'):
                setattr(image, 'tags', info.get('tags', None))
                image.tag_refs = [Tag.cache.get_unique(tag) for tag in image.tags.split(' ')]
                # self.instances2add.extend(image.tag_refs)

        assert info['id']
        check_res = Image.cache.check_exists(info['id'])
        rt = bool(check_res)
        if rt:
            img = check_res
        else:
            img = Image(id=info['id'], star=0, status=STATUS.QUEUING)
            self.instances2add.append(img)

        if info.get('status') == 'deleted':
            img.status = STATUS.DELETED
            self.log_fp.write(f'deleted image id:{img.id}\n')
            self.deleted_img_count += 1
            return  # 此后的图片，info中的信息都全了，就可以获得新名字了

        # new_name = new_name.translate(str.maketrans(r'/\:*?"<>|', "_________"))

        if not rt:
            update_one(img)
            self.log_fp.write(f'create "{img.name}"\n')
            self.created_img_count += 1
            return  # 此后都是数据库中有结果的图片了

        # if not img.history.finish:  # 图片已经被push了，不要干任何多余的事
        #     self.log_fp.write(f'image {img.id} already pushed\n')
        #     self.pushed_img_count += 1
        #     return

        if img.status == STATUS.DOWNLOADING:
            self.log_fp.write(f'image {img.id} is in download queue\n')
            self.download_img_count += 1
            return

        if (datetime.date.today() - img.last_update_date).days < UPDATE_FREQ:
            self.log_fp.write(f'image {img.id} is no need to update\n')
            self.no_update_img_count += 1
            return

        self.log_fp.write(f'update :{img.name}"\n')
        self.updated_img_count += 1
        update_one(img)

        # old_path = os.path.join(IMG_PATH, img.name)
        # new_path = os.path.join(IMG_PATH, new_name)
        # 这个太浪费时间了
        # if not os.path.exists(old_path):
        #     if img.status == STATUS.EXISTS:
        #         msg = f'file not found "{old_path} redownload this image"\n'
        #         print(msg, end='')
        #         self.reset_img_count += 1
        #         self.log_fp.write(msg)
        #         img.status = STATUS.QUEUING
        #     return

        # if img.name != new_name:  # 这意味着文件要重命名
        #     self.log_fp.write(f'rename to "{new_name}"\n')
        #     self.renamed_img_count += 1
        #     os.rename(old_path, new_path)
        #     return
    @classmethod
    def handle(cls, req, info=None):
        print(f"{req.url} 请求失败")
        cls.failed_urls.append(req.url)

    @staticmethod
    def request_callback(req, *args, **kwargs):
        print(f"{req.url}请求成功")

    def __del__(self):
        self.log_fp.close()


class YandeDaily(BaseYandeSpider):
    METHOD = 'DAILY'

    def refresh(self):
        begin = self.status_data.last_update_date
        end = datetime.date.today()
        print(begin, end)
        input('confirm?')
        delta = datetime.timedelta(days=1)
        while begin <= end:
            for tag in self.tags:
                yield f"{self.post_url}?limit=1000&tags={tag}+date:{begin}+"
            begin += delta

    def run(self):
        super(YandeDaily, self).run()
        self.status_data.last_update_date = datetime.date.today()
        self.status_data.save()


class YandeAll(BaseYandeSpider):
    METHOD = 'ALL'

    def __init__(self, from_page=1, *args, **kwargs):
        super(YandeAll, self).__init__(*args, **kwargs)
        self.page = from_page
        self.tag2dl = None
        self.batch_size = YANDE_ALL_UPDATE_SIZE

    def refresh(self):
        yield f"{self.post_url}?limit={self.batch_size}&tags={self.tag2dl}&page={self.page}"
        self.page += 1

    def run(self):
        for tag in self.tags:
            print(f'update tag = {tag}')
            self.tag2dl = tag
            while super(YandeAll, self).run():
                print('-' * 7)
            self.page = 1


# TODO: 如果请求太多的话还是分批比较好
class YandeId(BaseYandeSpider):
    METHOD = 'ID'

    def __init__(self, ids, *args, **kwargs):
        super(YandeId, self).__init__(*args, **kwargs)
        self.ids = ids

    def refresh(self):
        for id_ in self.ids:
            yield "%s?tags=id:%d" % (self.post_url, id_)


class TagTypeSpider(BaseYandeSpider):
    METHOD = 'TAGTYPE'
    INFO_KEY = ['id', 'name', 'type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = 1
        self.tag2dl = None
        self.batch_size = YANDE_ALL_UPDATE_SIZE

        self.post_url = f"{self.original_url}/tag.json"

    def refresh(self):
        yield f"{self.post_url}?limit={self.batch_size}&type={self.tag2dl}&page={self.page}"
        self.page += 1

    def run(self):
        for tag in self.tags:
            print(f'update tag = {tag}')
            self.tag2dl = tag
            while super(TagTypeSpider, self).run():
                print('-' * 7)
            self.page = 1

    def process_update_info(self, info):
        tag = Tag.cache.get_unique(info['name'])
        tag.type = TAGTYPE(info['type'])
        self.instances2add.append(tag)
