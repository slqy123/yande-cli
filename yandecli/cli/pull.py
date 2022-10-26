import os
import re

import click

from database import *
from yandecli.tools.file_io import get_device_by_platform
from yandecli.tools.history import YandeHistory
from settings import STATUS, IMG_PATH, CLEAR
from yandecli.state_info import IMG_PATH_EXISTS


@click.command(help='pull a history from your mobile device and update the information')
@click.option('-a', '--all', '_all', is_flag=True, default=False, show_default=True,
              help='If this flag is added, pull all histories')
def pull(_all=False):
    assert IMG_PATH_EXISTS

    def pull_one(yande_history: YandeHistory):
        yande_history.set(commit=True, finish=True)
        dir_name = yande_history.get_folder_name()

        DEVICE = get_device_by_platform(yande_history.platform)
        device = DEVICE(dir_name)
        names = device.listdir()
        ids = [int(re.match(r'\d+', name).group()) for name in names]
        imgs = ss.query(Image).filter(Image.history == yande_history.history).all()
        count = 0
        imgs2remove = []
        for img in imgs:
            img.count += 1
            if img.id in ids:
                img.star += 1
            else:
                count += 1
                if img.star == 0:
                    img.status = STATUS.DELETED
                    imgs2remove.append(f'{IMG_PATH}/{img.name}')
                    print(f'{CLEAR}delete', img.name, end="", flush=True)
                else:
                    print(f'{CLEAR}filter', img.name, end='', flush=True)
        print(f'\n{len(imgs2remove)} images removed, {count - len(imgs2remove)} filtered')
        if imgs2remove:
            print("start removing files?(Y/n)", end="", flush=True)
            rm: str = input()
            if rm.strip().lower() == 'y' or not rm:
                rm_success_flag = True
                rm_failed_imgs = []

                for path in imgs2remove:
                    if os.path.exists(path):
                        os.remove(path)
                    else:
                        print(f'file {path} not exists')
                        rm_success_flag = 1 if rm_success_flag is True else rm_success_flag + 1
                        rm_failed_imgs.append(path)

                if rm_success_flag is True:
                    print('files remove successfully')
                else:
                    with open('file_not_exists.txt', 'w') as f:
                        f.write('\n'.join(rm_failed_imgs))
                    print(f'{rm_success_flag} files failed to delete, see ./file_not_exists.txt for details')

        device.remove()

    if _all:
        input('are you sure?')
        histories = YandeHistory.get_all_unfinished_histories()
        for history in histories:
            pull_one(YandeHistory.select(history))
    else:
        yande_history_ = YandeHistory.select()
        pull_one(yande_history_)

    ss.commit()