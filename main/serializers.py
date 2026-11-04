from rest_framework import serializers

from main.models import Education
from main.validators import strip_html, strip_html_required


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
        return strip_html(value)

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return any(user.pk == request.user.pk for user in obj.starred_by.all())
