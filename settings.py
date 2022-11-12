from enum import Enum
from dataclasses import dataclass
from typing import Mapping


# 分别是网站网址，图片存放位置，下载图片临时存放位置，和push到PC中的图片的存放位置（此位置需与IMG_PATH位于相同盘符下）
@dataclass
class _DOMAIN:
    URL: str
    IMG_PATH: str
    DOWNLOAD_PATH: str
    VIEW_PATH: str


# 增加此处配置的同时，要对下方Enum里的DOMAIN的配置也进行增加
DOMAINS: Mapping[str, _DOMAIN] = {
    'YANDE': _DOMAIN(
        URL='https://yande.re',
        IMG_PATH="G:/yande/images",
        DOWNLOAD_PATH='F:/yande_dl',
        VIEW_PATH='G:/yande/view'
    ),
    'KONACHAN': _DOMAIN(
        URL='https://konachan.com',
        IMG_PATH="G:/yande/others/kona",
        DOWNLOAD_PATH='F:/kona_dl',
        VIEW_PATH='G:/yande/kona_view'
    ),
    'LOLIBOORU': _DOMAIN(
        URL='https://lolibooru.moe',
        IMG_PATH="G:/yande/others/lolibooru",
        DOWNLOAD_PATH='F:/lolibooru_dl',
        VIEW_PATH='G:/yande/lolibooru_view'
    ),

}

# 你的IDM路径和ADB路径，如果已经加入环境变量，直接写成程序名称即可
IDM_PATH = r'C:\Program Files (x86)\Internet Download Manager\IDMan.exe'
# ADB_PATH = r'C:\scoop\adb\adb.exe'
ADB_PATH = 'adb'
# 运行 adb devices 第一列就是
DEVICE_ID = 'QKXUT20611001197'

# 更新的频率(天)，在update时，即如果一个图片的上次更新时间距离今天超过这个时间，则触发更新
UPDATE_FREQ = 7

# 此处设置你的代理
PROXIES = {
    'http': 'http://127.0.0.1:11223',
    'https': 'http://127.0.0.1:11223'
}

# 默认的tag，update时可能会用
# TAGS = ['bondage', 'loli', 'pee', 'vibrator',
#         'anal', 'dildo', 'anal_beads', 'masturbation', 'yuri',
#         'cunnilingus', 'fingering', 'pussy_juice', 'fellatio',
#         'handjob', 'nopan', 'nekomimi', 'skirt_lift', 'tagme']

# 图片在手机中的存放位置
# 小提示：在文件夹名称前加 '.' 可以让这个文件夹下的内容不被qq，相册等软件探测到
ADB_ROOT = "sdcard/ADM/.comic"

# 在根据tag请求图片时，每次请求的图片数量，最大为1000
YANDE_ALL_UPDATE_SIZE = 1000

# constants
MB = 1024 * 1024
CLEAR = "\033[1K\r"


# Enums
class STATUS:
    EXISTS = 0
    DELETED = 1
    QUEUING = 2
    DOWNLOADING = 3


class TAGTYPE(Enum):
    GENERAL = 0
    ARTIST = 1
    COPYRIGHT = 3
    CHARACTER = 4
    CIRCLE = 5
    FAULTS = 6


class RATING(Enum):
    SAFE = 's'
    QUESTIONABLE = 'q'
    EXPLICIT = 'e'


class PLATFORM(Enum):
    MOBILE = 'MOBILE'
    PC = 'PC'


class DOMAIN(Enum):
    YANDE = DOMAINS['YANDE']
    KONACHAN = DOMAINS['KONACHAN']
    LOLIBOORU = DOMAINS['LOLIBOORU']


assert YANDE_ALL_UPDATE_SIZE <= 1000
