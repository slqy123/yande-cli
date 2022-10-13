# -*- coding: UTF-8 -*-
import os

os.chdir(os.path.split(os.path.abspath(__file__))[0])
import re
from random import sample, randrange

import shutil
from tqdm import trange
import click

from database import *
from settings import *
from yandecli.status import *
from yandecli.history import YandeHistory
from utils import check_exists, call
from yandecli.yande_requests import YandeDaily, YandeId, YandeAll, TagTypeSpider
from yandecli.file_io import get_device_by_platform

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def main_group():
    pass


@click.command(help='Show the current information of your images')
def status():
    # TODO 显示当前连接情况settings里的
    total_num = ss.query(Image).count()
    status_count = ss.query(Image.status, func.count(1)).group_by(Image.status).all()
    count_list = [0, 0, 0, 0]
    for index, count in status_count:
        count_list[index] = count
    exist_num, deleted_num, queuing_num, downloading_num = count_list
    histories = YandeHistory.get_all_unfinished_histories()
    print(f"{total_num} images in total, {exist_num} exists, {deleted_num} deleted, "
          f"{queuing_num} waiting for download, {downloading_num} in download queue")

    if not ADB_AVAILABLE:
        print('ADB is not available, can\'t get detailed history information from your mobile device')
    choices = []
    for i, history in enumerate(histories):
        choices.append(f'[{i}]:{YandeHistory.get_description_from_history(history)}')
    print(f"{len(histories)} push histories are not updated, they are:")
    print(*choices, sep='\n')

    import json
    from datetime import date
    with open('infos.json') as f:
        settings = json.loads(f.read())
    last_download_date = date.fromisoformat(settings['last'])
    day_pass = date.today() - last_download_date
    print(f'last download date is {last_download_date} which is {day_pass.days} days ago')


@click.command(help='Push [AMOUNT] images to your mobile device [--num] times')
@click.argument('amount', type=click.INT, default=100)
@click.option('-n', '--num', 'times', type=click.INT, default=1, show_default=True,
              help='How many times you want to push')
@click.option('-t', '--tag', type=str, default='', help='specify the the tag of the image you want to push')
@click.option('-r', '--random', type=bool, is_flag=True, default=False, show_default=True,
              help='should images start from random id')
@click.option('-s', '--star', type=int, default=None, help='the star of image you want to push')
@click.option('-p', '--platform', type=click.Choice(['MOBILE', 'PC']), default='MOBILE', show_default=True,
              help='the platform you want to push to')
