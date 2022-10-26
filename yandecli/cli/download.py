import os

import click

from database import *
from settings import DOWNLOAD_PATH, IDM_PATH, IMG_PATH
from settings import STATUS
from utils import call
from yandecli.state_info import IMG_PATH_EXISTS

@click.command('dl', help='Add [AMOUNT] images to IDM\'s download query')
@click.argument('amount', type=int, default=0)
def download_yande_imgs(amount: int = 0):
    assert DOWNLOAD_PATH
    from tqdm import trange

    def start_idm_download():
        nonlocal amount
        if amount == 0:
            total_amount = ss.query(Image).filter(Image.status == STATUS.QUEUING).count()
            user_cmd = input(f'Are you sure to download all images[{total_amount} in total](Y/n)?')
            if user_cmd.strip().lower() == 'n':
                return
            amount = total_amount

        imgs = list(ss.query(Image).filter(Image.status == STATUS.QUEUING).limit(amount))
        with trange(len(imgs)) as t:
            for i in t:
                img = imgs[i]
                t.set_description(f'id={img.id}')
                assert img.name
                assert img.file_url

                # call_in_bg(f'"{IDM_PATH}" /d "{img.file_url}" /p "{DOWNLOAD_PATH}" /f "{img.name}" /a /n')
                call(f'"{IDM_PATH}" /d "{img.file_url}" /p "{DOWNLOAD_PATH}" /f "{img.name}" /a /n')
                img.status = STATUS.DOWNLOADING

        call(f'"{IDM_PATH}" /s')
        ss.commit()

    start_idm_download()
    ss.commit()


@click.command(help='clear the images that are still in downloading')
def clear():
    assert IMG_PATH_EXISTS
    for img in ss.query(Image).filter(Image.status == STATUS.DOWNLOADING):
        if os.path.exists(os.path.join(IMG_PATH, img.name)):
            print(f'exists {img.name}')
            img.status = STATUS.EXISTS
        else:
            print(f'not found {img.name}')
            img.status = STATUS.QUEUING
    ss.commit()
