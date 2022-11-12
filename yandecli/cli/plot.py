# from utils import LazyImport
# plt = LazyImport('plotext')
import click
import os

# import plotext as plt
try:
    w, h = os.get_terminal_size()
except OSError:
    w, h = 0, 0
bar_width = w // 1.618


@click.group('plot', help='show graphs about image infos')
def plot_group():
    pass


@click.command()
def star():
    from database import img_query, Image, func
    from settings import STATUS

    import plotext as plt
    infos = img_query(Image.star, func.count(Image.star)) \
        .filter(Image.status == STATUS.EXISTS).group_by(Image.star).all()
    dislike = img_query(func.count('*')).filter(Image.status == STATUS.DELETED).all()[0][0]
    labels = ('dislike', 'unread', *(i[0] for i in infos if i[0] > 0))
    data = [dislike, *(i[1] for i in infos)]
    plt.simple_bar(labels, data, width=bar_width)
    plt.show()


@click.command()
def date():
    from database import img_query, Image, func
    from settings import STATUS
    import plotext as plt

    infos = img_query(Image.last_update_date, func.count(Image.last_update_date)) \
        .filter(Image.status == STATUS.EXISTS, Image.held == False).group_by(Image.last_update_date).all()
    plt.simple_bar([i[0] for i in infos], [i[1] for i in infos], width=bar_width)
    plt.show()


plot_group.add_command(star)
plot_group.add_command(date)
