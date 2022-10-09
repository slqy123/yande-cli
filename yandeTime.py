import json
import os
import sys

import grequests
import datetime
import time

import tqdm
import re
from database import ss, Image, Tag
from utils import check_exists
from settings import IMG_PATH, TAGS, CLEAR, STATUS, YANDE_ALL_UPDATE_SIZE, UPDATE_FREQ


# TODO 不依靠json文件，可以选择使用pickle来存储
class BaseYandeSpider:
    METHOD = 'BASE'
    INFO_KEY = ['id', 'file_ext', 'tags', 'file_url', 'author', 'creator_id']

    def __init__(self, tags=None):
        '''mode 可选择 refresh, 定时更新  以及all, 下载全部'''

        self.headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 "
                                      "(KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36"}
        # self.original_url = "https://oreno.imouto.us"
        self.original_url = "https://yande.re"
        self.proxies = {
            'http': 'http://127.0.0.1:11223',
            'https': 'http://127.0.0.1:11223'
        }
        self.post_url = self.original_url + "/post.json"
        self.output_dir = "./_all/"
        self.failed_urls = []
        self.img_result = []
        self.urls = None

        self.total_count = 0
        self.created_img_count = 0
        self.updated_img_count = 0
        self.renamed_img_count = 0
        self.pushed_img_count = 0
        self.deleted_img_count = 0
        self.download_img_count = 0
        self.reset_img_count = 0
        self.no_update_img_count = 0
        self.request_interval = 3

        if not tags:
            self.tags = TAGS
        else:
            self.tags = tags

        self.idm = r'"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'

        self.today = str(datetime.date.today())
        self.timestamp = int(datetime.datetime.today().timestamp())
        self.log_fp = open(f'download_log/{self.METHOD}-{self.today}-{self.timestamp}.txt', 'w', encoding='utf8')

    def refresh(self):
        return []

    def request_infos(self, urls, failed=False):
        if failed:
            print("waiting to download failed urls")
            for i in range(self.request_interval):
                print(f"{CLEAR}{self.request_interval - i}", end='')
                time.sleep(1)
            print('')
        img_infos = []
        self.failed_urls = []
        rs = (grequests.get(url, headers=self.headers, proxies=self.proxies,
                            callback=self.request_callback) for url in urls)
        for res in grequests.map(rs, size=3, exception_handler=self.handle):
            try:
                resJson = json.loads(res.text)
            except:
                if res is None:
                    print('response is None')
                    continue
                print(f"请求{res.request.url}失败")
                self.failed_urls.append(res.request.url)
                continue
            if len(resJson) == 0 and self.METHOD == 'ID' and isinstance(resJson, list):
                id_ = int(res.request.url.split('id:')[1])
                img_infos.append({
                    'id': id_,
                    'status': 'deleted',
                    'flag_detail': {'reason': 'disappear'}
                })
                continue
            for item in resJson:
                img_infos.append({key: item.get(key, None) for key in self.INFO_KEY})
                if item['status'] == 'deleted':
                    img_infos[-1]['status'] = 'deleted'
                    img_infos[-1]['flag_detail'] = {'reason': item["flag_detail"]["reason"]}
                    print(f'deleted image id:{item["id"]} for reason: {item["flag_detail"]["reason"]}')

        if self.failed_urls:
            return img_infos + self.request_infos(self.failed_urls, failed=True)
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
        ss.commit()

        print(
            "total: %d, create: %d, pushed: %d, deleted: %d, downloading: "
            "%d, update: %d include %d renamed images and %d to reset, %d no need to update" %
            (self.total_count, self.created_img_count, self.pushed_img_count, self.deleted_img_count,
             self.download_img_count, self.updated_img_count, self.renamed_img_count, self.reset_img_count, self.no_update_img_count))
        return True

    def process_update_info(self, info):
        def update_one(image):
            for key in ('tags', 'author', 'creator_id', 'file_url'):
                if info.get(key, None) != getattr(image, key):
                    setattr(image, key, info.get(key, None))
            image.last_update_date = datetime.date.today()

            # 更新多对多表的tag_refs，在考虑要不一要加入这个表
            img.tag_refs.clear()
            for tag in img.tags.split(' '):
                tag_instance = Tag.get_unique(tag)
                img.tag_refs.append(tag_instance)

        assert info['id']
        check_res = check_exists(Image, id=info['id'])
        rt = bool(check_res)
        if rt:
            img = check_res
        else:
            img = Image(id=info['id'], star=0, status=STATUS.QUEUING)
            ss.add(img)

        if info.get('status') == 'deleted':
            img.status = STATUS.DELETED
            self.log_fp.write(f'deleted image id:{img.id}\n')
            self.deleted_img_count += 1
            return  # 此后的图片，info中的信息都全了，就可以获得新名字了

        new_name = f'{info["id"]} {info["author"]}.{info["file_ext"]}'
        new_name = new_name.translate(str.maketrans(r'/\:*?"<>|', "_________"))

        if not rt:
            update_one(img)
            img.name = new_name
            self.log_fp.write(f'create "{new_name}"\n')
            self.created_img_count += 1
            return  # 此后都是数据库中有结果的图片了

        if not img.history.finish:  # 图片已经被push了，不要干任何多余的事
            self.log_fp.write(f'image {img.id} already pushed\n')
            self.pushed_img_count += 1
            return

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

        old_path = os.path.join(IMG_PATH, img.name)
        new_path = os.path.join(IMG_PATH, new_name)
        img.name = new_name
        # 这个太浪费时间了
        # if not os.path.exists(old_path):
        #     if img.status == STATUS.EXISTS:
        #         msg = f'file not found "{old_path} redownload this image"\n'
        #         print(msg, end='')
        #         self.reset_img_count += 1
        #         self.log_fp.write(msg)
        #         img.status = STATUS.QUEUING
        #     return

        if img.name != new_name:  # 这意味着文件要重命名
            self.log_fp.write(f'rename to "{new_name}"\n')
            self.renamed_img_count += 1
            os.rename(old_path, new_path)
            return

    def handle(self, req, info):
        print(f"{req.url} 请求失败")
        self.failed_urls.append(req.url)

    @staticmethod
    def request_callback(req, *args, **kwargs):
        print(f"{req.url}请求成功")

    def __del__(self):
        self.log_fp.close()


