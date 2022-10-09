import os
from settings import IMG_PATH, DOWNLOAD_PATH, EXCEPTION_PATH, DEVICE_ID, ADB_PATH
from utils import call

# 全局的状态信息
IMG_PATH_EXISTS = os.path.exists(IMG_PATH)
DOWNLOAD_PATH_EXISTS = os.path.exists(DOWNLOAD_PATH)
EXCEPTION_PATH_EXISTS = os.path.exists(EXCEPTION_PATH)
DEVICE_AVAILABLE = True if DEVICE_ID in call(f'"{ADB_PATH}" devices') else False
