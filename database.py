from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, Date, Boolean, UniqueConstraint, func, Enum
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from settings import TAGTYPE, RATING

# from os import path
# DB_PATH = path.split(__file__)[0] + '/test.db'

Base = declarative_base()
engine = create_engine(f'sqlite:///data.db')
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

        o = self.cache.get(key)
        return o

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
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    start = Column(Integer)
    end = Column(Integer)
    amount = Column(Integer)
    finish = Column(Boolean, default=False)
    img_star = Column(Integer)


Tag.cache = Cache(Tag, 'name')
Image.cache = Cache(Image, 'id')
Base.metadata.create_all(engine)
