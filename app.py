# -*- coding: UTF-8 -*-
import os

os.chdir(os.path.split(os.path.abspath(__file__))[0])
import click
from yandecli.cli.status import status
from yandecli.cli.plot import plot_group
from yandecli.cli.add import add
from yandecli.cli.pull import pull
from yandecli.cli.push import push
from yandecli.cli.download import download_yande_imgs, clear
from yandecli.cli.update import update

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# TODO hold 那些不在TAGS里的图片
@click.group(context_settings=CONTEXT_SETTINGS)
def main_group():
    pass


if __name__ == '__main__':
    main_group.add_command(push)
    main_group.add_command(pull)
    main_group.add_command(add)
    main_group.add_command(download_yande_imgs)
    main_group.add_command(status)
    main_group.add_command(update)
    main_group.add_command(clear)
    main_group.add_command(plot_group)

    main_group()
