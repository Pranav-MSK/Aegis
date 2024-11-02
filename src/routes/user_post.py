from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from humanize import naturaltime

from src.models import UserArticle, UserPostComment, UserPostLike

from src.config import app, db

user_post_bp = Blueprint('user_post', __name__)

@app.route('/system/updats', methods=['GET'])
def index():
    posts = UserArticle.query.all()
    return render_template('other/system_updates.html', posts=posts)

# get all the comments
@app.route('/comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    page = request.args.get('page', 1, type=int)
    comments_per_page = 4
    comments = UserPostComment.query.filter_by(post_id=post_id).paginate(page, comments_per_page, error_out=False)
    
    return render_template('comments.html', comments=comments, post_id=post_id)


@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    if content:
        new_post = UserArticle(user_id=current_user.id, content=content)
        db.session.add(new_post)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    existing_like = UserPostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = UserPostLike(post_id=post_id, user_id=current_user.id)
        db.session.add(new_like)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    content = request.form.get('content')
    if content:
        new_comment = UserPostComment(post_id=post_id, user_id=current_user.id, content=content)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('index'))


