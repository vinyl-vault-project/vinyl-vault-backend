from rest_framework import status
from rest_framework.exceptions import APIException


class OrderCancellationConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Only pending orders can be canceled."
    default_code = "order_not_cancelable"


class ProductAlreadyInCartConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Product is already in the cart."
    default_code = "product_already_in_cart"
