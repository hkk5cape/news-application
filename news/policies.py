from django.db.models import Q
from .models import Article, User


def is_editor(user):
    return user.is_authenticated and (
        user.role == "editor" or user.groups.filter(name="Editor").exists()
    )


def can_edit(user, obj):
    if not user.is_authenticated:
        return False
    if is_editor(user):
        return (
            obj.publisher_id is None
            or obj.publisher.editors.filter(pk=user.pk).exists()
        )
    return (
        user.role == "journalist"
        and obj.author_id == user.pk
        and (
            obj.publisher_id is None
            or obj.publisher.journalists.filter(pk=user.pk).exists()
        )
    )


def can_publish_under(user, publisher):
    if publisher is None:
        return True
    if is_editor(user):
        return publisher.editors.filter(pk=user.pk).exists()
    return publisher.journalists.filter(pk=user.pk).exists()


def subscribed_articles(user):
    if user.role != User.Role.READER:
        return Article.objects.none()
    return (
        Article.objects.filter(approved=True)
        .filter(
            Q(publisher__in=user.subscribed_publishers.all())
            | Q(author__in=user.subscribed_journalists.all())
        )
        .distinct()
    )


def subscribers(author_id, publisher_id):
    query = Q(subscribed_journalists__pk=author_id)
    if publisher_id:
        query |= Q(subscribed_publishers__pk=publisher_id)
    return User.objects.filter(role="reader", is_active=True).filter(query).distinct()
