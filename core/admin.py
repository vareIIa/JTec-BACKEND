from django.contrib import admin
from .models import Customer, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product_id", "product_name", "price"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "customer", "total", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "customer__email", "customer__name"]
    readonly_fields = ["order_number", "pix_payload", "created_at", "updated_at"]
    inlines = [OrderItemInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["email", "name", "created_at"]
    search_fields = ["email", "name"]
    readonly_fields = ["created_at", "updated_at"]
