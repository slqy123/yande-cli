from random import randrange

import click




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
@click.option('-rt', '--rating', type=str, default='sqe',
              help='the rating of the image can be s: safe, q: questionable, e: explicit')
def push(amount: int, times: int, tag: str, random: bool,
         star: int = None, platform: str = 'MOBILE', rating: str = 'sqe') -> None:
    from database import Image, img_query, func, ss
    from settings import PLATFORM, STATUS, RATING
    from yandecli.tools.file_io import get_device_by_platform
    from yandecli.tools.history import YandeHistory
    from yandecli.state_info import IMG_PATH_EXISTS, ADB_AVAILABLE


    assert IMG_PATH_EXISTS
    if platform == PLATFORM.MOBILE.value:
        assert ADB_AVAILABLE

    DEVICE = get_device_by_platform(PLATFORM(platform))

    def _push():
        min_count = star if star is not None else img_query(func.min(Image.count)).filter(
            Image.star == Image.count, Image.history.has(finish=True)).first()[0]
        print(f"min count = {min_count}")
        tmp_query = img_query(Image).filter(Image.star == Image.count,
                                            Image.status == STATUS.EXISTS,
                                            Image.count == min_count,
                                            Image.history.has(finish=True),
                                            Image.tags.contains(tag),  # 如果不传入tag，默认是空字符，此时等于没过滤
                                            Image.rating.in_([RATING(r) for r in rating]),
                                            Image.held == False
                                            ).order_by(Image.id)
        if random:
            pages = (tmp_query.count() // amount) + 1
            rand_page = randrange(0, pages)
            imgs = tmp_query.slice(rand_page * amount, (rand_page + 1) * amount).all()
            print(f'start from page {rand_page + 1}/{pages}')
        else:
            imgs = tmp_query.limit(amount).all()

        yande_history = YandeHistory.create_new(imgs, PLATFORM(platform))

        print(f"{len(imgs)} images in total from {yande_history.start} to {yande_history.end}")

        device = DEVICE(yande_history.get_folder_name())
        from tqdm import trange
        with trange(yande_history.amount) as t:
            for i in t:
                img = imgs[i]
                # TODO 要不要加相关标签
                # tags = ' '.join([t.name for t in img.tag_refs if t.type not in (TAGTYPE.GENERAL, TAGTYPE.CHARACTER)])
                # ext = img.name.rsplit('.', 1)[1]
                # new_name = f'{img.id} {tags}.{ext}'
                # new_name = new_name.translate(str.maketrans(r'/\:*?"<>|', "_________"))
                t.set_description(f"id={img.id}")
                size = device.push(img.name, f" [{i + 1}].".join(img.name.rsplit('.', 1)))
                t.set_postfix(size=f"{round(size, 2)}MB")
                img.history = yande_history.history
        print('push complete')
        ss.commit()

    for _ in range(times):
        _push()
