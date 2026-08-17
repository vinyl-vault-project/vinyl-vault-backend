from django.urls import include, path
from rest_framework.routers import SimpleRouter

from orders.views import CartItemViewSet, CartView

router = SimpleRouter()
router.register("cart/items", CartItemViewSet, basename="cart-item")

app_name = "orders"

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart-detail"),
    path("", include(router.urls)),
]
