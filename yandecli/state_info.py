# 全局的状态信息
import os
from settings import DEVICE_ID, ADB_PATH, _DOMAIN, DOMAINS, DOMAIN
from utils import call
from typing import Set, Dict
from dataclasses import dataclass, field
from datetime import date
import pickle


@dataclass
class _DATA:
    tags: Dict[str, Set[str]] = field(default_factory=lambda: {i.name: set() for i in DOMAIN})
    last_update_date: Dict[str, date] = field(default_factory=lambda: {i.name: date.today() for i in DOMAIN})
    domain: _DOMAIN = DOMAINS['YANDE']


class Data:
    _instance: 'Data' = None

    def __init__(self):
        assert not self._instance
        if os.path.exists('./data.pickle'):
            with open('./data.pickle', 'rb') as f:
                self.data: _DATA = pickle.load(f)
                # lud = {i.name: set() for i in DOMAIN}
                # lud['YANDE'] = self.data.tags
                # self.data.tags = lud
                # self.save()
        else:
            print('first time to use, init data...')
            self.data: _DATA = _DATA()

    @property
    def last_update_date(self):
        if not (result := self.data.last_update_date.get(DOMAIN(self.data.domain).name, None)):
            result = self.data.last_update_date[DOMAIN(self.data.domain).name] = date.today()
        return result

    @last_update_date.setter
    def last_update_date(self, value: date):
        self.data.last_update_date[DOMAIN(self.data.domain).name] = value

    @property
    def tags(self):
        if not (result := self.data.tags.get(DOMAIN(self.data.domain).name, None)):
            result = self.data.tags[DOMAIN(self.data.domain).name] = set()
        return result

    @tags.setter
    def tags(self, value: Set[str]):
        self.data.tags[DOMAIN(self.data.domain).name] = value

    def save(self):
        import pickle
        with open('./data.pickle', 'wb') as f:
            pickle.dump(self.data, f)


data = Data()

IMG_PATH = data.data.domain.IMG_PATH
DOWNLOAD_PATH = data.data.domain.DOWNLOAD_PATH
URL = data.data.domain.URL
VIEW_PATH = data.data.domain.VIEW_PATH

IMG_PATH_EXISTS = os.path.exists(IMG_PATH)
DOWNLOAD_PATH_EXISTS = os.path.exists(DOWNLOAD_PATH)
ADB_AVAILABLE = DEVICE_ID in call(f'"{ADB_PATH}" devices')
