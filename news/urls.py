from django.urls import path
from . import views

urlpatterns = [
    path("publishers/", views.publishers, name="publishers"),
    path("publishers/new/", views.publisher_edit, name="publisher_create"),
    path("publishers/<int:pk>/", views.publisher_detail, name="publisher"),
    path("publishers/<int:pk>/edit/", views.publisher_edit, name="publisher_edit"),
    path(
        "publishers/<int:pk>/employees/<int:user_pk>/remove/",
        views.employee_remove,
        name="employee_remove",
    ),
    path("", views.home, name="home"),
    path("workspace/", views.workspace, name="workspace"),
    path("articles/new/", views.article_edit, name="article_create"),
    path("articles/<int:pk>/", views.article_detail, name="article"),
    path("articles/<int:pk>/edit/", views.article_edit, name="article_edit"),
    path("articles/<int:pk>/delete/", views.article_delete, name="article_delete"),
    path("articles/<int:pk>/approve/", views.article_approve, name="article_approve"),
    path("subscriptions/", views.subscriptions, name="subscriptions"),
    path("newsletters/", views.newsletters, name="newsletters"),
    path("newsletters/new/", views.newsletter_edit, name="newsletter_create"),
    path("newsletters/<int:pk>/", views.newsletter_detail, name="newsletter"),
    path("newsletters/<int:pk>/edit/", views.newsletter_edit, name="newsletter_edit"),
    path(
        "newsletters/<int:pk>/delete/",
        views.newsletter_delete,
        name="newsletter_delete",
    ),
    path("newsletters/<int:pk>/send/", views.newsletter_send, name="newsletter_send"),
]