def push(amount: int, times: int, tag: str, random: bool, star: int = None, platform: str = 'MOBILE') -> None:
    assert ADB_AVAILABLE and IMG_PATH_EXISTS
    DEVICE = get_device_by_platform(PLATFORM(platform))
    def _push():
        min_count = star if star is not None else ss.query(func.min(Image.count)).filter(
            Image.star == Image.count, Image.history.has(finish=True)).first()[0]
        print(f"min count = {min_count}")
        img_query = ss.query(Image).filter(Image.star == Image.count,
                                           Image.status == STATUS.EXISTS,
                                           Image.count == min_count,
                                           Image.history.has(finish=True),
                                           Image.tags.contains(tag)  # 如果不传入tag，默认是空字符，此时等于没过滤
                                           )
        if random:
            pages = (img_query.count() // amount) + 1
            rand_page = randrange(0, pages)
            imgs = img_query.slice(rand_page * amount, (rand_page + 1) * amount).all()
            print(f'start from page {rand_page + 1}/{pages}')
        else:
            imgs = img_query.limit(amount).all()

        yande_history = YandeHistory.create_new(imgs, PLATFORM(platform))

        print(f"{len(imgs)} images in total from {yande_history.start} to {yande_history.end}")

        # target = f'{ADB_ROOT}/{yande_history.get_folder_name()}'
        # call(f'"{ADB_PATH}" -s {DEVICE_ID} shell "mkdir {target}"')
        device = DEVICE(yande_history.get_folder_name())
        with trange(yande_history.amount) as t:
            for i in t:
                img = imgs[i]
                tags = ' '.join([t.name for t in img.tag_refs if t.type not in (TAGTYPE.GENERAL, TAGTYPE.CHARACTER)])
                ext = img.name.rsplit('.', 1)[1]
                new_name = f'{img.id} {tags}.{ext}'
                new_name = new_name.translate(str.maketrans(r'/\:*?"<>|', "_________"))
                t.set_description(f"id={img.id}")
                # call_res = call(
                #     f'"{ADB_PATH}" -s {DEVICE_ID} push "{IMG_PATH}/{img.name}" "{target}/{new_name}"')
                # if '1 file pushed' in call_res:
                #     size = int(re.search(r"(\d+) bytes", call_res).group(1)) / MB
                #     t.set_postfix(size=f"{round(size, 2)}MB")
                # else:
                #     print('error! :: ', call_res)
                #     return None
                size = device.push(img.name, new_name)
                t.set_postfix(size=f"{round(size, 2)}MB")
                img.history = yande_history.history
        print(f'push complete')
        ss.commit()

    for _ in range(times):
        _push()


@click.command(help='pull a history from your mobile device and update the information')
@click.option('-a', '--all', '_all', is_flag=True, default=False, show_default=True,
              help='If this flag is added, pull all histories')
def pull(_all=False):
    assert ADB_AVAILABLE and IMG_PATH_EXISTS

    def pull_one(yande_history: YandeHistory):
        yande_history.set(commit=True, finish=True)
        dir_name = yande_history.get_folder_name()
        # target = f"{ADB_ROOT}/{dir_name}"
        # call(f'"{ADB_PATH}" -s {DEVICE_ID} shell "cd {target} && ls > out.txt"')
        # call(f'"{ADB_PATH}" -s {DEVICE_ID} pull {target}/out.txt ./')
        # call(f'"{ADB_PATH}" -s {DEVICE_ID} shell "rm {target}/out.txt"')
        #
        # with open('out.txt', encoding='utf-8') as fn:
        #     names = fn.read().split('\n')[0:-2]
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
                    print(CLEAR + 'delete', img.name, end="", flush=True)
                else:
                    print(CLEAR + 'filter', img.name, end='', flush=True)
        print(f'\n{len(imgs2remove)} images removed, {count - len(imgs2remove)} filtered')
        if imgs2remove:
            print("start removing files?(Y/n)", end="", flush=True)
            rm: str = input()
            if rm.strip().lower() == 'y' or rm == '':
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

        # call(f'"{ADB_PATH}" -s {DEVICE_ID} shell rm -rf {target}')
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


'''
@click.command()
@click.argument('count', type=int, default=0)
def trans(count: int = 0):
    # path = DOWNLOAD_PATH if not count else DOWNLOAD_PATH + '/all'
    path = DOWNLOAD_PATH
    confirm = False
    imgs = os.listdir(path)
    count = min(len(imgs), count)  # 防止图片数少于count时越界

    imgs = imgs[:count] if count else imgs
    img_count = len(imgs)
    print(img_count)
    for img in imgs:
        if not img.startswith('yande'):  # 图片没有id，一般是以2开头
            print('exception image: ', img)
            shutil.move(path + '/' + img, EXCEPTION_PATH + '/' + img)
            continue
        imgProcessRes = process_image(img)
        imgCheckRes = check_exists(Image, id=imgProcessRes['id'])
        if not imgCheckRes:  # 数据库中没有这个图片
            # 现在下载的时候已经会添加这个数据了，所以理论上应该一定会有，但是为了兼容旧的，留下来
            ss.add(Image(**imgProcessRes))

            print(imgProcessRes['id'], 'to add (with no item in database)')
            shutil.move(path + '/' + img,
                        IMG_PATH + '/' + imgProcessRes['name'])
        else:  # 一般都是else
            imgRes = imgCheckRes
            if imgRes.name:  # 考虑是图片发生了更新，还是为空项目添加名字
                img_count -= 1
                print(f'for id = {imgRes.id}')
                print(imgRes.name)
                print(imgProcessRes['name'])
                change = check_img_change(new_img=imgProcessRes['name'], exist_img=imgRes.name)
            else:  # 是空项目
                print(imgRes.id, 'to add')
                imgRes.name = imgProcessRes['name']
                imgRes.star = 0
                shutil.move(path + '/' + img,
                            IMG_PATH + '/' + imgProcessRes['name'])
                continue
            if change:  # 比较是否应该更新，也就是文件name是否更改
                imgRes.name = imgProcessRes['name']
                imgRes.tags = imgProcessRes['tags']
                print(imgProcessRes['id'], 'to update')
                shutil.move(path + '/' + img,
                            IMG_PATH + '/' + imgProcessRes['name'])
            else:
                if not os.path.exists(IMG_PATH + '/' + imgRes.name):
                    print('img not exists')
                    shutil.move(path + '/' + imgRes.name,
                                IMG_PATH + '/' + imgRes.name)
                else:
                    print('same image will be deleted')
                    if not confirm:
                        if input():
                            confirm = True
                    os.remove(path + '/' + img)

    print(f'{img_count} added in total')
    ss.commit()
'''


@click.command(help='Move download images from the download folder to image folder. \
if amount not given, default to move all images')
@click.argument('amount', type=int, default=0)
def add(amount: int = 0):
    assert DOWNLOAD_PATH_EXISTS and IMG_PATH_EXISTS
    all_download_imgs = os.listdir(DOWNLOAD_PATH)
    if amount > 0:
        all_download_imgs = all_download_imgs[: amount]
    with trange(len(all_download_imgs)) as t:
        for _, img in zip(t, all_download_imgs):
            checked_img = check_exists(Image, name=img)

            if not checked_img:
                print(f'delete img not found: {img}')
                os.remove(os.path.join(DOWNLOAD_PATH, img))
                return
            t.set_description(f'id={checked_img.id}')

            if checked_img.count != 0:
                print(f'error img {checked_img.id} count = {checked_img.count}')
                checked_img.count = 0

            assert checked_img.status == STATUS.DOWNLOADING and checked_img.count == 0

            src_path = os.path.join(DOWNLOAD_PATH, img)
            dst_path = os.path.join(IMG_PATH, img)
            shutil.move(src_path, dst_path)
            checked_img.status = STATUS.EXISTS

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


@click.command('dl', help='Add [AMOUNT] images to IDM\'s download query')
@click.argument('amount', type=int, default=0)
def download_yande_imgs(amount: int = 0):
    assert DOWNLOAD_PATH

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

                call(f'"{IDM_PATH}" /d "{img.file_url}" /p "{DOWNLOAD_PATH}" /f "{img.name}" /a /n')
                img.status = STATUS.DOWNLOADING

        call(f'"{IDM_PATH}" /s')
        ss.commit()

    start_idm_download()
    ss.commit()


@click.command()
@click.argument('amount', type=int, default=0)
@click.option('-m', '--mode', type=click.Choice(['id', 'tag', 'time', 'type']), default='time', show_default=True,
              help='Update mode')
@click.option('-t', '--tag', type=str, default='', help='Tags to update[optional]')
@click.option('-s', '--start', type=int, default=1, help='which page to start[optional]')
def update(amount: int = 0, mode: str = 'time', tag: str = '', start: int = 0):
    """
    Update to fetch the latest [AMOUNT] image's information

    there are four modes your can choose:

        id: update by the last update date of an image

        tag: update by the given tag, make sure to add --tag option if you use this mode

        time: update all images of default tags from last update time to now,
        if the option --tag is 'all', all images no matter what tags will be updated

        type: update the type of tags, use -t to give the type, it should be a integer, you can see the relation
        in settings.py
    """
    assert IMG_PATH_EXISTS

    if ss.query(Image).count():
        exists_img_query = ss.query(Image).filter(Image.status == STATUS.EXISTS)
        last_date = exists_img_query.order_by(Image.last_update_date.asc()).first().last_update_date
        img_query = exists_img_query.filter(Image.last_update_date == last_date)
    else:
        if mode != 'tag':
            print('First run this command, please update with "tag" mode')
            return

    if mode == 'id':
        if amount < 1:
            print("please input amount > 0")
            return
        ids = [img.id for img in img_query.limit(amount)]
        yande = YandeId(ids=ids)
        yande.run()
    elif mode == 'tag':
        def get_rand_tag() -> str:
            rand_img = img_query.filter(Image.tags != None).order_by(func.random()).first()
            if not rand_img:
                print('no proper tag found!')
                rand_img = ss.query(Image).filter(Image.tags != None).order_by(func.random()).first()
            tags = rand_img.tags.split(' ')
            print(tags, rand_img.id)
            rand_tag = sample(set(tags) & set(TAGS), 1)[0]
            print(f'choose img id={rand_img.id}, tag={rand_tag}')
            return rand_tag

        tag: str = tag if tag else get_rand_tag()
        if tag not in TAGS:
            user_input = input('this tag is not in the default tags, still want to update?(y/N)')
            if user_input.strip().lower() == 'n' or user_input.strip() == '':
                return

        yande = YandeAll(tags=[tag], from_page=start)
        yande.run()
    elif mode == 'time':
        tags = ('',) if tag == 'all' else None
        yande = YandeDaily(tags)
        yande.run()
    elif mode == 'type':
        tags = [''] if tag == 'all' else [int(tag)]
        yande = TagTypeSpider(tags)
        yande.run()


def test():
    all_img = ss.query(Image).all()
    for img in all_img:
        res = os.path.isfile(os.path.join(IMG_PATH, img.name))
        if (not res) and img.star != -1:
            print(img.id)


if __name__ == '__main__':
    main_group.add_command(push)
    main_group.add_command(pull)
    # main_group.add_command(trans)
    main_group.add_command(add)
    main_group.add_command(download_yande_imgs)
    main_group.add_command(status)
    main_group.add_command(update)
    main_group.add_command(clear)

    main_group()

    # while True:
    #     cmd = input('please input your command\n>>>').split()
    #     cmd_func = cmd[0]
    #     if cmd_func == 'push':
    #         push(int(cmd[1]))
    #     elif cmd_func == 'update':
    #         if cmd[-1] == 'all':
    #             update(_all=True)
    #         else:
    #             update()
    #     elif cmd_func == 'trans':
    #         if len(cmd) == 2:
    #             trans(int(cmd[1]))
    #             continue
    #         trans()
    #     elif cmd_func == 'dl':
    #         download_yande_imgs()
    #     elif cmd_func == 'quit':
    #         break
    #     else:
    #         input("test mod")
    #         test()
