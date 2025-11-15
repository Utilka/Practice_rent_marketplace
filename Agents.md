Here is a clean, compact agents.md styled document capturing the philosophy, architecture rules, and constraints you’ve been describing — written as if it were for GitHub Copilot/Codex or any code-generation LLM working inside your project.

---

# agents.md

Project Development Philosophy & Coding Standards

This document describes the architectural principles, design constraints, and coding philosophy that AI coding assistants must follow when generating or modifying code for this project.

---

## 🔥 Core Architectural Philosophy

### 1. Domain-Driven Folder Structure

* Code is grouped by domain, not by technical layer.
* Example domains: auth/, advertisements/, users/.
* Each domain contains:

  * router.py
  * service.py
  * repository.py
  * errors.py (domain-specific exceptions)
  * Other supporting domain files

### 2. Clear Layering: Router → Service → Repository

* Routers

  * Handle HTTP specifics (status codes, auth dependencies, responses declaration)
  * Should NOT contain real business logic
  * Call services only

* Services

  * Contain business rules
  * Raise domain errors, NEVER HTTP exceptions
  * Must be pure Python: no FastAPI imports

* Repositories

  * Handle persistence and database access
  * No business logic
  * May raise repo-specific errors or generic persistence exceptions

---

## 🧩 Error Handling Philosophy

### 1. Services raise domain errors

* Example:

  * auth.errors.NotAuthenticated
  * advertisements.errors.AdNotFound
  * advertisements.errors.AdIsLocked
* These are *not* HTTP errors.

### 2. Routers define responses explicitly

* Each route should declare responses via dictionary unpacking:

@router.put(
    "/ads/{ad_id}",
    responses={
        **advertisement_common_errors,
        **auth_errors,
        400: {"model": ErrorResponse, "description": "Cannot edit locked advertisement"},
    },
)
* This acts as local documentation for what the route can raise.

### 3. A global exception handler translates domain errors → HTTP

* Only one global handler is used.
* It maps known domain errors to proper HTTP codes and returns ErrorResponse.

### 4. Consistent error response model

{
  "error_code": "AD_LOCKED",
  "message": "This advertisement can no longer be edited",
  "request_id": "uuid",
  "user_id": "123"
}
Every error in the app uses this structure.

---

## 🔒 Authentication Philosophy

### Auth is done through dependencies, not middleware

* Middleware authentication is avoided because it breaks:

  * login/signup routes
  * predictable control flow
  * route granularity

### Auth dependency:

def get_current_user(...):
    set_user_id(user.id)
    return user
Middleware sets request_id; auth dependency sets user_id.

---

## 🪵 Logging Philosophy

### 1. JSON logging only

* All logs must be structured JSON.
* No plain text logs.

### 2. Logging context = request_id + user_id

* request_id set in middleware
* user_id set in authentication dependency
* These values are stored via contextvars

### 3. Logger injection

* Use a module-level logger:

logger = logging.getLogger(__name__)
* Do not import inside functions.

### 4. Logging from anywhere

* Services and repositories must be able to log without knowing about FastAPI.

### 5. Error handling middleware logs full traceback for 500 errors

* Full traceback is logged on server side (JSON)
* User still gets generic 500 response

---

## ⚙️ Middleware Philosophy

### Only middleware strictly necessary:

* Request ID assignment
* Request timing / structured access logs
* Optional: global error handling (wraps uncaught exceptions)

### Middleware must never do:

* Authentication
* Rate limiting (best left to dependencies or external tools)
* Domain-based logic

---

## 🧱 Simplicity & Maintainability Rules

### 1. No excessive magic helpers
* Avoid “clever” functions that hide simple dict building or error registration.
* Prefer explicit code.

### 2. Everything must be predictable

* If a developer opens a router file, they should immediately know:

  * which services it calls,
  * which errors it can return,
  * what the workflow is.

### 3. No hiding behavior in decorators or metaclasses

* Keep the code stupid simple.

### 4. Minimize global state

* Only allow:

  * request logger context
  * dependency injection states

### 5. Services must be deterministic and pure

* No reading global variables
* No side-effects except logging

---

## 📐 FastAPI Usage Standards

### **1. All public endpoints must declare FastAPI responses= explicitly.**

2. All validation is done by Pydantic, not in services.s.**

3. Annotated dependencies > plain Depends for clarity.y.**

4. Avoid overusing middleware for logic.c.**

---

## 📦 Testing Philosophy

Unit tests for:r:**

* services (pure business logic)
* repositories (DB behavior)

Integration tests for:r:**

* routers
* error handling
* logging output
* authentication flow

End-to-end tests for:r:**

* critical user flows

---

## 🎯 Summary — Essence of This ProjectSimple | Explicit | Domain-Driven | Predictable | FastAPI-powered | Production-readydy**

* Business logic in services
* HTTP concerns in routers
* Persistence in repositories
* Domain-specific exceptions
* One global exception handler
* Route-level explicit error declarations
* Context-based JSON logging
* request_id and user_id everywhere automatically
* No magic, no clever abstractions

---

If you want, I can also generate:

✅ A CONTRIBUTING.md
✅ A logging.md (full logging spec)
✅ A reusable cookiecutter-style project template
✅ A full example project skeleton following these rules

Just tell me which one you want next.