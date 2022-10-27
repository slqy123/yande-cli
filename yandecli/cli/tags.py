import click
from yandecli.state_info import Data
from database import *

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
    status_data = Data.get_data()
    if tag_name in status_data.data.tags:
        print(f'tag "{tag_name}" is already in default tags')
        return

    status_data.data.tags.add(tag_name)

    if update:
        tag = check_exists(Tag, name=tag_name)
        if not tag:
            print('No need to update')
            ss.add(Tag(name=tag_name))
            ss.commit()
            return

        print('updating...')
        for img in ss.query(Image).filter(Image.tag_refs.contains(tag)).all():
            img.held = False
        ss.commit()
        status_data.save()



    print(status_data.data.tags)


@click.command('rm')
@click.argument('tag_name', type=str)
@click.option('-u', '--update', default=True, type=bool,
              help='should images be held or unheld')
def remove(tag_name: str, update: bool = True):
    """
    remove a tag from default tags
    """
    status_data = Data.get_data()
    if tag_name not in status_data.data.tags:
        print(f'tag "{tag_name}" not found!')
        return

    status_data.data.tags.remove(tag_name)

    if update:
        tag = check_exists(Tag, name=tag_name)
        if not tag:
            print('No need to update')
            ss.add(Tag(name=tag_name))
            ss.commit()
            return

        print('updating...')
        for img in ss.query(Image).filter(Image.tag_refs.contains(tag)).all():
            img.held = True
        ss.commit()
        status_data.save()
    print(status_data.data.tags)


@click.command('list')
def list_():
    print(*Data.get_data().data.tags, sep='\n')


tags.add_command(add)
tags.add_command(remove)
tags.add_command(list_)
