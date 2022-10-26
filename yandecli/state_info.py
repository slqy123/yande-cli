# 全局的状态信息
import os
from settings import IMG_PATH, DOWNLOAD_PATH, DEVICE_ID, ADB_PATH
from utils import call

IMG_PATH_EXISTS = os.path.exists(IMG_PATH)
DOWNLOAD_PATH_EXISTS = os.path.exists(DOWNLOAD_PATH)
ADB_AVAILABLE = DEVICE_ID in call(f'"{ADB_PATH}" devices')