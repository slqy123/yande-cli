import click

from yandecli.tools.database import *
from settings import ADB_AVAILABLE
from yandecli.tools.history import YandeHistory


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
