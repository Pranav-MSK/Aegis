# cython: language_level=3
from datetime import datetime
from flask import render_template, request, redirect, url_for, Blueprint, jsonify
from flask_login import login_required, current_user

from src.config import app
from src.models import UserArticle, UserPostComment, UserPostLike, UserSavedPost, UserPostReport
from src.routes.helper.notification_helper import generate_system_notification


user_post_bp = Blueprint('user_post', __name__)

@app.route('/system/discussion', methods=['GET', 'POST'])
@login_required
def discussion_board():
    if request.method == 'POST':
        content = request.form.get('content')
        form_type = request.form.get('form_type')
        new_post_tags = request.form.getlist('tags')
        new_post_tags = ','.join(list(set(tag.strip() for tag in new_post_tags[0].split(',') if tag.strip())))
 
        if form_type == 'create_post' and content:
            new_post = UserArticle(user_id=current_user.id, content=content, tags=new_post_tags)
            new_post.save()                

            notification_data = {
                "type": "info",
                "icon": "info-circle",
                "title": "New Post",
                "message": f"New post by {current_user.first_name}: {content[:15]}...",
                "is_global": True
            }
            generate_system_notification(notification_data)
            return redirect(url_for('discussion_board'))

        if form_type == 'edit_post':
            post_id = request.form.get('post_id')
            post = UserArticle.query.get(post_id)
            if post and not post.is_deleted:  # Ensure the post exists and is not deleted
                post.content = content
                post.save()
            return redirect(url_for('discussion_board'))

    page = request.args.get('page', 1, type=int)  # Get the current page number
    per_page = 10

    # Get paginated list of undeleted posts
    pagination = UserArticle.query.filter_by(is_deleted=False).order_by(UserArticle.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # Retrieve saved posts for the current user, filtering out deleted ones
    saved_post_ids = [post.post_id for post in UserSavedPost.query.filter_by(user_id=current_user.id).all()]
    # saved_posts = UserArticle.query.filter(UserArticle.id.in_(saved_post_ids), UserArticle.is_deleted == False).all()

    # Use pagination for saved posts
    saved_pagination = UserArticle.query.filter(UserArticle.id.in_(saved_post_ids), UserArticle.is_deleted == False).order_by(UserArticle.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    liked_post_ids = [like.post_id for like in UserPostLike.query.filter_by(user_id=current_user.id).all()]

    latest_posts = UserArticle.query.filter_by(is_deleted=False).order_by(UserArticle.created_at.desc()).limit(5).all()

    deleted_posts = UserArticle.query.filter_by(is_deleted=True).all()

    post_tags = ["#announcement", "#introduction", "#general", "#help", "#feedback", "#suggestion", 
                 "#bug", "#feature", "#question", "#discussion", "#off-topic"]

    user_analytics = {
        "total_posts": UserArticle.query.filter_by(user_id=current_user.id, is_deleted=False).count(),
        "total_likes_received": UserPostLike.query.filter(UserPostLike.post_id.in_([post.id for post in UserArticle.query.filter_by(user_id=current_user.id, is_deleted=False).all()])).count(),
        "total_comments": UserPostComment.query.filter(UserPostComment.post_id.in_([post.id for post in UserArticle.query.filter_by(user_id=current_user.id, is_deleted=False).all()])).count(),
        "posts_liked": UserPostLike.query.filter_by(user_id=current_user.id).count(),
        "posts_saved": UserSavedPost.query.filter_by(user_id=current_user.id).count(),
        "comments_made": UserPostComment.query.filter_by(user_id=current_user.id).count()
    }

    return render_template('other/discussion_board.html', 
                           pagination=pagination, 
                           saved_pagination=saved_pagination, 
                           liked_post_ids=liked_post_ids,
                           latest_posts=latest_posts,
                            deleted_posts=deleted_posts,
                            post_tags=post_tags,
                            user_analytics=user_analytics)

# get all the comments
@app.route('/comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    page = request.args.get('page', 1, type=int)
    comments_per_page = 4
    comments = UserPostComment.query.filter_by(post_id=post_id).paginate(page, comments_per_page, error_out=False)
    
    return render_template('comments.html', comments=comments, post_id=post_id)


@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    existing_like = UserPostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing_like:
        existing_like.delete()
    else:
        new_like = UserPostLike(post_id=post_id, user_id=current_user.id)
        new_like.save()

        #post owner id
        post_owner_id = UserArticle.query.get(post_id).user_id
        notification_data = {
            "type": "info",
            "icon": "info-circle",
            "title": "Post Like",
            "message": f"Your post was liked by {current_user.first_name}",
            "is_global": False,
            "user_id": post_owner_id
        }
        generate_system_notification(notification_data, user_id=post_owner_id)
    
    return redirect(url_for('discussion_board'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    content = request.form.get('content')
    if content:
        new_comment = UserPostComment(post_id=post_id, user_id=current_user.id, content=content)
        new_comment.save()

        #post owner id
        post_owner_id = UserArticle.query.get(post_id).user_id
        notification_data = {
            "type": "info",
            "icon": "info-circle",
            "title": "Post Comment",
            "message": f"Your post was commented by {current_user.first_name}",
            "is_global": False,
            "user_id": post_owner_id
        }
        generate_system_notification(notification_data, user_id=post_owner_id)
    return redirect(url_for('discussion_board'))


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = UserArticle.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        return redirect(url_for('discussion_board'))  # Prevent editing other users' posts
    
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

        notification_data = {
            "type": "info",
            "icon": "info-circle",
            "title": "Post Deleted",
            "message": f"You have deleted your post {post.content[:15]}...",
            "is_global": False,
        }
        generate_system_notification(notification_data)

        post.is_deleted = True
        post.save()


    return redirect(url_for('discussion_board'))

@app.route('/save_post/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    existing_save = UserSavedPost.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if not existing_save:
        new_save = UserSavedPost(post_id=post_id, user_id=current_user.id)
        new_save.save()
    return redirect(url_for('discussion_board'))

@app.route('/unsave_post/<int:post_id>', methods=['POST'])
@login_required
def unsave_post(post_id):
    existing_save = UserSavedPost.query.filter_by(post_id=post_id).first()
    if existing_save:
        existing_save.delete()
    return redirect(url_for('discussion_board'))


# restore_post
@app.route('/restore_post/<int:post_id>', methods=['POST'])
@login_required
def restore_post(post_id):
    post = UserArticle.query.get_or_404(post_id)
    if post.user_id == current_user.id:
        post.is_deleted = False
        post.save()
    return redirect(url_for('discussion_board'))

# delete_post_permanently
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
            comment.updated_at = datetime.utcnow()  # Update the timestamp
            comment.save()
    return redirect(url_for('discussion_board'))


@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = UserPostComment.query.get_or_404(comment_id)
    if comment.user_id == current_user.id:
        comment.delete()
    return redirect(url_for('discussion_board'))

