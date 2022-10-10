from enum import Enum

# 分别是图片存放位置，下载图片临时存放位置，和出错的图片存放位置（这个好像没啥用）
IMG_PATH = "G:/yande/images"
DOWNLOAD_PATH = 'F:/yande_dl'
EXCEPTION_PATH = 'G:/yande/Exceptions'

ADB_PATH = r'C:\scoop\adb\adb.exe'
# 运行 adb devices 第一列就是
DEVICE_ID = 'QKXUT20611001197'

# 更新的频率(天)，即如果一个图片的上次更新时间距离今天超过这个时间，则触发更新
UPDATE_FREQ = 30

# 默认的tag，update时会用
TAGS = ['bondage', 'loli', 'pee', 'vibrator',
        'anal', 'dildo', 'anal_beads', 'masturbation', 'yuri',
        'cunnilingus', 'fingering', 'pussy_juice', 'fellatio', 'handjob', 'nopan', 'nekomimi']

# 图片在手机中的存放位置
ROOT = "sdcard/ADM/.comic"

# 在根据tag请求图片时，每次请求的图片数量，最大为1000
YANDE_ALL_UPDATE_SIZE = 1000
assert YANDE_ALL_UPDATE_SIZE <= 1000

# constants
MB = 1024 * 1024
CLEAR = "\033[1K\r"


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
