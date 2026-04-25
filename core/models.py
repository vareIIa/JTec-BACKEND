import random
import string
from django.db import models


def _gen_order_number():
    suffix = "".join(random.choices(string.digits, k=6))
    return f"JTEC{suffix}"


class Customer(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    google_id = models.CharField(max_length=200, blank=True)
    google_picture = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or self.email

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["-created_at"]


class Order(models.Model):
    PENDING = "pending"
    AWAITING = "awaiting_payment"
    PAID = "paid"
    DELIVERED = "delivered"

    STATUS_CHOICES = [
        (PENDING, "Pendente"),
        (AWAITING, "Aguardando Pagamento"),
        (PAID, "Pago"),
        (DELIVERED, "Entregue"),
    ]

    order_number = models.CharField(max_length=20, unique=True, default=_gen_order_number)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    pix_payload = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_number} — {self.customer}"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} — {self.order.order_number}"

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
