import click


@click.group(help='operations about image tags')
def tags():
    pass


@click.command()
@click.argument('tag_name', type=str)
@click.option('-u', '--update', default=True, type=bool,
              help='should images be held or unheld')
def add(tag_name: str, update: bool = True):
    """
    add a tag to default tags
    """
    from yandecli.state_info import data
    from database import ss, img_query, Image, Tag
    status_data = data
    if tag_name in status_data.tags:
        print(f'tag "{tag_name}" is already in default tags')
        return

    status_data.tags.add(tag_name)
    status_data.save()

    if update:
        tag = ss.query(Tag).filter_by(name=tag_name).all()
        if not tag:
            print('No need to update')
            ss.add(Tag(name=tag_name))
            ss.commit()
            return
        tag = tag[0]

        print('updating...')
        for img in img_query(Image).filter(Image.tag_refs.contains(tag)).all():
            img.held = False
        ss.commit()

    print(status_data.tags)


@click.command('rm')
@click.argument('tag_name', type=str)
@click.option('-u', '--update', default=True, type=bool,
              help='should images be held or unheld')
def remove(tag_name: str, update: bool = True):
    """
    remove a tag from default tags
    """
    from yandecli.state_info import data
    from database import ss, img_query, Image, Tag
    status_data = data
    if tag_name not in status_data.tags:
        print(f'tag "{tag_name}" not found!')
        return

    status_data.tags.remove(tag_name)

    if update:
        if not (tag := ss.query(Tag).filter_by(name=tag_name).all()):
            print('No need to update')
            ss.add(Tag(name=tag_name))
            ss.commit()
            return

        tag = tag[0]

        print('updating...')
        for img in img_query(Image).filter(Image.tag_refs.contains(tag)).all():
            img.held = True
        ss.commit()
        status_data.save()
    print(status_data.tags)


@click.command('list')
def list_():
    from yandecli.state_info import data
    print(*data.tags, sep='\n')


tags.add_command(add)
tags.add_command(remove)
tags.add_command(list_)
