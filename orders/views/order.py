from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order, OrderItem
from orders.serializers.order import (
    OrderCheckoutSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
)
from orders.services.order import cancel_order, checkout


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderDetailSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "order_number"

    def _base_queryset(self):
        queryset = Order.objects.all()
        return queryset.filter(user=self.request.user)

    def _list_queryset(self):
        items = OrderItem.objects.select_related("product__release").order_by("pk")
        return self._base_queryset().prefetch_related(Prefetch("items", queryset=items))

    def _detail_queryset(self):
        items = (
            OrderItem.objects.select_related("product__release")
            .prefetch_related(
                "product__release__artists",
                "product__labels",
            )
            .order_by("pk")
        )
        return self._base_queryset().prefetch_related(Prefetch("items", queryset=items))

    def get_queryset(self):
        if self.action == "list":
            return self._list_queryset()
        if self.action == "retrieve":
            return self._detail_queryset()
        return self._base_queryset()

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCheckoutSerializer
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    @extend_schema(
        summary="Create an order from the current user's cart",
        description=(
            "Validate and atomically convert the authenticated user's cart "
            "into a pending order."
        ),
        request=OrderCheckoutSerializer,
        responses={
            status.HTTP_201_CREATED: OrderDetailSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="The checkout data or cart contents are invalid."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="A valid JWT access token is required."
            ),
        },
        tags=["Orders"],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_order = checkout(
            user=request.user,
            checkout_data=serializer.validated_data,
        )
        order = self._detail_queryset().get(pk=created_order.pk)
        response_data = OrderDetailSerializer(
            order,
            context=self.get_serializer_context(),
        ).data

        return Response(response_data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Cancel an order",
        description=(
            "Cancel a pending order owned by the authenticated user and "
            "restore its product stock."
        ),
        request=None,
        responses={
            status.HTTP_200_OK: OrderDetailSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="A valid JWT access token is required."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="The order was not found."
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="Only pending orders can be canceled."
            ),
        },
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, *args, **kwargs):
        order = self.get_object()
        canceled_order = cancel_order(order=order)

        order = self._detail_queryset().get(pk=canceled_order.pk)
        response_data = OrderDetailSerializer(
            order,
            context=self.get_serializer_context(),
        ).data

        return Response(response_data, status=status.HTTP_200_OK)
