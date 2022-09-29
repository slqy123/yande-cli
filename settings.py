# 分别是图片存放位置，下载图片临时存放位置，和出错的图片存放位置（这个好像没啥用）
IMG_PATH = "G:/yande/images"
DOWNLOAD_PATH = 'F:/yande_dl'
EXCEPTION_PATH = 'G:/yande/Exceptions'

# 运行 adb devices 第一列就是
DEVICE_ID = 'QKXUT20611001197'

# 默认的tag，update时会用
TAGS = ['bondage', 'loli', 'pee', 'vibrator',
        'anal', 'dildo', 'anal_beads', 'masturbation', 'yuri',
        'cunnilingus', 'fingering', 'pussy_juice', 'fellatio', 'handjob', 'nopan']

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
