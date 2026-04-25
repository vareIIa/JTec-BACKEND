from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Customer, Order, OrderItem
from .serializers import OrderSerializer
from .pix import generate_pix_payload

PIX_KEY = "+5531985975200"
MERCHANT_NAME = "JTEC"
MERCHANT_CITY = "BELO HORIZONTE"

# ── Schemas para documentação ──────────────────────────────

_customer_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["email"],
    properties={
        "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", example="cliente@email.com"),
        "name": openapi.Schema(type=openapi.TYPE_STRING, example="João Silva"),
        "google_id": openapi.Schema(type=openapi.TYPE_STRING, description="ID do Google (preenchido pelo OAuth)", example="1099234567890"),
        "google_picture": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL da foto do Google"),
    },
)

_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["product_id", "product_name", "price"],
    properties={
        "product_id": openapi.Schema(type=openapi.TYPE_STRING, example="starter-next-15"),
        "product_name": openapi.Schema(type=openapi.TYPE_STRING, example="Starter Kit Next.js 15 + Tailwind v4"),
        "price": openapi.Schema(type=openapi.TYPE_NUMBER, example=297.00),
    },
)

_create_order_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["customer", "items"],
    properties={
        "customer": _customer_schema,
        "items": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=_item_schema,
        ),
    },
    example={
        "customer": {"email": "cliente@email.com", "name": "João Silva"},
        "items": [
            {"product_id": "starter-next-15", "product_name": "Starter Kit Next.js 15", "price": 297.00},
            {"product_id": "course-llm-pratica", "product_name": "Curso: LLMs na Prática", "price": 197.00},
        ],
    },
)

_order_response = openapi.Response(
    description="Pedido criado com sucesso",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "order_number": openapi.Schema(type=openapi.TYPE_STRING, example="JTEC482019"),
            "total": openapi.Schema(type=openapi.TYPE_STRING, example="494.00"),
            "status": openapi.Schema(type=openapi.TYPE_STRING, example="pending"),
            "pix_payload": openapi.Schema(type=openapi.TYPE_STRING, description="Payload EMV do QR code PIX"),
            "customer_email": openapi.Schema(type=openapi.TYPE_STRING, example="cliente@email.com"),
            "customer_name": openapi.Schema(type=openapi.TYPE_STRING, example="João Silva"),
            "items": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "product_id": openapi.Schema(type=openapi.TYPE_STRING),
                        "product_name": openapi.Schema(type=openapi.TYPE_STRING),
                        "price": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
        },
    ),
)


class CreateOrderView(APIView):
    @swagger_auto_schema(
        operation_id="create_order",
        operation_summary="Criar pedido e gerar PIX",
        operation_description=(
            "Cria um novo pedido com os itens do carrinho, salva o cliente no banco "
            "e gera o payload EMV do QR code PIX com o valor total.\n\n"
            "O `pix_payload` retornado deve ser passado para a biblioteca `qrcode.react` "
            "no frontend para renderizar o QR code."
        ),
        request_body=_create_order_body,
        responses={
            201: _order_response,
            400: openapi.Response(
                description="Dados inválidos",
                examples={"application/json": {"error": "E-mail é obrigatório."}},
            ),
        },
        tags=["Pedidos"],
    )
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
    @swagger_auto_schema(
        operation_id="confirm_order",
        operation_summary="Confirmar pagamento PIX",
        operation_description=(
            "Chamado pelo frontend quando o cliente clica em 'Já paguei'. "
            "Atualiza o status do pedido para `awaiting_payment` para que o admin "
            "possa verificar e enviar os produtos."
        ),
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={
            200: openapi.Response(
                description="Status atualizado",
                examples={"application/json": {"order_number": "JTEC482019", "status": "awaiting_payment"}},
            ),
            404: openapi.Response(
                description="Pedido não encontrado",
                examples={"application/json": {"error": "Pedido não encontrado."}},
            ),
        },
        tags=["Pedidos"],
    )
    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({"error": "Pedido não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        order.status = Order.AWAITING
        order.save(update_fields=["status", "updated_at"])

        return Response({"order_number": order.order_number, "status": order.status})


class GetOrderView(APIView):
    @swagger_auto_schema(
        operation_id="get_order",
        operation_summary="Consultar pedido",
        operation_description="Retorna os detalhes completos de um pedido pelo número (ex: JTEC482019).",
        manual_parameters=[
            openapi.Parameter(
                "order_number",
                openapi.IN_PATH,
                description="Número do pedido gerado automaticamente",
                type=openapi.TYPE_STRING,
                example="JTEC482019",
            )
        ],
        responses={
            200: _order_response,
            404: openapi.Response(
                description="Pedido não encontrado",
                examples={"application/json": {"error": "Pedido não encontrado."}},
            ),
        },
        tags=["Pedidos"],
    )
    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({"error": "Pedido não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data)
