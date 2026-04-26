from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="JTEC API",
        default_version="v1",
        description=(
            "API do sistema de loja JTEC.\n\n"
            "Fluxo principal:\n"
            "1. `POST /api/orders/create/` — cria pedido e gera QR code PIX\n"
            "2. `POST /api/orders/{order_number}/confirm/` — cliente confirma que pagou\n"
            "3. `GET /api/orders/{order_number}/` — consulta detalhes do pedido"
        ),
        contact=openapi.Contact(
            name="JTEC",
            email="jtecBH@hotmail.com",
            url="https://jotatec.netlify.app",
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),

    # Swagger UI
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]
