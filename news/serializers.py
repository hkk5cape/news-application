from rest_framework import serializers
from .models import Article, Newsletter, Publisher, User
from .policies import can_publish_under


class UserSerializer(serializers.ModelSerializer):
    subscriptions = serializers.SerializerMethodField()
    independent_articles = serializers.SerializerMethodField()
    independent_newsletters = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "role",
            "subscriptions",
            "independent_articles",
            "independent_newsletters",
        ]

    def get_subscriptions(self, obj):
        if obj.role != "reader":
            return None
        return {
            "publishers": list(obj.subscribed_publishers.values_list("pk", flat=True)),
            "journalists": list(
                obj.subscribed_journalists.values_list("pk", flat=True)
            ),
        }

    def get_independent_articles(self, obj):
        return (
            list(obj.independent_articles.values_list("pk", flat=True))
            if obj.independent_articles is not None
            else None
        )

    def get_independent_newsletters(self, obj):
        return (
            list(obj.independent_newsletters.values_list("pk", flat=True))
            if obj.independent_newsletters is not None
            else None
        )


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "description", "editors", "journalists"]
        read_only_fields = fields


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "created_at",
            "approved",
            "publisher",
            "revision",
            "approved_by",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "approved",
            "revision",
            "approved_by",
        ]

    def validate_publisher(self, publisher):
        if not can_publish_under(self.context["request"].user, publisher):
            raise serializers.ValidationError("You are not assigned to this publisher.")
        return publisher


class NewsletterSerializer(serializers.ModelSerializer):
    articles = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Article.objects.filter(approved=True)
    )

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "publisher",
            "articles",
            "revision",
        ]
        read_only_fields = ["id", "created_at", "author", "revision"]

    def validate_publisher(self, publisher):
        if not can_publish_under(self.context["request"].user, publisher):
            raise serializers.ValidationError("You are not assigned to this publisher.")
        return publisher

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["articles"] = list(
            instance.articles.filter(approved=True).values_list("pk", flat=True)
        )
        return data
