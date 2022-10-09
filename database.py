from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, Date, Boolean, UniqueConstraint, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# from os import path
# DB_PATH = path.split(__file__)[0] + '/test.db'

Base = declarative_base()
engine = create_engine(f'sqlite:///data.db')
Session = sessionmaker(bind=engine)
session = Session()
ss = session
history_session = Session()

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


class Tag(Base):
    __tablename__ = 'tag'
    name = Column(Text, primary_key=True, nullable=False)

    @classmethod
    def get_unique(cls, name):
        # get the session cache, creating it if necessary
        cache = session._unique_cache = getattr(session, '_unique_cache', {})
        # create a key for memorizing
        key = (cls, name)
        # check the cache first
        o = cache.get(key)
        if o is None:
            # check the database if it's not in the cache
            o = session.query(cls).filter_by(name=name).first()
            if o is None:
                # create a new one if it's not in the database
                o = cls(name=name)
                session.add(o)
            # update the cache
            cache[key] = o
        return o


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


Base.metadata.create_all(engine)
