from django.urls import path
from . import views

urlpatterns = [
    path("orders/create/", views.CreateOrderView.as_view(), name="create-order"),
    path("orders/<str:order_number>/confirm/", views.ConfirmOrderView.as_view(), name="confirm-order"),
    path("orders/<str:order_number>/", views.GetOrderView.as_view(), name="get-order"),
]
