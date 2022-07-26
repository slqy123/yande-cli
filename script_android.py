from subprocess import call
import sys
import os
import datetime

"""
用法：
1、dif 将手机文件与电脑比较，删除电脑上多了的
2、push <order> 将电脑文件传送到手机，默认传入根目录下的（最多），若传入order参数，则将指定的精简后的备份传入
   oder参数可选：
    first 第一个，
    last 最后一个，
    [number] 第number次的结果，
    choose 列出来让我选
3、collect 将手机文件以txt格式保存下来，放在collect目录下
"""

method = sys.argv[1]
dir = sys.argv[2]
root = "sdcard/ADM/.comic"
file_dir = root + f"/{dir}"

if method == 'dif':  
    call(f'adb shell "cd {file_dir} && ls > out.txt && exit"')
    call(f'adb pull {file_dir}/out.txt')
    with open('out.txt') as f:
        content = set(f.read().split('\n'))
        # print(content[0], content[-1] == '')  # out.txt True
    pc_files = os.listdir(dir)
    count = 0
    for pc_file in pc_files:
        if pc_file not in content:
            print(pc_file, 'deleted')
            os.remove(f"{dir}/{pc_file}")
            count += 1
    print(f"Delete {count} pictures in total")


elif method == 'push':  
    if len(sys.argv) > 3:  # 说明传入了第三个参数
        order = sys.argv[3]
        txt_bak_path = f"collect/{dir}"
        bak_txts = os.listdir(txt_bak_path)
        bak_txts.sort(key=lambda x: int(x.split("_")[0]))

        if order == 'first':
            txt = bak_txts[0]
        elif order == 'last':
            txt = bak_txts[-1]
        elif order == 'choose':
            for index, file in enumerate(bak_txts):
                print(f'[{index}]: {file}')
            choice = int(input("Please input your choice: "))
            txt = bak_txts[choice]
        else:
            txt = bak_txts[int(order)-1]
        print(f"choose {txt} to push")

        with open(f"{txt_bak_path}/{txt}") as f:
            file_names = f.read().split('\n')
        call(f'adb shell "mkdir {file_dir}"')
        for file_name in file_names:
            call(f'adb push "{dir}/{file_name}" {root}/{dir}')

    else:
        call(f'adb shell "mkdir {file_dir}"')
        call(f"adb push {dir} {root}")


elif method == 'collect':
    target_path = f'collect/{dir}'
    if not os.path.exists(target_path):
        print(f'path {dir} in collect not exists, create this folder')
        os.mkdir(target_path)
    collects = os.listdir(target_path)
    if collects:
        index = max([int(s.split('_')[0]) for s in collects]) + 1
    else:
        index = 1
    txt_name = f'{index}_{datetime.date.today()}'

    call(f'adb shell "cd {file_dir} && ls > out.txt && exit"')
    call(f'adb pull {file_dir}/out.txt ./collect/{dir}/{txt_name}.txt')
