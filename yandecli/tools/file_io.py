import os

from settings import ADB_PATH, DEVICE_ID, ADB_ROOT, MB, PLATFORM
from yandecli.state_info import IMG_PATH, VIEW_PATH
from utils import call
import re
import shutil


class BaseIO:
    platform = None

    def __init__(self, folder_name):
        self.folder = folder_name
        self.folder_path = f'{ADB_ROOT if self.platform == PLATFORM.MOBILE else VIEW_PATH}/{self.folder}'
        self.mkdir()

    def mkdir(self):
        pass

    def push(self, img_name: str, new_name: str = '') -> float:
        pass

    def listdir(self):
        pass

    def remove(self):
        pass


class ADB(BaseIO):
    platform = PLATFORM.MOBILE

    @staticmethod
    def _execute(*args: str) -> str:
        return call((ADB_PATH, '-s', DEVICE_ID, *args))

    def mkdir(self):
        self._execute('shell', f'mkdir -p "{self.folder_path}"')

    def push(self, img_name: str, new_name: str = '') -> float:
        res = self._execute('push', f'{IMG_PATH}/{img_name}', f'{self.folder_path}/{new_name}')
        size = int(re.search(r"(\d+) bytes", res)[1]) / MB
        return round(size, 2)

    def listdir(self):
        self._execute('shell', f'cd "{self.folder_path}" && ls > out.txt')
        self._execute('pull', f'{self.folder_path}/out.txt', './')
        self._execute('shell', f'rm "{self.folder_path}/out.txt"')

        with open('out.txt', encoding='utf-8') as fn:
            return fn.read().split('\n')[:-2]

    def remove(self):
        self._execute('shell', f'rm -rf "{self.folder_path}"')


class OS(BaseIO):
    platform = PLATFORM.PC

    def mkdir(self):
        os.makedirs(self.folder_path, exist_ok=True)

    def push(self, img_name: str, new_name: str = '') -> float:
        os.link(f'{IMG_PATH}/{img_name}', f'{self.folder_path}/{new_name}')
        size = os.path.getsize(f'{IMG_PATH}/{img_name}') / MB
        return round(size, 2)

    def listdir(self):
        return os.listdir(self.folder_path)

    def remove(self):
        shutil.rmtree(self.folder_path)


def get_device_by_platform(platform: PLATFORM):
    return ADB if platform == PLATFORM.MOBILE else OS
