import click

@click.command(help='Show the current information of your images')
def status():
    from database import img_query, DOMAIN, Image, func
    from yandecli.state_info import ADB_AVAILABLE
    from yandecli.tools.history import YandeHistory
    from yandecli.state_info import IMG_PATH_EXISTS, data

    assert IMG_PATH_EXISTS

    print(f'Current domain is {DOMAIN(data.data.domain).name}')

    # TODO 显示当前连接情况settings里的
    total_num = img_query(Image).count()
    status_count = img_query(Image.status, func.count(1)).group_by(Image.status).all()
    count_list = [0, 0, 0, 0]
    for index, count in status_count:
        count_list[index] = count
    exist_num, deleted_num, queuing_num, downloading_num = count_list
    histories = YandeHistory.get_all_unfinished_histories()
    print(f"{total_num} images in total, {exist_num} exists, {deleted_num} deleted, "
          f"{queuing_num} waiting for download, {downloading_num} in download queue")

    if not ADB_AVAILABLE:
        print('ADB is not available, can\'t get detailed history information from your mobile device')
    choices = [f'[{i}]:{YandeHistory.get_description_from_history(history)}' for i, history in enumerate(histories)]

    print(f"{len(histories)} push histories are not updated, they are:")
    print(*choices, sep='\n')

    from datetime import date
    d = data
    last_download_date = d.last_update_date
    day_pass = date.today() - last_download_date
    print(f'Last download date is {last_download_date} which is {day_pass.days} days ago')
