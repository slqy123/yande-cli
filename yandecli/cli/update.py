from random import sample

import click
from yandecli.tools.database import *
from settings import IMG_PATH_EXISTS, STATUS, TAGS
from yandecli.tools.yande_requests import YandeId, YandeAll, YandeDaily, TagTypeSpider


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
        print(f'last update date: {last_date}')
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
            print(last_date)
            rand_img = img_query.filter(Image.tags != None).order_by(func.random()).first()
            YandeId([rand_img.id]).run()
            if not rand_img:
                print('no proper tag found!')
                rand_img = ss.query(Image).filter(Image.tags != None).order_by(func.random()).first()
            tags = rand_img.tags.split(' ')
            print(tags, rand_img.id)
            rand_tag = sample(list(set(tags) & set(TAGS)), 1)[0]
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
