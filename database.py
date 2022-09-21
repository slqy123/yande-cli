from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, Date, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
# from os import path
# DB_PATH = path.split(__file__)[0] + '/test.db'
Base = declarative_base()
engine = create_engine(f'sqlite:///test.db')
ss = sessionmaker(bind=engine)()


class Image(Base):
    __tablename__ = 'image'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    rtags = relationship('Tag', secondary='images2tags', backref='Images')
    star = Column(Integer, default=0)
    count = Column(Integer, default=0)
    file_url = Column(Text, default='')
    history_id = Column(Integer, ForeignKey('history.id'), default=0)
    history = relationship('History', backref='images')
    tags = Column(Text, default='')
    last_update_date = Column(Date)
    author = Column(Text)
    creator_id = Column(Integer)


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True)


class Images2Tags(Base):
    __tablename__ = 'images2tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey('image.id'))
    tag_id = Column(Integer, ForeignKey('tag.id'))


class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    start = Column(Integer)
    end = Column(Integer)
    amount = Column(Integer)
    finish = Column(Boolean, default=False)
    img_star = Column(Integer)
