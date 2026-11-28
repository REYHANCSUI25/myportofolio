from rest_framework import serializers

from main.models import Education, Experience
from main.validators import strip_html_required, validate_period


class EducationSerializer(serializers.ModelSerializer):
    is_ongoing = serializers.BooleanField(read_only=True)
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = Education
        fields = [
            "id",
            "institution",
            "degree",
            "description",
            "started_at",
            "ended_at",
            "is_ongoing",
            "star_count",
            "is_starred",
        ]
        read_only_fields = ["id"]

    def validate_institution(self, value):
        return strip_html_required(value)

    def validate_degree(self, value):
        return strip_html_required(value)

    def validate_description(self, value):
        return strip_html_required(value)

    def validate(self, attrs):
        if "started_at" in attrs or "ended_at" in attrs:
            validate_period(
                attrs.get("started_at", getattr(self.instance, "started_at", None)),
                attrs.get("ended_at", getattr(self.instance, "ended_at", None)),
            )
        return attrs

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return any(user.pk == request.user.pk for user in obj.starred_by.all())


class ExperienceSerializer(serializers.ModelSerializer):
    is_ongoing = serializers.BooleanField(read_only=True)

    class Meta:
        model = Experience
        fields = [
            "id",
            "title",
            "category",
            "description",
            "thumbnail",
            "started_at",
            "ended_at",
            "is_ongoing",
        ]
        read_only_fields = ["id", "started_at"]

    def validate_title(self, value):
        return strip_html_required(value)

    def validate_description(self, value):
        return strip_html_required(value)
