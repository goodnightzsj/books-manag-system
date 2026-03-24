# Authentication & Security Architecture

## 1. Identity

- **What it is:** Stateless JWT Bearer-token authentication with a small admin/user RBAC layer.
- **Purpose:** Authenticate users, issue short-lived access tokens, and gate privileged routes through a shared dependency.

## 2. Core Components

- `backend/app/core/config.py:17-25` -- Security and bootstrap settings: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `ADMIN_*`.
- `backend/app/core/security.py:7-32` -- Password hashing, password verification, JWT encode, and JWT decode.
- `backend/app/api/deps.py:8-40` -- `HTTPBearer`, `get_current_user`, and `require_admin`.
- `backend/app/api/auth.py:10-61` -- `/auth/register`, `/auth/login`, and `/auth/me`.
- `backend/app/models/user.py:10-30` -- `UserRole` enum and `User` ORM model.
- `backend/app/schemas/user.py:7-32` -- `UserCreate`, `UserLogin`, `User`, `Token`, and `TokenData`.
- `backend/app/db/base.py:12-17` -- Request-scoped session provider.

## 3. Execution Flow

### 3.1 Registration Flow

- **1. Request:** `POST /api/v1/auth/register` enters `backend/app/api/auth.py:12-40`.
- **2. Uniqueness checks:** Username and email are checked sequentially at `backend/app/api/auth.py:14-26`.
- **3. Password hashing:** `get_password_hash` from `backend/app/core/security.py:12-13` stores a bcrypt hash.
- **4. Persist user:** `backend/app/api/auth.py:29-38` inserts the user and returns the response model.

### 3.2 Login Flow

- **1. Request:** `POST /api/v1/auth/login` enters `backend/app/api/auth.py:42-57`.
- **2. Lookup:** User is loaded by `username` at `backend/app/api/auth.py:44`.
- **3. Verify password:** `verify_password` from `backend/app/core/security.py:9-10` validates the bcrypt hash.
- **4. Update audit field:** `last_login` is written at `backend/app/api/auth.py:52-54`.
- **5. Issue token:** `create_access_token` from `backend/app/core/security.py:15-24` signs a JWT with `sub=<user.id>`.

### 3.3 Authenticated Request Flow

- **1. Extract header:** `HTTPBearer()` parses `Authorization: Bearer <token>` at `backend/app/api/deps.py:8`.
- **2. Decode JWT:** `decode_access_token` at `backend/app/core/security.py:26-32` verifies signature and reads `sub`.
- **3. Resolve user:** `backend/app/api/deps.py:24-31` loads the `User` row by UUID.
- **4. Inject ORM object:** The route receives `current_user: User`.

### 3.4 Admin-Gated Request Flow

- **1. Reuse auth chain:** `require_admin` depends on `get_current_user` at `backend/app/api/deps.py:34`.
- **2. Compare role:** `backend/app/api/deps.py:35-39` requires `current_user.role == UserRole.ADMIN`.
- **3. Enforce 403:** Non-admin callers receive `HTTP 403`.
- **4. Current coverage:** Books write routes use it at `backend/app/api/books.py:60-64`, category mutation routes at `backend/app/api/categories.py:41-45`, `:61-65`, `:111-116`, `:139-144`, and all scanner routes at `backend/app/api/scanner.py:42-46`, `:64-68`, `:103-107`, `:190-194`.

## 4. Design Notes

- **Stateless access tokens:** There is no token revocation, refresh-token flow, or server-side session store.
- **Two-role RBAC only:** The current model supports `admin` and `user`; there is no finer-grained permission system.
- **Password policy is schema-level only:** `UserCreate.password` enforces `min_length=6` at `backend/app/schemas/user.py:12-13`; there is no DB-level password policy.
- **Bootstrap path is env-driven:** Initial admin creation relies on `ADMIN_PASSWORD` through `backend/entrypoint.sh:57-73` or `backend/scripts/create_admin.py:21-37`.
- **Missing auth endpoints:** There is still no logout or refresh endpoint in `backend/app/api/auth.py:10-61`.
