# 全局的状态信息
import os
from settings import IMG_PATH, DOWNLOAD_PATH, DEVICE_ID, ADB_PATH
from utils import call
from typing import Set
from dataclasses import dataclass
from datetime import date

IMG_PATH_EXISTS = os.path.exists(IMG_PATH)
DOWNLOAD_PATH_EXISTS = os.path.exists(DOWNLOAD_PATH)
ADB_AVAILABLE = DEVICE_ID in call(f'"{ADB_PATH}" devices')


@dataclass
class _DATA:
    tags: Set[str]
    last_update_date: date


# 这是一个单例，请使用get_data方法进行创建
class Data:
    _instance: 'Data' = None

    def __init__(self):
        import pickle
        if os.path.exists('./data.pickle'):
            with open('./data.pickle', 'rb') as f:
                self.data: _DATA = pickle.load(f)
        else:
            print('first time to use, init data...')
            self.data: _DATA = _DATA(set(), date.today())

    @classmethod
    def get_data(cls):
        return cls._instance or cls()

    def save(self):
        import pickle
        with open('./data.pickle', 'wb') as f:
            pickle.dump(self.data, f)
