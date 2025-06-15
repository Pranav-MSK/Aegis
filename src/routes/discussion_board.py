# cython: language_level=3
from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import login_required, current_user

from src.config.app_config import app
from src.services.decorators.access_decorators import systemguard_enterprise

from src.services.discussion_service import DiscussionService
from src.services.discussion_service import NotificationService

discussion_board_bp = Blueprint('user_post', __name__)
discussion_service = DiscussionService()
notification_service = NotificationService()

@app.route('/system/discussion', methods=['GET', 'POST'])
@systemguard_enterprise()
@login_required
def discussion_board():
    if request.method == 'POST':
        form_data = request.form.to_dict(flat=True) # type: ignore
        form_data['tags'] = request.form.getlist('tags')
        discussion_service.process_post_submission(form_data, current_user)
        return redirect(url_for('discussion_board'))

    context = discussion_service.get_discussion_context(current_user, request.args.get('page', 1, type=int))
    return render_template('system/discussion_board.html', **context)

@app.route('/comments/<int:post_id>', methods=['GET'])
@login_required
def get_comments(post_id):
    page = request.args.get('page', 1, type=int)
    comments = discussion_service.get_comments(post_id, page)
    return render_template('comments.html', comments=comments, post_id=post_id)

@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    discussion_service.toggle_like(post_id, current_user)
    return redirect(url_for('discussion_board'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    content = request.form.get('content')
    discussion_service.add_comment(post_id, current_user, content)
    return redirect(url_for('discussion_board'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    if request.method == 'POST':
        content = request.form.get('content')
        discussion_service.edit_post(post_id, current_user, content)
        return redirect(url_for('discussion_board'))
    post = discussion_service.get_user_post(post_id, current_user)
    return render_template('other/edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    discussion_service.soft_delete_post(post_id, current_user)
    return redirect(url_for('discussion_board'))

@app.route('/save_post/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    discussion_service.save_post(post_id, current_user)
    return redirect(url_for('discussion_board'))

@app.route('/unsave_post/<int:post_id>', methods=['POST'])
@login_required
def unsave_post(post_id):
    discussion_service.unsave_post(post_id, current_user)
    return redirect(url_for('discussion_board'))

@app.route('/restore_post/<int:post_id>', methods=['POST'])
@login_required
def restore_post(post_id):
    discussion_service.restore_post(post_id, current_user)
    return redirect(url_for('discussion_board'))

@app.route('/delete_post_permanently/<int:post_id>', methods=['POST'])
@login_required
def delete_post_permanently(post_id):
    discussion_service.delete_post_permanently(post_id, current_user)
    return redirect(url_for('discussion_board'))

@app.route('/edit_comment/<int:comment_id>', methods=['POST'])
@login_required
def edit_comment(comment_id):
    content = request.form.get('content')
    discussion_service.edit_comment(comment_id, current_user, content)
    return redirect(url_for('discussion_board'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    discussion_service.delete_comment(comment_id, current_user)
    return redirect(url_for('discussion_board'))
