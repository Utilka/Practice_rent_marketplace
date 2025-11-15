# Rent_Mark Technical Requirements (v1)

### Version

MVP – Internal Developer Documentation

---

## 1. System Overview

### 1.1 Platform Summary

Rent_Mark is a student housing platform connecting **tenants (students)** and **landlords (owners/agencies)**. The MVP delivers a functional end-to-end product where tenants can search, apply, and communicate with landlords, and landlords can post listings and manage applications.

### 1.2 Architecture Summary

**Frontend:** React (SPA)
**Backend:** FastAPI (Python 3.11+)
**Database:** PostgreSQL (**AWS RDS**)
**File Storage:** **AWS S3** (private bucket, presigned upload)
**Notifications:** **AWS SES** (email)
**Hosting:** **Single EC2 instance** running **Docker Compose** (Caddy + API + worker + frontend + optional pgAdmin)
**Region:** **eu-west-1 (Ireland)** — cost-effective EU region

### 1.3 Logical Components

| Layer         | Component        | Description                                                         |
| ------------- | ---------------- | ------------------------------------------------------------------- |
| Frontend      | React web app    | Tenant + Landlord interfaces, connected to REST API                 |
| Backend       | FastAPI services | Auth, user management, listings, applications, messaging, documents |
| Database      | PostgreSQL       | Relational storage (users, listings, messages, docs)                |
| Storage       | S3               | Document and image uploads                                          |
| Notifications | SES / in-app     | Account events, message alerts                                      |

### 1.4 Core Data Flow

1. User registers via email or Google OAuth.
2. Tenant completes profile and dossier (uploads documents to S3).
3. Tenant searches listings, applies to property.
4. Landlord receives application, reviews dossier, accepts/rejects.
5. Chat opens between both parties; contract manually uploaded.

---

## 2. Environment & Infrastructure

### 2.1 Environments

| Env         | Purpose         | URL Example            |
| ----------- | --------------- | ---------------------- |
| **Dev**     | Local + testing | `localhost:8000`       |
| **Staging** | QA, pre-release | `staging.Rent_Mark.com` |
| **Prod**    | Live MVP        | `app.Rent_Mark.com`     |

### 2.2 Deployment (EC2 + Docker Compose)

