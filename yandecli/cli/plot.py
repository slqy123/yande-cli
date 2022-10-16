from utils import LazyImport
plt = LazyImport('plotext')
import click
from database import *
from settings import STATUS
import os
# import plotext as plt
w, h = os.get_terminal_size()


@click.command()
def star():
    infos = ss.query(Image.star, func.count(Image.star)).filter(Image.status == STATUS.EXISTS).group_by(Image.star).all()
    dislike = ss.query(func.count('*')).filter(Image.status == STATUS.DELETED).all()[0][0]
    labels = ('dislike', 'unread', *(i[0] for i in infos if i[0] > 0))
    data = [dislike, *(i[1] for i in infos)]
    plt.simple_bar(labels, data, width=w//1.618)
    plt.show()
