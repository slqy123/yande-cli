# -*- coding: UTF-8 -*-
import re
import shutil
import sys

from sqlalchemy.sql import func
from sqlalchemy import or_, not_
from database import *
from settings import *
from datetime import date
from tqdm import tqdm, trange

# from subprocess import call 重新定义了一个call函数，会返回输出的内容
from utils import *

import os
import time

from yandeTime import YandeSpider, YandeId, YandeAll

root = "sdcard/ADM/.comic"


def call(command):
    return os.popen(command).read()


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
                print('delete', img.name)
            else:
                print('filter' + img.name)
    print(f'{count} images to be removed in total')
    print("start removing files?")
    input()
    for path in imgs2remove:
        if os.path.exists(path):
            os.remove(path)
        else:
            print(f'file {path} not exists')
    ss.commit()


def push(amount):
    # 想个办法解决多次push会重复的问题（目前用last_id解决）
    # 可以加个字段(已用此方法解决)

    # last_id = History.query.order_by(History.date).all()[-1].end
    min_count = ss.query(func.min(Image.count)).filter(Image.star == Image.count).first()[0]
    print(f"min count = {min_count}")
    # if not ss.query(Image).filter(Image.id > last_id).all():
    #     last_id = 0
    imgs = list(ss.query(Image).filter(Image.star == Image.count,
                                       # Image.id > last_id,
                                       Image.count == min_count,
                                       Image.history.has(finish=True)
                                       ).limit(amount))
    print(f"{len(imgs)} images in total")

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

    target = f'{root}/{get_folder_name_from_trace(trace)}'
    call(f'adb2 shell "mkdir {target}')
    with trange(length) as t:
        for i in t:
            img = imgs[i]
            img_id = get_id_from_file_name(img.name)
            t.set_description(f"id={img_id}")
            call_res = call(f'adb2 push "{IMG_PATH}/{img.name}" "{target}/{img.name}"')
            if '1 file pushed' in call_res:
                size = int(re.search(r"(\d+) bytes", call_res).group(1)) / MB
                t.set_postfix(size=f"{round(size, 2)}MB")
            else:
                print('error! :: ', call_res)
                return None
            img.history_id = trace.id
    print(f'{length} pushed')
    ss.commit()


def history_select(_all):
    history = ss.query(History).filter(History.finish == False, History.id > 0).all()
    for i, trace in enumerate(history):
        print(f"[{i}]:id={trace.id} pushed at {str(trace.date)} from {trace.start} to {trace.end}")

    if _all:
        return history
    else:
        index = int(input('input the index you want to update: '))
        trace = history[index]
        return trace


# def clear():
#     trace = history_select(_all=False)
#     ss.query(Image).filter_by(history_id=trace.id).update({
#         'history_id': 0
#     })
#     ss.delete(trace)

def update(_all=False):
    def update_one(_trace):
        ss.add(_trace)
        _trace.finish = True
        dir_name = get_folder_name_from_trace(_trace)
        target = f"{root}/{dir_name}"
        call(f'adb2 shell "cd {target} && ls > out.txt && exit"')
        call(f'adb2 pull {target}/out.txt ./')
        call(f'adb2 shell "rm {target}/out.txt"')

        update_star('out.txt', _trace.id)

        call(f'adb2 shell rm -rf {target}')

    if _all:
        input('are you sure?')
        history = history_select(_all=True)
        for trace in history:
            update_one(trace)
    else:
        trace = history_select(_all=False)
        update_one(trace)

    ss.commit()


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


def download_yande_imgs():
    def add_empty_item(img_id, img_url):
        check_res = check_exists(Image, id=img_id)
        if check_res:
            check_res.url = img_url
        else:
            new_img = Image(id=img_id, url=img_url, star=-1)
            ss.add(new_img)

    typ = input("what kind of method you want: ")
    if typ == 'daily':
        yande = YandeSpider(need_json=True, add_database_cb=add_empty_item)
    elif typ == 'all':
        tag = input('the tag you want: ')
        yande = YandeAll([tag], add_database_cb=add_empty_item)
    elif typ == 'id':
        yande = YandeId(add_database_cb=add_empty_item)
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
    device_list = call('adb2 devices')
    if DEVICE_ID not in device_list:
        print('no devices found!')
        sys.exit(-1)

    while True:
        cmd = input('please input your command\n>>>').split()
        cmd_func = cmd[0]
        if cmd_func == 'push':
            push(int(cmd[1]))
        elif cmd_func == 'update':
            if cmd[-1] == 'all':
                update(_all=True)
            else:
                update()
        elif cmd_func == 'trans':
            if len(cmd) == 2:
                trans(int(cmd[1]))
                continue
            trans()
        elif cmd_func == 'dl':
            download_yande_imgs()
        elif cmd_func == 'quit':
            break
        else:
            input("test mod")
            test()
