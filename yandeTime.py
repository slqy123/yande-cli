import json
import os
import sys

import grequests
import requests
from lxml import html
import datetime
import time
from subprocess import call
from pyperclip import copy
import shutil
import re
from database import ss, Image
from utils import check_exists
import os
from settings import IMG_PATH, TAGS, CLEAR

INFO_KEY = ['id', 'file_ext', 'tags', 'file_url', 'author', 'creator_id']


# TODO 不依靠json文件，可以选择使用pickle来存储
class BaseYandeSpider:
    METHOD = 'BASE'

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
            for i in range(30):
                print(f"{CLEAR}{30 - i}", end='')
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
            for item in resJson:
                img_infos.append({key: item[key] for key in INFO_KEY})

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
        # TODO 觉得没啥问题就把下面这个这删了吧
        assert len(set(info['file_url'] for info in self.img_result)) == len(self.img_result)
        self.total_count += len(self.img_result)

        for info in self.img_result:
            self.process_update_info(info)

        print("total: %d, create: %d, update: %d include %d renamed images" %
              (self.total_count, self.created_img_count, self.updated_img_count, self.renamed_img_count))
        return True
    def process_update_info(self, info):
        assert info['id']
        check_res = check_exists(Image, id=info['id'])
        rt = bool(check_res)
        if rt:
            img = check_res
        else:
            img = Image(id=info['id'], star=-2)
            ss.add(img)

        img.last_update_date = datetime.date.today()

        diff = False
        for key in ('tags', 'author', 'creator_id', 'file_url'):
            if info[key] != getattr(img, key):
                setattr(img, key, info[key])
                diff = True

        new_name = f'{img.id} {img.author}.{info["file_ext"]}'
        new_name = new_name.translate(str.maketrans(r'/\:*?"<>|', "_________"))
        if img.name != new_name:
            diff = True

        if not rt:
            img.name = new_name
            self.log_fp.write(f'create "{new_name}"\n')
            self.created_img_count += 1
            ss.commit()
            return

        if diff:
            assert img.name
            self.log_fp.write(f'update :{img.name}"\n')
            self.updated_img_count += 1

            if img.name != new_name:
                old_path = os.path.join(IMG_PATH, img.name)
                new_path = os.path.join(IMG_PATH, new_name)
                img.name = new_name

                if not os.path.exists(old_path):
                    if img.star >= 0:
                        msg = f'file not found "{img.name}"\n'
                        print(msg, end='')
                        self.log_fp.write(msg)
                        img.star = -2
                        ss.commit()
                    return

                if old_path != new_path:
                    self.log_fp.write(f'rename to "{new_name}"\n')
                    self.renamed_img_count += 1
                    os.rename(old_path, new_path)
                    img.name = new_name

        ss.commit()

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

        with open('infos.json') as f:
            self.settings = json.loads(f.read())

    def refresh(self):
        begin = datetime.date(*[int(i)
                                for i in self.settings['last'].split('-')])
        end = datetime.date.today()
        print(begin, end)
        input('confirm?')
        delta = datetime.timedelta(days=1)
        while begin <= end:
            for tag in self.tags:
                yield "%s?limit=1000&tags=%s+date:%s+" % (self.post_url, tag, begin)
            begin += delta

    def run(self):
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
        self.batch_size = 3

    def refresh(self):
        tag2dl = self.tags[0]
        # print("%s?limit=1000&tags=%s&page=%s" % (self.post_url, tag2dl, 1))
        # pages = int(input('with a limit of 1000, how many pages?: '))

        for i in range(self.page, self.page + self.batch_size):
            self.page += 1
            yield "%s?limit=1000&tags=%s&page=%s" % (self.post_url, tag2dl, str(i))

    def run(self):
        while super(YandeAll, self).run():
            print('-'*7)


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
