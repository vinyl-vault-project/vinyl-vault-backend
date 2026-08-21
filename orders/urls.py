from django.urls import include, path
from rest_framework.routers import DefaultRouter

from orders.views.cart import CartItemViewSet, CartView
from orders.views.order import OrderViewSet

router = DefaultRouter()
router.register("cart/items", CartItemViewSet, basename="cart-item")
router.register("orders", OrderViewSet, basename="order")

app_name = "orders"

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart-detail"),
    path("", include(router.urls)),
]