class YandeDaily(BaseYandeSpider):
    METHOD = 'DAILY'

    def __init__(self, *args, **kwargs):
        super(YandeDaily, self).__init__(*args, **kwargs)
        self.settings = {}
    def refresh(self):
        begin = datetime.date(*[int(i) for i in self.settings['last'].split('-')])
        end = datetime.date.today()
        print(begin, end)
        input('confirm?')
        delta = datetime.timedelta(days=1)
        while begin <= end:
            for tag in self.tags:
                yield "%s?limit=1000&tags=%s+date:%s+" % (self.post_url, tag, begin)
            begin += delta

    def run(self):
        if not os.path.exists('infos.json'):
            print('This is your first time to run, so the current time will be set to be your last update time. '
                  'Next time when you run this command, all images with TAGS in this period will be updated')
            self.settings = {'max_id': 0}
            self.img_result = [{'id': 0}]
        else:
            with open('infos.json') as f:
                self.settings = json.loads(f.read())
            super(YandeDaily, self).run()

        ids = [info['id'] for info in self.img_result]

        self.settings['max_id'] = max(self.settings['max_id'],
                                      max(ids))
        self.settings['last'] = str(datetime.date.today())
        with open('infos.json', 'w') as f:
            json.dump(self.settings, f)


class YandeAll(BaseYandeSpider):
    METHOD = 'ALL'

    def __init__(self, *args, **kwargs):
        super(YandeAll, self).__init__(*args, **kwargs)
        self.page = 1
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


if __name__ == '__main__':
    pass
