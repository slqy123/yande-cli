# -*- coding: UTF-8 -*-
import os
os.chdir(os.path.split(__file__)[0])
import re
import shutil
import sys

from sqlalchemy.sql import func
from sqlalchemy import or_, not_
from database import *
from settings import *
from datetime import date
from tqdm import tqdm, trange
import click
import inquirer
# from subprocess import call 重新定义了一个call函数，会返回输出的内容
from utils import *

import time

from yandeTime import YandeDaily, YandeId, YandeAll

root = "sdcard/ADM/.comic"


def call(command):
    return os.popen(command).read()


def get_description_from_trace(trace):
    trace_path = get_folder_name_from_trace(trace)
    img_num = int(call(f'adb2 -s {DEVICE_ID} shell "cd {root}/{trace_path} && ls -l |grep ^-|wc -l"'))
    return f"id={trace.id} pushed at {str(trace.date)} "\
           f"from {trace.start} to {trace.end}({img_num}/{trace.amount})"


@click.group()
def main_group():
    pass


def update_star(file_name, trace_id):
    """
    :param file_name: 存放所有图片文件的文件名
    :param trace_id: 对应的history_id
    :return: 更新阅读数据
    """
    with open(file_name, encoding='utf-8') as fn:
        content = fn.read().split('\n')[1:-1]
    ids = set([int(s.split(' ')[1]) for s in content])
    imgs = ss.query(Image).filter(Image.history_id == trace_id).all()
    count = 0
    imgs2remove = []
    for img in imgs:
        img.count += 1
        if img.id in ids:
            img.star += 1
        else:
            count += 1
            if img.star == 0:
                img.star = -1
                imgs2remove.append(f'{IMG_PATH}/{img.name}')
                print(CLEAR + 'delete', img.name, end="", flush=True)
            else:
                print(CLEAR + 'filter' + img.name, end='', flush=True)
    print(f'\n{count} images to be removed in total')
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
        
        ss.commit()


@click.command()
def status():
    total_num = ss.query(Image).count()
    exist_num = ss.query(Image).filter(Image.star >= 0).count()
    traces = ss.query(History).filter(History.finish == False).all()

    import json
    from datetime import date
    with open('infos.json') as f:
        settings = json.loads(f.read())
    last_download_date = date.fromisoformat(settings['last'])
    day_pass = date.today() - last_download_date
    choices = []
    for i, trace in enumerate(traces):
        choices.append(f'[{i}]:{get_description_from_trace(trace=trace)}')

    print(f"{total_num} images in total, {exist_num} exists, {total_num - exist_num} are deleted")
    print(f"{len(traces)} push histories are not updated, they are:")
    print(*choices, sep='\n')
    print(f'last download date is {last_download_date} which is {day_pass.days} days ago')


@click.command()
@click.argument('amount', type=click.INT)
@click.option('-t', '--times', type=click.INT, default=1)
def push(amount: int, times: int) -> None:
    def _push():
        min_count = ss.query(func.min(Image.count)).filter(
            Image.star == Image.count, Image.history.has(finish=True)).first()[0]
        print(f"min count = {min_count}")
        imgs = list(ss.query(Image).filter(Image.star == Image.count,
                                           Image.count == min_count,
                                           Image.history.has(finish=True)
                                           ).limit(amount))

        minId = imgs[0].id
        maxId = imgs[-1].id
        length = len(imgs)
        today = date.today()
        trace = History(
            date=today,
            start=minId,
            end=maxId,
            amount=length
        )
        ss.add(trace)
        ss.commit()

        print(f"{len(imgs)} images in total from {minId} to {maxId}")

        target = f'{root}/{get_folder_name_from_trace(trace)}'
        call(f'adb2 -s {DEVICE_ID} shell "mkdir {target}"')
        with trange(length) as t:
            for i in t:
                img = imgs[i]
                img_id = get_id_from_file_name(img.name)
                t.set_description(f"id={img_id}")
                call_res = call(f'adb2 -s {DEVICE_ID} push "{IMG_PATH}/{img.name}" "{target}/{img.name}"')
                if '1 file pushed' in call_res:
                    size = int(re.search(r"(\d+) bytes", call_res).group(1)) / MB
                    t.set_postfix(size=f"{round(size, 2)}MB")
                else:
                    print('error! :: ', call_res)
                    return None
                img.history_id = trace.id
        print(f'{length} pushed')
        ss.commit()

    for _ in range(times):
        _push()


