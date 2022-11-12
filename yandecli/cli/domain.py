from settings import DOMAIN
from yandecli.state_info import data
import click

_NAMES = [i.name for i in DOMAIN]


@click.group(help="switch/list domains")
def domain():
    pass


@click.command('list', help='list all domains possible, can manually added in settings.py')
def list_():
    click.echo(*_NAMES)


@click.command(help="use a domain, show domain names by list command")
@click.argument('name', type=click.Choice(_NAMES, case_sensitive=False))
def use(name: str):
    """
    switch domain     name is not case-sensitive
    """
    domain2use: DOMAIN = getattr(DOMAIN, name)
    data.data.domain = domain2use.value
    data.save()


domain.add_command(list_)
domain.add_command(use)
