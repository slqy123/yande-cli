import os
import re
from yandeTime import YandeSpider
import sys
import shutil


class DealImg:
    def __init__(self):
        self.path = r'F:\movies\song for yg\_all'

    def clear_2(self):
        imgs = os.listdir(self.path)
        for img in imgs:
            res = re.sub(r'_[2-9](\.[a-z]+)$', r'\1', img)
            if res != img:
                if res in imgs:
                    p = os.path.join(self.path, img)
                    os.remove(p)
                    print(f"{img} has been removed")


class Classify:
    def __init__(self, dr=r'F:\movies\song for yg\_all'):
        self.dr = dr
        self.fs = os.listdir(dr)
        self.fids = [int(f.split()[1]) for f in self.fs]

    def create_and_move(self):
        for fid, f in zip(self.fids, self.fs):
            name = str(fid // 25000 + 1)
            if not os.path.exists(name):
                print("create folder" + name)
                os.makedirs(name)

            shutil.move(self.dr + '/' + f, name + '/' + f)
            print(f"successfully move {fid} to {name}")


method = sys.argv[1]

if method == 'clear':
    deal = DealImg()
    deal.clear_2()
elif method == 'refresh':
    yande = YandeSpider(
        tags=['bondage', 'loli', 'pee', 'vibrator',
              'anal', 'dildo', 'anal_beads', 'masturbation'
              ])
    yande.run()
elif method == 'classify':
    cl = Classify()
    cl.create_and_move()