* **Single EC2** VM runs Docker Compose with services:

  * `caddy`: reverse proxy (HTTP/2, automatic TLS via Let's Encrypt; WS supported)
  * `api`: FastAPI (Uvicorn workers)
  * `worker`: background jobs (Celery) for compression + emails
  * `redis`: queue/broker for Celery
  * `web`: React static build (served by Caddy)
  * `pgadmin` (optional, non-prod or VPN/IP-allowlisted in prod): PostgreSQL admin UI
* **Managed services kept minimal**: **RDS (PostgreSQL)** + **S3** + **SES** only.

**Note:** If `pgadmin` is enabled in prod, lock it to an **IP allowlist** and use a **strong admin password**.

### 2.3 Storage & Uploads

* Direct upload to **S3** via **presigned PUT** (100MB max/client)
* Client calls `POST /documents/finalize` → enqueues **compression job**
* Compression target: **≤10MB** per stored object (best-effort; see §Documents)

### 2.4 CI/CD

* GitHub Actions → build images → push to ECR (or Docker Hub) → SSH deploy to EC2 (compose pull + up)

### 2.5 Secrets & Configuration

* `.env` on EC2 and/or AWS Parameter Store for secrets.

```
REGION=eu-west-1
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
JWT_AUDIENCE=Rent_Mark
AWS_S3_BUCKET=Rent_Mark-storage
SES_REGION=eu-west-1
STRIPE_SECRET=sk_live_...
```

### 2.6 Security

* JWT verification (Cognito or future provider) via JWKS
* HTTPS enforced at Caddy; HSTS; CORS locked to prod/staging origins
* S3 objects private; access via presigned URLs

### 2.7 pgAdmin exposure (prod-safe)

* **Accessible on the web** but **restricted**:

  * **IP allowlist** at EC2 Security Group (add your office/home IPs).
  * **Strong password** for `PGADMIN_DEFAULT_PASSWORD` (min 20 chars).
  * Optional **basic auth** at Caddy in front of pgAdmin.
  * Disable in compose for environments where not needed.
* Never expose database directly; pgAdmin connects via internal Docker network to RDS.

---

## 3. Backend (FastAPI)

### 3.1 Module Overview

| Module           | Description                                        |
| ---------------- | -------------------------------------------------- |
| **auth**         | JWT-based login, signup, Google OAuth              |
| **users**        | Tenant / landlord profiles, role management        |
| **listings**     | CRUD operations for property listings              |
| **applications** | Tenant applications, status tracking               |
| **messaging**    | Chat threads between tenant ↔ landlord             |
| **documents**    | File upload + metadata (tenant dossier, contracts) |
| **contracts**    | Manual upload + association with applications      |

### 3.2 API Conventions

* RESTful endpoints (`/auth/login`, `/listings/{id}`)
* All requests/response use JSON
* Auth required except `/auth/*` and `/listings/public`
* Standard response format:

```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

* Pagination: `?page=1&limit=20`
* Errors: HTTP 400/401/404/500 with message field

### 3.3 Core Endpoints

#### **Auth**

```http
POST /auth/signup
{
  "email": "user@example.com",
  "password": "abc12345",
  "role": "tenant"
}
→ 201 Created
{
  "user_id": 12,
  "token": "<jwt>"
}
```

```http
POST /auth/login
{
  "email": "user@example.com",
  "password": "abc12345"
}
→ 200 OK
{
  "token": "<jwt>",
  "role": "tenant"
}
```

#### **Users / Profiles**

```http
GET /users/me
→ 200 OK
{
  "id": 12,
  "email": "user@example.com",
  "role": "tenant",
  "profile": {...}
}
```

```http
PUT /users/me
{
  "first_name": "Alex",
  "last_name": "Doe",
  "phone": "+33123456789"
}
→ 200 OK
```

#### **Listings**

```http
GET /listings?city=Paris&price_max=1000
→ 200 OK
{
  "results": [
    {"id":1, "title":"Studio Paris 18e", "price":720, "available":true}
  ]
}
```

```http
POST /landlord/listings
{
  "title": "Studio meublé 20m²",
  "city": "Paris",
  "rent": 720,
  "type": "studio",
  "rooms": 1,
  "documents_required": ["id_card", "proof_of_study"]
}
→ 201 Created
```

#### **Applications**
TODO We need to allow profile details to be rewritable per application
```http
POST /tenant/applications
{
  "listing_id": 1,
  "guarantor_id": 3
}
→ 201 Created
{
  "id": 45,
  "status": "pending"
}
```

```http
PATCH /applications/45
{
  "status": "accepted"
}
→ 200 OK
```

#### **Messaging**

```http
POST /messages
{
  "recipient_id": 21,
  "listing_id": 1,
  "content": "Bonjour, le logement est-il toujours disponible ?"
}
→ 201 Created
```

```http
GET /messages/thread/1
→ 200 OK
{
  "thread_id": 1,
  "participants": [12,21],
  "messages": [
    {"sender":12, "content":"Bonjour", "created_at":"2025-07-27T12:00"}
  ]
}
```

#### **Documents / Contracts**

```http
POST /documents/presign
{
  "filename": "id_card.pdf",
  "content_type": "application/pdf"
}
→ 200 OK
{
  "upload_url": "https://s3.aws...",
  "file_id": 99
}
```

```http
POST /contracts
{
  "application_id": 45,
  "file_id": 99
}
→ 201 Created
```

---

## 4. Engineering Practices (MVP)

* **Auth**: TBD
* **API**: FastAPI + Pydantic v2; consistent error envelope; pagination `page/limit`.
* **DB**: SQLAlchemy 2.x + Alembic; UUID PKs; snake_case.
* **Files**: S3 + presigned URLs; **post-upload compression pipeline** via Celery worker.
* **Security**: CORS allowlist; rate limiting (slowapi) on auth/messaging; request size limits.
* **Quality**: ruff + mypy + black + pre-commit; CI running tests; branch protections.
* **Observability**: structured logs; request IDs; `/healthz`; Sentry-compatible error reporting.
* **I18n**: backend returns i18n keys; frontend handles ENG/UKR.
* **GDPR**: Right-to-erasure; data export; S3 lifecycle rules.

---

## 5. Authentication Design TBD

---

## 6. Locked Decisions & Implications

**(Applied from your latest message)**

1. **Infra**: Single **EC2 + Docker Compose** for app stack; only **RDS**, **S3**, **SES** as managed services. Region **eu-west-1 (Ireland)**.
2. **Roles**: `tenant`, `landlord`, `admin` (internal admin UI).
3. **Messaging**: Default **polling** (10s). WebSocket optional later (see estimate below).
4. **Documents**: Client upload limit **100MB**; stored size **≤10MB** after compression; allowed types: `pdf, doc, docx, odt, jpg, jpeg, png, application/octet-stream` (contracts).
5. **Listings auto-close**: Single-unit closes upon landlord choosing tenant. **Multi-room** tracked per **room**; listing closes when all rooms filled.
6. **Applications lifecycle**: `pending` → (`withdrawn` by tenant | `rejected` by landlord | `accepted_pending_payment` by landlord) → `confirmed` after first payment.
7. **Guarantors**: Landlord-configured **required count** (0..50). Max per application **50**.
8. **Payments**: **Stripe Payments** (single merchant account) for **first payment** to Rent_Mark; manual pass-through to landlord offline. No Connect/marketplace in MVP.
9. **Credits/Boost**: **Deferred (post-MVP)**.
10. **Locale**: **FR** only; currency **EUR**; timezone **Europe/Paris**.
11. **PII & Documents**: Two scopes: **profile-level** (persist until user deletion) and **application-level** (retention rules below).
12. **Admin**: Can **ban/unban tenants/landlords**, **takedown listings**.

---

## 7. WebSockets

The app should begin with polling and migrate to websockets in the future

---

## 8. Database Schema (MVP)

**Note:** ERD described textually; formal diagram can be added later.

### 8.1 Entities

* **users** `(id uuid, email, role enum[tenant, landlord, admin], created_at, status enum[active,banned])`
* **tenant_profile** `(user_id PK/FK, first_name, last_name, phone, nationality, birth_date, education, budget_eur)`
* **landlord_profile** `(user_id PK/FK, org_name, contact_name, phone)`
* **listings** `(id uuid, landlord_id FK users, title, city, address, description, rent_eur, charges_eur, type enum[studio,room,flat], status enum[draft,published,closed], availability_date, created_at)`
* **listing_rooms** `(id uuid, listing_id FK, name, capacity int default 1, status enum[open,filled,closed], rent_eur, charges_eur, deposit_eur, min_duration_months, max_duration_months)`
* **listing_requirements** `(listing_id PK/FK, guarantor_required_count int, income_min_multiplier numeric, documents jsonb)`
* **applications** `(id uuid, listing_id FK, room_id FK nullable, tenant_id FK users, status enum[pending,withdrawn,rejected,accepted_pending_payment,confirmed], move_in_date, duration_months, created_at, updated_at)`
* **application_status_history** `(id uuid, application_id FK, old_status, new_status, actor_id FK users nullable, created_at)`
* **guarantors** `(id uuid, tenant_id FK users, first_name, last_name, relation, phone, email, income_eur, nationality, birth_date)`
* **application_guarantors** `(application_id FK, guarantor_id FK, PRIMARY KEY (application_id, guarantor_id))`
* **documents** `(id uuid, owner_type enum[user,application,guarantor,contract], owner_id uuid, kind enum[id_card,proof_of_study,rib,visa,other], filename, mime_type, size_bytes, s3_key, sha256, created_at)`
* **contracts** `(id uuid, application_id FK, document_id FK documents, status enum[draft,sent,signed,void], created_at)`
* **messages_threads** `(id uuid, listing_id FK, tenant_id FK, landlord_id FK, created_at)`
* **messages** `(id uuid, thread_id FK, sender_id FK users, content text, created_at, read_at nullable)`
* **payments** `(id uuid, application_id FK, provider enum[stripe], provider_ref text, amount_eur numeric, currency char(3) default 'EUR', status enum[requires_payment_method,requires_confirmation,processing,succeeded,canceled,failed], created_at, updated_at)`
* **admin_actions** `(id uuid, admin_id FK users, action enum[user_ban,user_unban,listing_takedown], target_type enum[user,listing], target_id uuid, reason text, created_at)`

### 8.2 Indexes & Constraints

* `UNIQUE(users.email)`; partial index for `users(status='active')`
* `applications`: unique constraint `(listing_id, tenant_id)` to prevent duplicates
* Foreign keys with `ON DELETE CASCADE` where appropriate
* Time-based indexes on `messages(thread_id, created_at)`

### 8.3 Retention Rules

* **Application-level documents**: delete **90 days** after application becomes `rejected/withdrawn`; keep for `confirmed` while contract active + **12 months** after.
* **Profile-level documents**: keep until user deletes profile or is deleted; support export.

---

## 9. Module Specs (MVP)

### 9.1 Listings

**Create**

```http
POST /landlord/listings
{
  "title":"Studio 20m²", "city":"Paris", "rent_eur":720,
  "type":"studio", "availability_date":"2025-08-25",
  "requirements": {"guarantor_required_count":1, "documents":["id_card","proof_of_study"]}
}
→ 201 {"id":"...","status":"draft"}
```

**Publish**

```http
POST /landlord/listings/{id}/publish → 200 {"status":"published"}
```

**Auto-close**

```http
POST /landlord/listings/{id}/close → 200 {"status":"closed"}
```

**Search**

```http
GET /listings?city=Paris&price_max=1000&page=1&limit=20
→ 200 {"results":[...], "total":123}
```

### 9.2 Applications

**Create** (only after dossier meets requirements)

```http
POST /tenant/applications
{
  "listing_id":"...", "room_id":"...", "move_in_date":"2025-08-27", "duration_months":6,
  "guarantor_ids":["g1","g2"]
}
→ 201 {"id":"...","status":"pending"}
```

**Withdraw (tenant)**

```http
POST /applications/{id}/withdraw → 200 {"status":"withdrawn"}
```

**Reject (landlord)**

```http
POST /applications/{id}/reject → 200 {"status":"rejected"}
```

**Accept (landlord)**

```http
POST /applications/{id}/accept → 200 {"status":"accepted_pending_payment"}
```

**Confirm (after payment webhook)**

```http
POST /applications/{id}/confirm → 200 {"status":"confirmed"}
```

Validation rules will check listing capacity; if all rooms filled → listing closed.

### 9.3 Documents & Compression

**Presign**

```http
POST /documents/presign {"filename":"file.pdf","content_type":"application/pdf","scope":"application"}
→ 200 {"upload_url":"...","file_id":"..."}
```

**Finalize**

```http
POST /documents/finalize {"file_id":"..."}
→ 202 {"state":"queued_for_compression"}
```

**Compression worker**

* For `jpg/jpeg/png`: resize & re-encode
* For `pdf`: optimize (images downscale)
* For `doc/docx/odt`: attempt downsize by stripping embedded media; if still >10MB, store original and flag `oversized=true`

### 9.4 Messaging

**Start or fetch thread**

```http
POST /messages/threads {"listing_id":"...","participant_id":"<other_user_id>"}
→ 200 {"thread_id":"..."}
```

**Send message**

```http
POST /messages {"thread_id":"...","content":"Bonjour"}
→ 201 {"id":"..."}
```

**Poll**

```http
GET /messages/threads/{id}?since=2025-08-01T12:00:00Z → 200 {"messages":[...]}
```

### 9.5 Payments (Stripe, one-off to Rent_Mark)

**Create Payment Intent** (server → Stripe)

```http
POST /payments/intents {"application_id":"..."}
→ 200 {"client_secret":"...","amount_eur":3400}
```

**Webhook** `/payments/webhook` → updates `payments.status` and transitions application to `confirmed` on `succeeded`.

### 9.6 Admin

**Ban/Unban**

```http
POST /admin/users/{id}/ban → 200 {"status":"banned"}
POST /admin/users/{id}/unban → 200 {"status":"active"}
```

**Takedown listing**

```http
POST /admin/listings/{id}/takedown → 200 {"status":"closed"}
```

All admin actions logged in `admin_actions`.

---

## 10. Frontend Integration Notes

* **Routing**: role-guarded areas (`/tenant/*`, `/landlord/*`, `/admin/*`)
* **State**: API slice per module (auth, listings, apps, messages, payments)
* **Polling**: messages poll every **10s** with `since` cursor
* **i18n**: FR default; currency formatting `EUR`; timezone `Europe/Paris`

---

## 11. Next Steps

* Confirm any tweaks to DB fields or endpoints above.
* I can add **acceptance criteria** per endpoint and **Alembic migration seeds** next. ## 12. DevOps artifacts (skeletons)

### 12.1 `docker-compose.yml` (minimal)

```yaml
version: "3.9"
services:
  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - web_build:/srv/web:ro
    depends_on: [api]
    environment:
      - ACME_AGREE=true
      - CADDY_EMAIL=${CADDY_EMAIL}
  api:
    image: ghcr.io/Rent_Mark/api:latest
    env_file: [.env]
    command: ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","2"]
    expose: ["8000"]
  worker:
    image: ghcr.io/Rent_Mark/api:latest
    env_file: [.env]
    command: ["celery","-A","app.worker.celery_app","worker","-l","INFO"]
    depends_on: [redis]
  redis:
    image: redis:7-alpine
  web:
    image: ghcr.io/Rent_Mark/web:latest
    # build pipeline should place static build into this volume
    volumes:
      - web_build:/usr/share/nginx/html:ro
  pgadmin:
    image: dpage/pgadmin4:8
    env_file: [.env]
    expose: ["80"]
    # In prod, restrict via Security Group IP allowlist
volumes:
  web_build:
```

### 12.2 `Caddyfile`

```caddyfile
Rent_Mark.com {
  encode gzip zstd
  @api path /api/*
  reverse_proxy @api api:8000 {
    header_up X-Forwarded-Proto https
  }
  handle {
    root * /srv/web
    try_files {path} /index.html
    file_server
  }
}

pgadmin.Rent_Mark.com {
  # Optional basic auth in addition to IP allowlist
  # basicauth /* {
  #   admin JDJhJDEwJG...
  # }
  reverse_proxy pgadmin:80
}
```

### 12.3 `.env.example`

```env
REGION=eu-west-1
# DB (async)
DATABASE_URL=postgresql+asyncpg://dbuser:dbpass@rds-host:5432/Rent_Mark
# AWS
AWS_S3_BUCKET=Rent_Mark-storage
SES_REGION=eu-west-1
# Auth/JWT
JWT_AUDIENCE=Rent_Mark
JWT_ISSUER=https://cognito-idp.eu-west-1.amazonaws.com/<userpool-id>
# Stripe
STRIPE_SECRET=sk_live_xxx
# Caddy/pgAdmin
CADDY_EMAIL=ops@Rent_Mark.com
PGADMIN_DEFAULT_EMAIL=admin@Rent_Mark.com
PGADMIN_DEFAULT_PASSWORD=change_me_to_a_long_random_secret
```

### 12.4 Alembic (async) quick start

```bash
alembic init -t async alembic
```

`alembic/env.py` key bits:

```python
from sqlalchemy.ext.asyncio import async_engine_from_config
from logging.config import fileConfig
from alembic import context
from app.db import metadata, Base
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=None,
    )
    async def do_run_migrations(connection):
        await connection.run_sync(target_metadata.create_all)
        await context.run_migrations()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        connection.run_sync(lambda c: None)
run_migrations_online()
```

First migration stub `alembic/versions/0001_init.py`:

```python
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql
revision = "0001_init"
down_revision = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
    op.create_table(
        "users",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("role", sa.Enum("tenant","landlord","admin", name="user_role"), nullable=False),
        sa.Column("status", sa.Enum("active","banned", name="user_status"), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role;")
    op.execute("DROP TYPE IF EXISTS user_status;")
```

---

## 13. Notes on pgAdmin security

* Keep **RDS SG** locked; allow inbound only from EC2.
* Expose **pgadmin.Rent_Mark.com** publicly **only** with:

  * **IP allowlist** (Security Group) and **strong admin password**.
  * Optional **Caddy basic auth** layer.
* Rotate `PGADMIN_DEFAULT_PASSWORD` regularly; disable pgAdmin in compose when not needed.
