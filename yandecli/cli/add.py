import click
import os

from settings import DOWNLOAD_PATH
from settings import STATUS, IMG_PATH
from yandecli.state_info import DOWNLOAD_PATH_EXISTS, IMG_PATH_EXISTS
from database import *


@click.command(help='Move download images from the download folder to image folder. \
if amount not given, default to move all images')
@click.argument('amount', type=int, default=0)
def add(amount: int = 0):
    from tqdm import trange
    import shutil
    assert DOWNLOAD_PATH_EXISTS and IMG_PATH_EXISTS
    all_download_imgs = os.listdir(DOWNLOAD_PATH)
    if amount > 0:
        all_download_imgs = all_download_imgs[: amount]
    with trange(len(all_download_imgs)) as t:
        for _, img in zip(t, all_download_imgs):
            checked_img = check_exists(Image, id=int(img.split('.')[0]))

            if not checked_img:
                print(f'delete img not found: {img}')
                os.remove(os.path.join(DOWNLOAD_PATH, img))
                ss.commit()
                return
            t.set_description(f'id={checked_img.id}')
            if img != checked_img.name:
                checked_img.name = img

            if checked_img.count != 0:
                print(f'error img {checked_img.id} count = {checked_img.count}')
                checked_img.count = 0

            assert checked_img.status == STATUS.DOWNLOADING and checked_img.count == 0

            src_path = os.path.join(DOWNLOAD_PATH, img)
            dst_path = os.path.join(IMG_PATH, img)
            shutil.move(src_path, dst_path)
            checked_img.status = STATUS.EXISTS

    ss.commit()
