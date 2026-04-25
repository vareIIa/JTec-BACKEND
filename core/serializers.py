from rest_framework import serializers
from .models import Customer, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_id", "product_name", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_number",
            "total",
            "status",
            "pix_payload",
            "items",
            "customer_email",
            "customer_name",
            "created_at",
        ]
