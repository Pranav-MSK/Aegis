from datetime import datetime
from flask import request
from sqlalchemy import desc

from src.models import UserArticle, UserPostComment, UserPostLike, UserSavedPost
from src.schemas import UserNotification   
from src.services.notification.manager import generate_system_notification

class NotificationService:
    def notify_post_action(self, title, message, type="info", icon="info-circle", is_global=False, user_id=None):
        notification_data = UserNotification(
            type=type,
            icon=icon,
            title=title,
            message=message,
            is_global=is_global,
            user_id=user_id
        )
        generate_system_notification(notification_data, user_id=user_id)


class DiscussionService:
    def __init__(self):
        self.notification_service = NotificationService()

    def process_post_submission(self, form_data, current_user):
        content = form_data.get('content')
        form_type = form_data.get('form_type')
        tags = ','.join(list(set(tag.strip() for tag in form_data.get('tags', [''])[0].split(',') if tag.strip())))

        if form_type == 'create_post' and content:
            new_post = UserArticle(user_id=current_user.id, content=content, tags=tags) # type: ignore
            new_post.save()
            self.notification_service.notify_post_action(
                title="New Post",
                message=f"New post by {current_user.first_name}: {content[:15]}...",
                is_global=True
            )

        elif form_type == 'edit_post':
            post_id = form_data.get('post_id')
            post = UserArticle.query.get(post_id)
            if post and not post.is_deleted:
                post.content = content
                post.save()

    @staticmethod
    def get_discussion_context(current_user, page):
        per_page = 10
        pagination = UserArticle.query.filter_by(is_deleted=False).order_by(desc(UserArticle.created_at)).paginate(page=page, per_page=per_page, error_out=False)
        saved_post_ids = [p.post_id for p in UserSavedPost.query.filter_by(user_id=current_user.id).all()]
        saved_pagination = UserArticle.query.filter(UserArticle.id.in_(saved_post_ids), UserArticle.is_deleted == False).order_by(desc(UserArticle.created_at)).paginate(page=page, per_page=per_page, error_out=False)
        liked_post_ids = [like.post_id for like in UserPostLike.query.filter_by(user_id=current_user.id).all()]
        latest_posts = UserArticle.query.filter_by(is_deleted=False).order_by(desc(UserArticle.created_at)).limit(5).all()
        deleted_posts = UserArticle.query.filter_by(is_deleted=True).all()

        user_posts = UserArticle.query.filter_by(user_id=current_user.id, is_deleted=False).all()
        user_post_ids = [p.id for p in user_posts]

        user_analytics = {
            "total_posts": len(user_posts),
            "total_likes_received": UserPostLike.query.filter(UserPostLike.post_id.in_(user_post_ids)).count(),
            "total_comments": UserPostComment.query.filter(UserPostComment.post_id.in_(user_post_ids)).count(),
            "posts_liked": UserPostLike.query.filter_by(user_id=current_user.id).count(),
            "posts_saved": len(saved_post_ids),
            "comments_made": UserPostComment.query.filter_by(user_id=current_user.id).count()
        }

        return {
            "pagination": pagination,
            "saved_pagination": saved_pagination,
            "liked_post_ids": liked_post_ids,
            "latest_posts": latest_posts,
            "deleted_posts": deleted_posts,
            "post_tags": ["#announcement", "#introduction", "#general", "#help", "#feedback", "#suggestion", "#bug", "#feature", "#question", "#discussion", "#off-topic"],
            "user_analytics": user_analytics
        }

    def get_comments(post_id, page, per_page=4):
        return UserPostComment.query.filter_by(post_id=post_id).paginate(page, per_page, error_out=False) # type: ignore

    def toggle_like(self, post_id, current_user):
        like = UserPostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
        post_owner_id = UserArticle.query.get(post_id).user_id # type: ignore

        if like:
            like.delete()
        else:
            UserPostLike(post_id=post_id, user_id=current_user.id).save() # type: ignore
            self.notification_service.notify_post_action(
                title="Post Like",
                message=f"Your post was liked by {current_user.first_name}",
                user_id=post_owner_id
            )

    def add_comment(self, post_id, current_user, content):
        if content:
            UserPostComment(post_id=post_id, user_id=current_user.id, content=content).save() # type: ignore
            post_owner_id = UserArticle.query.get(post_id).user_id # type: ignore
            self.notification_service.notify_post_action(
                title="Post Comment",
                message=f"Your post was commented by {current_user.first_name}",
                user_id=post_owner_id
                )
    
    @staticmethod
    def edit_post(post_id, current_user, content):
        post = UserArticle.query.get_or_404(post_id)
        if post.user_id == current_user.id and content:
            post.content = content
            post.save()

    @staticmethod
    def get_user_post(post_id, current_user):
        post = UserArticle.query.get_or_404(post_id)
        return post if post.user_id == current_user.id else None

    def soft_delete_post(self, post_id, current_user):
        post = UserArticle.query.get_or_404(post_id)
        if post.user_id == current_user.id:
            post.is_deleted = True
            post.save()
            self.notification_service.notify_post_action(
                title="Post Deleted",
                message=f"You have deleted your post {post.content[:15]}..."
            )

    @staticmethod
    def save_post(post_id, current_user):
        if not UserSavedPost.query.filter_by(post_id=post_id, user_id=current_user.id).first():
            UserSavedPost(post_id=post_id, user_id=current_user.id).save() # type: ignore

    @staticmethod
    def unsave_post(post_id, current_user):
        save = UserSavedPost.query.filter_by(post_id=post_id, user_id=current_user.id).first()
        if save:
            save.delete()

    @staticmethod
    def restore_post(post_id, current_user):
        post = UserArticle.query.get_or_404(post_id)
        if post.user_id == current_user.id:
            post.is_deleted = False
            post.save()

    @staticmethod
    def delete_post_permanently(post_id, current_user):
        post = UserArticle.query.get_or_404(post_id)
        if post.user_id == current_user.id:
            post.delete()

    @staticmethod
    def edit_comment(comment_id, current_user, content):
        comment = UserPostComment.query.get_or_404(comment_id)
        if comment.user_id == current_user.id and content:
            comment.content = content
            comment.updated_at = datetime.utcnow()
            comment.save()

    @staticmethod
    def delete_comment(comment_id, current_user):
        comment = UserPostComment.query.get_or_404(comment_id)
        if comment.user_id == current_user.id:
            comment.delete()

