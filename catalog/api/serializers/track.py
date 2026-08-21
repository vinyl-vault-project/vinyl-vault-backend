from rest_framework import serializers

from catalog.models import Track


class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ["id", "side", "position", "title", "duration_seconds", "audio_preview_url"]

