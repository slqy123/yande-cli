from exts import db

class Image(db.Model):
    query: db.Query
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    tags = db.relationship('Tag', secondary='images2tags', backref='Images')
    star = db.Column(db.Integer, default=0)
    count = db.Column(db.Integer, default=0)
    url = db.Column(db.Text, default='')
    history_id = db.Column(db.Integer, db.ForeignKey('history.id'), default=0)
    history = db.relationship('History', backref='images')

class Tag(db.Model):
    query: db.Query

    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, unique=True)


class Images2Tags(db.Model):
    __tablename__ = 'images2tags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))


class History(db.Model):
    query: db.Query
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date)
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    finish = db.Column(db.Boolean, default=False)
