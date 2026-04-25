# JTEC Backend — E-commerce REST API

Production-ready Django REST API for JTEC e-commerce platform with PIX payment integration.

**Live API:** [https://jtec-backend.onrender.com](https://jtec-backend.onrender.com)  
**Swagger Docs:** [https://jtec-backend.onrender.com/swagger/](https://jtec-backend.onrender.com/swagger/)  
**ReDoc:** [https://jtec-backend.onrender.com/redoc/](https://jtec-backend.onrender.com/redoc/)

---

## 📋 Overview

RESTful API for managing e-commerce orders with PIX payment support. Handles:
- Customer creation/updates (with Google OAuth data)
- Order creation with auto-generated IDs
- PIX EMV QR code payload generation
- Order status tracking
- Real-time order lookups

**Tech Stack:**
- Django 6.0.4
- Django REST Framework
- PostgreSQL (Neon serverless)
- drf-yasg (Swagger/ReDoc)
- Gunicorn (production WSGI)
- WhiteNoise (static files)

---

## 🚀 Quick Start

### Local Development

```bash
# Setup
git clone https://github.com/vareIIa/JTec-BACKEND.git
cd JTec-BACKEND
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Initialize database
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver
```

Visit `http://localhost:8000/swagger/` for interactive API docs.

### Environment Variables

**.env (local development):**
```env
DEBUG=True
SECRET_KEY=django-insecure-your-dev-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/jtec_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**.env (production on Render):**
```env
DEBUG=False
SECRET_KEY=your-strong-secret-key-min-50-chars
DATABASE_URL=postgresql://neon_user:pass@ep-xxx-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require
ALLOWED_HOSTS=jtec-backend.onrender.com
CORS_ALLOWED_ORIGINS=https://jotatec.netlify.app
```

---

## 📚 API Endpoints

### 1. Create Order & Generate PIX

**Request:**
```http
POST /api/orders/create/
Content-Type: application/json

{
  "customer": {
    "email": "cliente@example.com",
    "name": "João Silva",
    "google_id": "1234567890",
    "google_picture": "https://example.com/photo.jpg"
  },
  "items": [
    {
      "product_id": "starter-next-15",
      "product_name": "Starter Kit Next.js 15 + Tailwind v4",
      "price": 297.00
    },
    {
      "product_id": "course-llm-pratica",
      "product_name": "Curso: LLMs na Prática",
      "price": 197.00
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "order_number": "JTEC482019",
  "total": "494.00",
  "status": "pending",
  "pix_payload": "00020126580014br.gov.bcb.pix0136...",
  "customer_email": "cliente@example.com",
  "customer_name": "João Silva",
  "items": [
    {
      "product_id": "starter-next-15",
      "product_name": "Starter Kit Next.js 15 + Tailwind v4",
      "price": "297.00"
    },
    {
      "product_id": "course-llm-pratica",
      "product_name": "Curso: LLMs na Prática",
      "price": "197.00"
    }
  ],
  "created_at": "2026-04-25T14:30:00Z"
}
```

**Error (400):**
```json
{
  "error": "E-mail é obrigatório."
}
```

### 2. Confirm Order Payment

**Request:**
```http
POST /api/orders/{order_number}/confirm/
Content-Type: application/json

{}
```

**Response (200 OK):**
```json
{
  "order_number": "JTEC482019",
  "status": "awaiting_payment"
}
```

**Error (404):**
```json
{
  "error": "Pedido não encontrado."
}
```

### 3. Get Order Details

**Request:**
```http
GET /api/orders/{order_number}/
```

**Response (200 OK):**
```json
{
  "order_number": "JTEC482019",
  "total": "494.00",
  "status": "awaiting_payment",
  "pix_payload": "00020126580014br.gov.bcb.pix0136...",
  "customer_email": "cliente@example.com",
  "customer_name": "João Silva",
  "items": [
    {
      "product_id": "starter-next-15",
      "product_name": "Starter Kit Next.js 15 + Tailwind v4",
      "price": "297.00"
    }
  ],
  "created_at": "2026-04-25T14:30:00Z"
}
```

---

## 🏗️ Database Schema

### Customer
```sql
CREATE TABLE customer (
  id SERIAL PRIMARY KEY,
  email VARCHAR(254) UNIQUE NOT NULL,
  name VARCHAR(255),
  google_id VARCHAR(255),
  google_picture VARCHAR(500),
  created_at TIMESTAMP AUTO_NOW_ADD,
  updated_at TIMESTAMP AUTO_NOW
);
```

### Order
```sql
CREATE TABLE order (
  id SERIAL PRIMARY KEY,
  order_number VARCHAR(20) UNIQUE NOT NULL,  -- e.g., JTEC482019
  customer_id INT FOREIGN KEY,
  total DECIMAL(10, 2),
  status VARCHAR(20),  -- pending, awaiting_payment, paid, delivered
  pix_payload TEXT,
  created_at TIMESTAMP AUTO_NOW_ADD,
  updated_at TIMESTAMP AUTO_NOW
);
```

### OrderItem
```sql
CREATE TABLE order_item (
  id SERIAL PRIMARY KEY,
  order_id INT FOREIGN KEY,
  product_id VARCHAR(255),
  product_name VARCHAR(255),
  price DECIMAL(10, 2),
  created_at TIMESTAMP AUTO_NOW_ADD
);
```

---

## 💳 PIX Payment Integration

### Order Number Format
- **Pattern:** `JTEC` + 6-digit random
- **Example:** `JTEC482019`, `JTEC791543`
- **Used as:** PIX `txid` (transaction ID for manual reconciliation)

### PIX Payload Generation
The backend generates EMV-formatted PIX QR code payloads compliant with [Brazilian Central Bank specifications](https://www.bcb.gov.br/).

**Generated payload includes:**
- **PIX Key:** `+5531985975200` (personal key)
- **Merchant Name:** `JTEC`
- **Merchant City:** `BELO HORIZONTE`
- **Amount:** Order total
- **TxID:** Order number
- **CRC16-CCITT:** Checksum for integrity

**Frontend uses this payload with `qrcode.react` to generate scannable QR code.**

### Configuration
Edit `core/views.py`:
```python
PIX_KEY = "+5531985975200"
MERCHANT_NAME = "JTEC"
MERCHANT_CITY = "BELO HORIZONTE"
```

---

## 🔄 Order Status Workflow

```
CREATE ORDER
    ↓
pending (PIX QR displayed, user hasn't paid)
    ↓
(User scans & pays)
    ↓
awaiting_payment (User clicked "Já paguei!", admin reviews)
    ↓
(Admin confirms payment in bank)
    ↓
paid (Admin sends products)
    ↓
delivered (Customer received)
```

**Status transitions:**
- Frontend: `pending` → `awaiting_payment` (via `/confirm/` endpoint)
- Admin: `awaiting_payment` → `paid` → `delivered` (manual via Django admin)

---

## 🚀 Deployment (Render)

### Prerequisites
- GitHub repo pushed
- Neon PostgreSQL account with connection string

### Steps

1. **Connect to Render:**
   - Sign up at [render.com](https://render.com)
   - New → Web Service
   - Connect GitHub repo → select `JTec-BACKEND`

2. **Configure:**
   - **Name:** `jtec-backend`
   - **Environment:** `Python`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && \
     python manage.py collectstatic --noinput && \
     python manage.py migrate
     ```
   - **Start Command:**
     ```bash
     gunicorn JTEC.wsgi:application --bind 0.0.0.0:$PORT --workers 2
     ```

3. **Environment Variables:**
   | Key | Value |
   |-----|-------|
   | `DEBUG` | `False` |
   | `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DATABASE_URL` | From Neon console |
   | `ALLOWED_HOSTS` | `jtec-backend.onrender.com` |
   | `CORS_ALLOWED_ORIGINS` | `https://jotatec.netlify.app` |

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for build (~2-3 min)
   - Visit `https://jtec-backend.onrender.com/swagger/` to verify

### Auto-Deploy
- Push to `main` branch → Render auto-builds & deploys
- Build logs visible in Render dashboard

---

## 🗄️ Database Setup (Neon)

### Initial Setup
1. Create account at [neon.tech](https://neon.tech)
2. Create project → copy connection string
3. Add `DATABASE_URL` to Render env vars
4. **First deploy auto-runs migrations** (`python manage.py migrate`)

### Manual Migrations
```bash
# Local
python manage.py migrate

# Remote (SSH into Render)
python manage.py migrate --database=production
```

### Database Query
```bash
# Connect to Neon from local
psql postgresql://user:pass@ep-xxx.c-5.us-east-1.aws.neon.tech/neondb

# View tables
\dt

# Query orders
SELECT * FROM core_order ORDER BY created_at DESC LIMIT 10;
```

---

## 📊 Admin Panel

Django admin available at `/admin/`:

1. **Create superuser (local):**
   ```bash
   python manage.py createsuperuser
   ```

2. **Access:**
   - Local: `http://localhost:8000/admin/`
   - Production: `https://jtec-backend.onrender.com/admin/`

3. **Manage:**
   - View all customers
   - View all orders (filter by status)
   - Manually mark orders as `paid`/`delivered`
   - Bulk actions

---

## 🔐 Security

### Production Checklist
- [x] `DEBUG=False` in production
- [x] `SECRET_KEY` is strong (50+ chars, random)
- [x] `ALLOWED_HOSTS` restricted to domain
- [x] `CORS_ALLOWED_ORIGINS` restricted to frontend domain
- [x] Database uses SSL (`sslmode=require`)
- [x] HTTPS enforced (Render auto-upgrades)
- [x] Cookies set secure in production (`SESSION_COOKIE_SECURE`)

### Environment Variables
- Never commit `.env` file
- Use platform-specific secret managers (Render dashboard, etc.)
- Rotate `SECRET_KEY` periodically

---

## 🧪 Testing

### Manual API Testing

**Using curl:**
```bash
curl -X POST http://localhost:8000/api/orders/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": {"email": "test@example.com", "name": "Test User"},
    "items": [{"product_id": "test-1", "product_name": "Test", "price": 100.00}]
  }'
```

**Using Swagger UI:**
Visit `http://localhost:8000/swagger/` → click "Try it out" on any endpoint

### Automated Tests
```bash
python manage.py test core
```

---

## 📈 Monitoring

### Logs
- **Local:** `python manage.py runserver` output
- **Render:** Logs tab in dashboard (auto-scrolls)

### Common Issues

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'rest_framework'` | Run `pip install -r requirements.txt` |
| `OperationalError: no such table` | Run `python manage.py migrate` |
| `CORS errors` | Check `CORS_ALLOWED_ORIGINS` matches frontend domain |
| `404 on /api/orders/` | Verify URL in frontend matches backend domain |
| `Gunicorn bind error` | Render sets `$PORT` automatically, don't hardcode |

---

## 📝 File Structure

```
JTec-BACKEND/
├── core/
│   ├── models.py          # Customer, Order, OrderItem
│   ├── views.py           # CreateOrderView, ConfirmOrderView, GetOrderView
│   ├── serializers.py     # OrderSerializer
│   ├── pix.py             # PIX payload generation (CRC16-CCITT)
│   └── urls.py            # /api/orders/* routes
├── JTEC/
│   ├── settings.py        # Django config (CORS, DRF, Swagger, DB)
│   ├── urls.py            # Root routes + Swagger schema
│   ├── wsgi.py            # WSGI app for Gunicorn
│   └── asgi.py            # ASGI app (async)
├── manage.py              # Django CLI
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── build.sh               # Build script for Render
├── render.yaml            # Render deployment config
└── README.md              # This file
```

---

## 🔗 Related Repositories

- **Frontend:** [github.com/vareIIa/JTec](https://github.com/vareIIa/JTec)
- **Backend:** [github.com/vareIIa/JTec-BACKEND](https://github.com/vareIIa/JTec-BACKEND)

---

## 📄 License & Contact

Built with ❤️ by JTEC — João Vitor C. Varella

- **Email:** jvvarella@hotmail.com
- **Phone:** [(31) 98597-5200](tel:+5531985975200)
- **Website:** [jotatec.netlify.app](https://jotatec.netlify.app)
- **LinkedIn:** [linkedin.com/in/joaovitorvarella](https://linkedin.com/in/joaovitorvarella)

---

**Status:** ✅ Production ready | Last updated: April 2026
