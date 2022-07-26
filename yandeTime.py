import json
import os

import grequests
import requests
from lxml import html
import datetime
import time
from subprocess import call, Popen
from pyperclip import copy
import shutil
import re


class YandeSpider:
    def __init__(self, tags=None, need_json=False, add_database_cb=None):
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
        self.add_database_cb = add_database_cb
        with open('infos.json') as f:
            self.settings = json.loads(f.read())
        if not tags:
            self.tags = ['bondage', 'loli', 'pee', 'vibrator',
                         'anal', 'dildo', 'anal_beads', 'masturbation', 'yuri',
                         'cunnilingus', 'fingering', 'pussy_juice']
        else:
            self.tags = tags
        self.today = str(datetime.date.today())
        self.idm = r'"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"'
        self.need_json = need_json

    def refresh(self):
        begin = datetime.date(*[int(i)
                                for i in self.settings['last'].split('-')])
        end = datetime.date.today()
        print(begin, end)
        input('confirm?')
        delta = datetime.timedelta(days=1)
        while begin <= end:
            for tag in self.tags:
                yield "%s?limit=200&tags=%s+date:%s+" % (self.post_url, tag, begin)
            begin += delta

    def request_infos(self, urls, failed=False):
        if failed:
            print("waiting to download failed urls")
            for i in range(30):
                print(f"\r{30 - i}", end='')
                time.sleep(1)
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
                img_infos.append({"id": item['id'],
                                  'file_ext': item['file_ext'],
                                  'tags': item['tags'],
                                  'file_url': item['file_url']})

        if self.failed_urls:
            return img_infos + self.request_infos(self.failed_urls, failed=True)
        else:
            return img_infos

    def run(self):
        urls = set(self.refresh())
        img_infos = self.request_infos(urls)
        if self.add_database_cb:
            for img_id, img_url in set((item['id'], item['file_url']) for item in img_infos):
                self.add_database_cb(img_id=img_id, img_url=img_url)
        urls = set([info['file_url'] for info in img_infos])
        print(len(urls))
        copy('\n'.join(urls))
        call(self.idm)

        ids = [info['id'] for info in img_infos]
        if self.need_json:
            self.settings['max_id'] = max(self.settings['max_id'],
                                          max(ids))
            self.settings['last'] = str(datetime.date.today())
            with open('infos.json', 'w') as f:
                json.dump(self.settings, f)

    def handle(self, req, info):
        print(f"{req.url} 请求失败")
        self.failed_urls.append(req.url)

    @staticmethod
    def request_callback(req, *args, **kwargs):
        print(f"{req.url}请求成功")


class YandeAll(YandeSpider):
    def refresh(self):
        tag = self.tags[0]
        print("%s?limit=1000&tags=%s&page=%s" % (self.post_url, tag, 1))
        pages = int(input('with a limit of 1000, how many pages?: '))

        for i in range(1, pages + 1):
            yield "%s?limit=1000&tags=%s&page=%s" % (self.post_url, tag, str(i))


# TODO: 如果请求太多的话还是分批比较好
class YandeId(YandeSpider):
    def refresh(self):
        with open('del.txt') as f:
            contents = f.read().split('\n')
            _ids = [int(c) for c in contents]
            for _id in _ids:
                yield "%s?limit=200&tags=id:%d" % (self.post_url, _id)


if __name__ == '__main__':
    typ = input("what kind of method you want: ")
    if typ == 'daily':
        yande = YandeSpider(need_json=True)
    elif typ == 'all':
        tag = input('the tag you want: ')
        yande = YandeAll([tag])
    elif typ == 'id':
        yande = YandeId()
    yande.run()
