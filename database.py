from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, Date, Boolean, UniqueConstraint, func, Enum
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from settings import TAGTYPE, RATING, PLATFORM

Base = declarative_base()
engine = create_engine('sqlite:///data.db?check_same_thread=False')
Session = sessionmaker(bind=engine)
session = Session()
ss = session
history_session = Session()


class Cache:
    def __init__(self, cls, pk):
        self.pk = pk
        self.cache = None
        self.cls = cls

    def check_exists(self, key):
        if self.cache is None:
            self._fill_cache()

        return self.cache.get(key)

    def get_unique(self, key):
        o = self.check_exists(key)
        if o is None:
            o = self.cls(**{self.pk: key})
            session.add(o)
            self.cache[key] = o
        return o

    def _fill_cache(self):
        print(f'filling cache {self.cls}')
        items = session.query(self.cls).all()
        self.cache = {
            getattr(item, self.pk): item for item in items
        }


class Image(Base):
    __tablename__ = 'image'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    tag_refs = relationship('Tag', secondary='images2tags', backref='images')
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
    UniqueConstraint('game_id', 'tag_name')

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('image.id'))
    tag_name = Column(Integer, ForeignKey('tag.name'))


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


def check_exists(obj, **kwargs):
    # print(kwargs)
    res = ss.query(obj).filter_by(**kwargs).all()
    if len(res) == 0:
        return False
    if len(res) == 1:
        return res[0]
    raise


Tag.cache = Cache(Tag, 'name')
Image.cache = Cache(Image, 'id')
Base.metadata.create_all(engine)
