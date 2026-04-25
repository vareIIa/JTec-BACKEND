from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Customer, Order, OrderItem
from .serializers import OrderSerializer
from .pix import generate_pix_payload

PIX_KEY = "+5531985975200"
MERCHANT_NAME = "JTEC"
MERCHANT_CITY = "BELO HORIZONTE"


class CreateOrderView(APIView):
    def post(self, request):
        customer_data = request.data.get("customer", {})
        items_data = request.data.get("items", [])

        email = (customer_data.get("email") or "").strip().lower()
        if not email:
            return Response({"error": "E-mail é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        if not items_data:
            return Response({"error": "Carrinho vazio."}, status=status.HTTP_400_BAD_REQUEST)

        customer, _ = Customer.objects.update_or_create(
            email=email,
            defaults={
                "name": customer_data.get("name", ""),
                "google_id": customer_data.get("google_id", ""),
                "google_picture": customer_data.get("google_picture", ""),
            },
        )

        total = sum(Decimal(str(item.get("price", 0))) for item in items_data)

        order = Order.objects.create(customer=customer, total=total)

        order.pix_payload = generate_pix_payload(
            pix_key=PIX_KEY,
            amount=float(total),
            merchant_name=MERCHANT_NAME,
            merchant_city=MERCHANT_CITY,
            txid=order.order_number,
        )
        order.save(update_fields=["pix_payload"])

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product_id=item.get("product_id", ""),
                product_name=item.get("product_name", ""),
                price=Decimal(str(item.get("price", 0))),
            )
            for item in items_data
        ])

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConfirmOrderView(APIView):
    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({"error": "Pedido não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        order.status = Order.AWAITING
        order.save(update_fields=["status", "updated_at"])

        return Response({"order_number": order.order_number, "status": order.status})


class GetOrderView(APIView):
    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({"error": "Pedido não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data)