def history_select(_all):
    history = ss.query(History).filter(History.finish == False, History.id > 0).all()
    choices = []
    for i, trace in enumerate(history):
        choices.append(f'[{i}]:{get_description_from_trace(trace=trace)}')

    if _all:
        return history
    else:
        question = [
            inquirer.List(
                'choice',
                message='which history do you want to update?',
                choices=choices
            )
        ]
        ans = inquirer.prompt(question)
        index = re.match(r'\[(\d+)\]', ans['choice']).group(1)
        trace = history[int(index)]
        return trace


# def clear():
#     trace = history_select(_all=False)
#     ss.query(Image).filter_by(history_id=trace.id).update({
#         'history_id': 0
#     })
#     ss.delete(trace)

@click.command()
@click.option('-a', '--all', '_all', is_flag=True, default=False, show_default=True)
def update(_all=False):
    def update_one(_trace):
        ss.add(_trace)
        _trace.finish = True
        dir_name = get_folder_name_from_trace(_trace)
        target = f"{root}/{dir_name}"
        call(f'adb2 -s {DEVICE_ID} shell "cd {target} && ls > out.txt && exit"')
        call(f'adb2 -s {DEVICE_ID} pull {target}/out.txt ./')
        call(f'adb2 -s {DEVICE_ID} shell "rm {target}/out.txt"')

        update_star('out.txt', _trace.id)

        call(f'adb2 -s {DEVICE_ID} shell rm -rf {target}')

    if _all:
        input('are you sure?')
        history = history_select(_all=True)
        for trace in history:
            update_one(trace)
    else:
        trace = history_select(_all=False)
        update_one(trace)

    ss.commit()


@click.command()
@click.argument('count', type=int, default=0)
def trans(count=0):
    path = DOWNLOAD_PATH if not count else DOWNLOAD_PATH + '/all'
    confirm = False
    imgs = os.listdir(path)
    count = min(len(imgs), count)  # 防止图片数少于count时越界
    if 'all' in imgs:
        imgs.remove('all')
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


@click.command('dl')
@click.argument('method', type=click.Choice([
    'daily', 'all', 'id'
]), default='daily')
@click.option('-t', '--tag', type=str, default='')
# @click.option('-i', '--id', '_id', type=int, default=0)
def download_yande_imgs(method: str, tag: str = ''):
    def add_item(img_id, img_url) -> bool:
        """
        :param img_id:
        :param img_url:
        :return: True if img exists else False
        """
        check_res = check_exists(Image, id=img_id)
        if check_res:
            check_res.url = img_url
            return True
        else:
            new_img = Image(id=img_id, url=img_url, star=-1)
            ss.add(new_img)
            return False

    typ = method
    if typ == 'daily':
        yande = YandeDaily(add_database_cb=add_item)
    elif typ == 'all':
        assert tag
        yande = YandeAll(add_database_cb=add_item, tags=[tag])
    elif typ == 'id':
        yande = YandeId(add_database_cb=add_item)
    else:
        return
    yande.run()
    ss.commit()


def test():
    all_img = ss.query(Image).all()
    for img in all_img:
        res = os.path.isfile(os.path.join(IMG_PATH, img.name))
        if (not res) and img.star != -1:
            print(img.id)


# TODO 这个还是可以优化一下

if __name__ == '__main__':
    assert os.path.exists(IMG_PATH)
    assert os.path.exists(DOWNLOAD_PATH)
    assert os.path.exists(EXCEPTION_PATH)

    device_list = call('adb2 devices')
    if DEVICE_ID not in device_list:
        print('no devices found!')
        sys.exit(-1)
    main_group.add_command(push)
    main_group.add_command(update)
    main_group.add_command(trans)
    main_group.add_command(download_yande_imgs)
    main_group.add_command(status)

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
