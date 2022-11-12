from random import sample

import click


# TODO update 功能拆分

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

        tag: update by the given tag, make sure to add --tag option or set default tags if you use this mode

        time: update all images of default tags from last update time to now,
        if the option --tag is 'all', all images no matter what tags will be updated

        type: update the type of tags, use -t to give the type, it should be an integer, you can see the relation
        in settings.py
    """

    from database import img_query, Image, func
    from settings import STATUS
    from yandecli.tools.yande_requests import YandeId, YandeAll, YandeDaily, TagTypeSpider
    from yandecli.state_info import IMG_PATH_EXISTS, data

    assert IMG_PATH_EXISTS

    has_img = bool(img_query(Image).filter(Image.status == STATUS.EXISTS).count())
    if (not has_img) and mode not in ('tag', 'type'):
        print('first use this command, please use the tag mod')
        return
    exists_img_query = img_query(Image).filter(Image.status == STATUS.EXISTS, Image.held == False)
    last_date = exists_img_query.order_by(Image.last_update_date.asc()).first().last_update_date if has_img else None
    print(f'last update date: {last_date}')
    tmp_query = exists_img_query.filter(Image.last_update_date == last_date)

    if mode == 'id':
        if amount < 1:
            print("please input amount > 0")
            return

        ids = [img.id for img in tmp_query.limit(amount)]
        yande = YandeId(ids=ids)
        yande.run()
    elif mode == 'tag':
        status_data = data

        def get_rand_tag() -> str:
            if not has_img:
                print('since this is your first update, please give a tag name')
                return ''

            print(last_date)
            rand_img = tmp_query.filter(Image.tags != None).order_by(func.random()).first()
            YandeId([rand_img.id]).run()
            if not rand_img:
                print('no proper tag found!')
                rand_img = img_query(Image).filter(Image.tags != None).order_by(func.random()).first()
            tags = rand_img.tags.split(' ')
            print(tags, rand_img.id)
            rand_tag = sample(list(set(tags) & status_data.tags), 1)[0]
            print(f'choose img id={rand_img.id}, tag={rand_tag}')
            return rand_tag

        tag: str = tag or get_rand_tag()
        if tag not in status_data.tags:
            if tag != '':
                print('this tag is not in the default tags, please add it to default before update.')
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
