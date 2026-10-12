from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import api

urlpatterns = [
    path("token/", obtain_auth_token, name="api_token"),
    path("me/", api.Me.as_view(), name="api_me"),
    path("articles/", api.ArticleList.as_view(), name="api_articles"),
    path(
        "articles/subscribed/", api.SubscribedArticles.as_view(), name="api_subscribed"
    ),
    path("articles/<int:pk>/", api.ArticleDetail.as_view(), name="api_article"),
    path(
        "articles/<int:pk>/approve/", api.ApproveArticle.as_view(), name="api_approve"
    ),
    path("approved/", api.ApprovedEndpoint.as_view(), name="api_approved"),
    path("publishers/", api.PublisherList.as_view(), name="api_publishers"),
    path("newsletters/", api.NewsletterList.as_view(), name="api_newsletters"),
    path(
        "newsletters/<int:pk>/", api.NewsletterDetail.as_view(), name="api_newsletter"
    ),
]
