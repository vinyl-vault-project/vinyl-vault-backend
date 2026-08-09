from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    summary="Check API health",
    description="Confirm that the backend application can respond to HTTP requests.",
    responses={
        status.HTTP_200_OK: inline_serializer(
            name="HealthCheckResponse",
            fields={"status": serializers.CharField()},
        )
    },
    tags=["Health"],
    auth=[],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"})
