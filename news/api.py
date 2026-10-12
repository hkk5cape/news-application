from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ApprovalEvent, ApprovedLog, Article, Newsletter, Publisher
from .policies import can_edit, is_editor, subscribed_articles
from .serializers import (
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
    UserSerializer,
)
from .services import approve_article, dispatch_approval


class ArticleAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST":
            return request.user.role == "journalist" and request.user.has_perm(
                "news.add_article"
            )
        return request.user.has_perm(
            "news.change_article"
            if request.method != "DELETE"
            else "news.delete_article"
        )

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or can_edit(request.user, obj)


class ArticleList(generics.ListCreateAPIView):
    permission_classes = [ArticleAccess]
    serializer_class = ArticleSerializer
    queryset = Article.objects.filter(approved=True).select_related(
        "author", "publisher"
    )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, approved=False)


class SubscribedArticles(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        if self.request.user.role != "reader":
            raise PermissionDenied("This endpoint is for readers.")
        return subscribed_articles(self.request.user)


class ArticleDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [ArticleAccess]

    def get_queryset(self):
        user = self.request.user
        visible = Q(approved=True) | Q(author=user)
        if is_editor(user):
            visible |= Q(publisher=None) | Q(publisher__editors=user)
        return Article.objects.filter(visible).distinct()

    def perform_update(self, serializer):
        serializer.save(
            approved=False, approved_by=None, revision=serializer.instance.revision + 1
        )


class ApproveArticle(APIView):
    def post(self, request, pk):
        get_object_or_404(Article, pk=pk)
        if not is_editor(request.user) or not request.user.has_perm(
            "news.approve_article"
        ):
            raise PermissionDenied
        event = approve_article(pk, request.user)
        dispatch_approval(event)
        return Response(
            {
                "event_id": event.pk,
                "approved": True,
                "api_logged": event.api_logged,
                "pending_emails": event.deliveries.filter(sent=False).count(),
            }
        )


class ApprovedEndpoint(APIView):
    def post(self, request):
        if not is_editor(request.user):
            raise PermissionDenied
        try:
            event_id = int(request.data.get("event_id"))
        except (ValueError, TypeError):
            return Response({"event_id": "A valid event ID is required."}, status=400)
        with transaction.atomic():
            event = get_object_or_404(
                ApprovalEvent.objects.select_for_update(), pk=event_id
            )
            if event.approved_by_id != request.user.pk:
                raise PermissionDenied
            log, created = ApprovedLog.objects.get_or_create(
                event=event, defaults={"payload": event.snapshot}
            )
        return Response(
            {"id": log.pk, "event_id": event.pk}, status=201 if created else 200
        )

    def get(self, request):
        if not is_editor(request.user):
            raise PermissionDenied
        logs = ApprovedLog.objects.filter(event__approved_by=request.user).order_by(
            "-pk"
        )[:100]
        return Response(
            [
                {"id": item.pk, "event_id": item.event_id, "payload": item.payload}
                for item in logs
            ]
        )


class NewsletterAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        action = (
            "add"
            if request.method == "POST"
            else "delete"
            if request.method == "DELETE"
            else "change"
        )
        return request.user.has_perm(f"news.{action}_newsletter")

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or can_edit(request.user, obj)


class NewsletterList(generics.ListCreateAPIView):
    permission_classes = [NewsletterAccess]
    serializer_class = NewsletterSerializer
    queryset = Newsletter.objects.prefetch_related("articles").all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NewsletterDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [NewsletterAccess]
    serializer_class = NewsletterSerializer
    queryset = Newsletter.objects.prefetch_related("articles").all()

    def perform_update(self, serializer):
        serializer.save(revision=serializer.instance.revision + 1)


class PublisherList(generics.ListAPIView):
    serializer_class = PublisherSerializer
    queryset = Publisher.objects.prefetch_related("editors", "journalists").order_by(
        "name"
    )


class Me(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
