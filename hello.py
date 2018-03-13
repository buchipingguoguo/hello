__author__ = 'my'

import os
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, request, current_app
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_script import Manager
from markdown import markdown
import bleach
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Required
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_pagedown import PageDown
from flask_pagedown.fields import PageDownField

# from sqlalchemy import


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWM'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'mingming'
app.config['FLASKY_POSTS_PER_PAGE'] = 20
db = SQLAlchemy(app)
# db = sqlalchemy(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
manager = Manager(app)
pagedown = PageDown(app)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    # title = db.Column(db.String(64), unique=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categorys.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'br', 'img']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags,  attributes=['src'], strip=True))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        for i in range(count):
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)))
            db.session.add(p)
            db.session.commit()


db.event.listen(Post.body, 'set', Post.on_changed_body)


class Category(db.Model):
    __tablename__ = 'categorys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    posts = db.relationship('Post', backref='category')
    # articles = db.relationship('Post', backref='category')



class PostForm(FlaskForm):
    body = TextAreaField('write yourself')
    category_id = QuerySelectField('category', query_factory=lambda: Category.query.all(
    ), get_pk=lambda a: str(a.id), get_label=lambda a: a.name)
    submit = SubmitField('submit')


class CateforyForm(FlaskForm):
    name = TextAreaField('writecategory', validators=[Required()])
    submit = SubmitField('submit')



@app.route('/', methods=['GET', 'POST'])
def index():
    # posts = Post.query.order_by(Post.id).all()
    names = Category.query.order_by(Category.id).all()
    # print names
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.id).paginate(page,
        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    # form = PostForm()
    # if form.validate_on_submit():
    #     post = Post(body=form.body.data)
    #     db.session.add(post)
    #     db.session.commit()
    #     return redirect(url_for('index'))

    return render_template('index.html', current_time=datetime.utcnow(), posts=posts, names=names, pagination=pagination)

@app.route('/post', methods=['GET', 'POST'])
def post():
    form = PostForm()
    forma = CateforyForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, category_id=str(form.category_id.data.id))
        # category_id = Post(category_id=str(form.category_id.data.id))
        db.session.add(post)
        # db.session.commit()
        # category = Category(name=forma.name.data)
        # db.session.add(category_id)
        # db.session.add(category)
        db.session.commit()
        return redirect(url_for('post'))
    if forma.validate_on_submit():
        category = Category(name=forma.name.data)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('post'))
    return render_template('admin.html', form=form, forma=forma)


@app.route('/category/<string:name>', methods=['GET', 'POST'])
def category(name):
    # print Category.quer7y.get(name).id
    print name
    posts = Post.query.filter_by(category_id=Category.query.filter_by(name=name).first().id).all()
    return render_template('category.html', posts=posts)

if __name__ == '__main__':
    manager.run()