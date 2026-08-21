from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Cart, CartItem
from orders.serializers.cart import (
    CartItemCreateSerializer,
    CartItemReadSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
)
from orders.services.cart import (
    add_cart_item,
    remove_cart_item,
    update_cart_item_quantity,
)


class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Get the current user's cart",
        description="Return the authenticated user's cart and its items.",
        responses={
            status.HTTP_200_OK: CartSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="A valid JWT access token is required."
            ),
        },
        tags=["Cart"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        items = CartItem.objects.select_related("product__release").prefetch_related(
            "product__release__artists"
        )

        return Cart.objects.prefetch_related(Prefetch("items", queryset=items)).get(
            pk=cart.pk
        )


class CartItemViewSet(viewsets.GenericViewSet):
    serializer_class = CartItemReadSerializer
    permission_classes = (IsAuthenticated,)
    lookup_url_kwarg = "item_id"

    def get_serializer_class(self):
        if self.action == "create":
            return CartItemCreateSerializer
        if self.action == "partial_update":
            return CartItemUpdateSerializer

        return self.serializer_class

    def get_queryset(self):
        return (
            CartItem.objects.select_related("cart", "product__release")
            .prefetch_related("product__release__artists")
            .filter(cart__user=self.request.user)
        )

    def _serialize_item(self, item_id):
        item = self.get_queryset().get(pk=item_id)
        return CartItemReadSerializer(
            item,
            context=self.get_serializer_context(),
        ).data

    @extend_schema(
        summary="Add an item to the cart",
        description=(
            "Add an active, in-stock product to the authenticated user's cart."
        ),
        request=CartItemCreateSerializer,
        responses={
            status.HTTP_201_CREATED: CartItemReadSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="The product or quantity is invalid."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="A valid JWT access token is required."
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="The product is already in the cart."
            ),
        },
        tags=["Cart"],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        requested_product = serializer.validated_data["product"]

        item = add_cart_item(
            user=request.user,
            requested_product=requested_product,
            quantity=quantity,
        )

        return Response(
            self._serialize_item(item.pk),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a cart item quantity",
        description="Set a new quantity for an item in the current user's cart.",
        request=CartItemUpdateSerializer,
        responses={
            status.HTTP_200_OK: CartItemReadSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="The quantity is invalid or exceeds available stock."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="A valid JWT access token is required."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="The cart item was not found."
            ),
        },
        tags=["Cart"],
    )
    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]

        item = update_cart_item_quantity(
            user=request.user,
            item_id=self.kwargs[self.lookup_url_kwarg],
            quantity=quantity,
        )

        return Response(
            self._serialize_item(item.pk),
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Remove an item from the cart",
        description="Remove an item that belongs to the current user's cart.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="The cart item was removed."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="A valid JWT access token is required."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="The cart item was not found."
            ),
        },
        tags=["Cart"],
    )
    def destroy(self, request, *args, **kwargs):
        remove_cart_item(
            user=request.user,
            item_id=self.kwargs[self.lookup_url_kwarg],
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
