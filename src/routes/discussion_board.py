# cython: language_level=3
from datetime import datetime
from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import login_required, current_user

from src.config import app
from src.models import UserArticle, UserPostComment, UserPostLike, UserSavedPost
from src.routes.helper.notification.manager import generate_system_notification
from src.schemas.discussion_board import UserNotification
from src.routes.helper.access_decorators import systemguard_enterprise

discussion_board_bp = Blueprint('user_post', __name__)

# Utility Functions
def create_post(content, tags):
    post = UserArticle(user_id=current_user.id, content=content, tags=tags)
    post.save()
    notify_user("New Post", f"New post by {current_user.first_name}: {content[:15]}...", True)

def edit_existing_post(post_id, content):
    post = UserArticle.query.get(post_id)
    if post and not post.is_deleted:
        post.content = content
        post.save()

def notify_user(title, message, is_global, user_id=None):
    notification = UserNotification(
        type="info",
        icon="info-circle",
        title=title,
        message=message,
        is_global=is_global,
        user_id=user_id
    )
    generate_system_notification(notification, user_id=user_id)

# Routes
@app.route('/system/discussion', methods=['GET', 'POST'])
@systemguard_enterprise()
@login_required
def discussion_board():
    if request.method == 'POST':
        content = request.form.get('content')
        form_type = request.form.get('form_type')
        tags = ','.join(list(set(tag.strip() for tag in request.form.getlist('tags')[0].split(',') if tag.strip())))

        if form_type == 'create_post' and content:
            create_post(content, tags)
        elif form_type == 'edit_post':
            edit_existing_post(request.form.get('post_id'), content)
        return redirect(url_for('discussion_board'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    all_posts = UserArticle.query.filter_by(is_deleted=False).order_by(UserArticle.created_at.desc())
    pagination = all_posts.paginate(page=page, per_page=per_page, error_out=False)

    saved_post_ids = [post.post_id for post in UserSavedPost.query.filter_by(user_id=current_user.id).all()]
    saved_pagination = UserArticle.query.filter(UserArticle.id.in_(saved_post_ids), UserArticle.is_deleted == False).order_by(UserArticle.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    liked_post_ids = [like.post_id for like in UserPostLike.query.filter_by(user_id=current_user.id).all()]
    latest_posts = all_posts.limit(5).all()
    deleted_posts = UserArticle.query.filter_by(is_deleted=True).all()

    post_tags = ["#announcement", "#introduction", "#general", "#help", "#feedback", "#suggestion", "#bug", "#feature", "#question", "#discussion", "#off-topic"]

    user_posts = UserArticle.query.filter_by(user_id=current_user.id, is_deleted=False)
    user_post_ids = [post.id for post in user_posts]

    user_analytics = {
        "total_posts": user_posts.count(),
        "total_likes_received": UserPostLike.query.filter(UserPostLike.post_id.in_(user_post_ids)).count(),
        "total_comments": UserPostComment.query.filter(UserPostComment.post_id.in_(user_post_ids)).count(),
        "posts_liked": UserPostLike.query.filter_by(user_id=current_user.id).count(),
        "posts_saved": UserSavedPost.query.filter_by(user_id=current_user.id).count(),
        "comments_made": UserPostComment.query.filter_by(user_id=current_user.id).count()
    }

    return render_template('system/discussion_board.html', pagination=pagination, saved_pagination=saved_pagination,
                           liked_post_ids=liked_post_ids, latest_posts=latest_posts, deleted_posts=deleted_posts,
                           post_tags=post_tags, user_analytics=user_analytics)

@app.route('/comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    page = request.args.get('page', 1, type=int)
    comments = UserPostComment.query.filter_by(post_id=post_id).paginate(page, 4, error_out=False)
    return render_template('comments.html', comments=comments, post_id=post_id)

@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    existing_like = UserPostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing_like:
        existing_like.delete()
    else:
        UserPostLike(post_id=post_id, user_id=current_user.id).save()
        notify_user("Post Like", f"Your post was liked by {current_user.first_name}", False, UserArticle.query.get(post_id).user_id)
    return redirect(url_for('discussion_board'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    content = request.form.get('content')
    if content:
        UserPostComment(post_id=post_id, user_id=current_user.id, content=content).save()
        notify_user("Post Comment", f"Your post was commented by {current_user.first_name}", False, UserArticle.query.get(post_id).user_id)
    return redirect(url_for('discussion_board'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = UserArticle.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        return redirect(url_for('discussion_board'))
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            post.content = content
            post.save()
            return redirect(url_for('discussion_board'))
    return render_template('other/edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = UserArticle.query.get_or_404(post_id)
    if post.user_id == current_user.id:
        post.is_deleted = True
        post.save()
        notify_user("Post Deleted", f"You have deleted your post {post.content[:15]}...", False)
    return redirect(url_for('discussion_board'))

@app.route('/save_post/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    if not UserSavedPost.query.filter_by(post_id=post_id, user_id=current_user.id).first():
        UserSavedPost(post_id=post_id, user_id=current_user.id).save()
    return redirect(url_for('discussion_board'))

@app.route('/unsave_post/<int:post_id>', methods=['POST'])
@login_required
def unsave_post(post_id):
    existing_save = UserSavedPost.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing_save:
        existing_save.delete()
    return redirect(url_for('discussion_board'))

@app.route('/restore_post/<int:post_id>', methods=['POST'])
@login_required
def restore_post(post_id):
    post = UserArticle.query.get_or_404(post_id)
    if post.user_id == current_user.id:
        post.is_deleted = False
        post.save()
    return redirect(url_for('discussion_board'))

@app.route('/delete_post_permanently/<int:post_id>', methods=['POST'])
@login_required
def delete_post_permanently(post_id):
    post = UserArticle.query.get_or_404(post_id)
    if post.user_id == current_user.id:
        post.delete()
    return redirect(url_for('discussion_board'))

@app.route('/edit_comment/<int:comment_id>', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = UserPostComment.query.get_or_404(comment_id)
    if comment.user_id == current_user.id:
        content = request.form.get('content')
        if content:
            comment.content = content
            comment.updated_at = datetime.utcnow()
            comment.save()
    return redirect(url_for('discussion_board'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = UserPostComment.query.get_or_404(comment_id)
    if comment.user_id == current_user.id:
        comment.delete()
    return redirect(url_for('discussion_board'))
