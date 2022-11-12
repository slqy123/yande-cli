from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, Date, Boolean, UniqueConstraint, func, Enum, \
    and_
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from settings import TAGTYPE, RATING, PLATFORM, DOMAIN
from yandecli.state_info import data

Base = declarative_base()
engine = create_engine('sqlite:///data.db?check_same_thread=False')
Session = sessionmaker(bind=engine)
session = Session()
ss = session
history_session = Session()


class Cache:
    def __init__(self, cls, pk):
        self.pk = pk
        self.cache = {}
        self.cls = cls

    def check_exists(self, key):
        if not self.cache:
            self.fill_cache(key)

        return self.cache.get(key)

    def get_unique(self, key):
        o = self.check_exists(key)
        if o is None:
            o = self.cls(**{self.pk: key})
            # session.add(o)
            self.cache[key] = o
        return o

    def fill_cache(self, key):
        pass


class ImageCache(Cache):
    def __init__(self):
        super(ImageCache, self).__init__(Image, 'id')

    def fill_cache(self, _):
        print(f'filling cache {self.cls}')
        items = img_query(Image).all()
        self.cache = {
            getattr(item, self.pk): item for item in items
        }


class TagCache(Cache):
    def __init__(self):
        super(TagCache, self).__init__(Tag, 'name')

    def fill_cache(self, _):
        print(f'filling cache {self.cls}')
        items = ss.query(Tag).all()
        self.cache = {
            getattr(item, self.pk): item for item in items
        }


class Image(Base):
    __tablename__ = 'image'
    id = Column(Integer, primary_key=True)
    domain = Column(Enum(DOMAIN), default=DOMAIN(data.data.domain), primary_key=True)
    name = Column(Text)
    tag_refs = relationship('Tag', secondary='images2tags', backref='images',
                            primaryjoin='and_(Image.id == Images2Tags.image_id, Image.domain == Images2Tags.domain)', lazy='dynamic')
    star = Column(Integer, default=0)
    count = Column(Integer, default=0)
    file_url = Column(Text, default='')
    history_id = Column(Integer, ForeignKey('history.id'), default=0)
    history = relationship('History', backref='images')
    tags = Column(Text, default='')
    last_update_date = Column(Date)
    author = Column(Text)
    creator_id = Column(Integer)
    status = Column(Integer)
    rating = Column(Enum(RATING))
    held = Column(Boolean, default=False)


class Tag(Base):
    __tablename__ = 'tag'
    name = Column(Text, primary_key=True, nullable=False)
    type = Column(Enum(TAGTYPE))


class Images2Tags(Base):
    __tablename__ = 'images2tags'

    image_id = Column(Integer, ForeignKey('image.id'), primary_key=True)
    domain = Column(Enum(DOMAIN), ForeignKey('image.domain'), primary_key=True)
    tag_name = Column(Integer, ForeignKey('tag.name'), primary_key=True)
    # del_ = Column('del', Boolean, default=False)


class History(Base):
    # 变动history字段后，对应的yandecli.history的init也要相应更改
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    start = Column(Integer)
    end = Column(Integer)
    amount = Column(Integer)
    finish = Column(Boolean, default=False)
    img_star = Column(Integer)
    platform = Column(Enum(PLATFORM))
    domain = Column(Enum(DOMAIN), default=DOMAIN(data.data.domain))


def check_exists(obj, **kwargs):
    # print(kwargs)
    res = ss.query(obj).filter_by(domain=DOMAIN(domain), **kwargs).all()
    if not res:
        return False
    if len(res) == 1:
        return res[0]
    raise


Tag.cache = TagCache()
Image.cache = ImageCache()
Base.metadata.create_all(engine)

domain = data.data.domain


def img_query(*args):
    return ss.query(*args).filter(Image.domain == DOMAIN(domain))


def history_query(*args):
    return ss.query(*args).filter(History.domain == DOMAIN(domain))
