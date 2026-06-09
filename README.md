# Finance Management Web Application

A full-stack personal finance tracker with budget management, transaction tracking, savings goals, and account management. Built with Django REST Framework and Next.js 13 App Router.

**176 tests** — 65 backend integration + 111 frontend E2E.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5.2, Django REST Framework, SimpleJWT |
| **Frontend** | Next.js 13.5 (App Router), React 18, Tailwind CSS, Recharts |
| **Database** | PostgreSQL (production), SQLite (development/testing) |
| **Auth** | JWT access/refresh tokens (Bearer scheme) |
| **Testing** | Django TestCase (backend), Playwright + pytest (frontend) |

---

## Project Structure

```
backend/
├── finance/
│   ├── migrations/          # DB migrations (incl. seed categories)
│   ├── tests/
│   │   ├── test_all.py      # 65 backend integration tests
│   │   └── test_frontend.py # 111 frontend E2E tests (Playwright)
│   ├── models.py            # Account, Category, Budget, Transaction, SavingsGoal
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # API views with atomic balance/budget updates
│   └── urls.py              # API route definitions
├── main/
│   ├── settings.py          # Django configuration
│   ├── middleware.py        # APITrailingSlashMiddleware
│   └── urls.py              # Root URL config
├── manage.py
└── requirements.txt

frontend/
├── src/
│   ├── app/
│   │   ├── layout.js        # Root layout (Navbar + main wrapper)
│   │   ├── page.js          # Landing page
│   │   ├── login/page.js    # Login form
│   │   ├── register/page.js # Registration form
│   │   ├── dashboard/page.js # Dashboard with charts & stats
│   │   ├── accounts/page.js  # Account management (CRUD)
│   │   ├── transactions/page.js # Transaction management (CRUD + filters)
│   │   ├── budget/page.js     # Budget management (CRUD + progress rings)
│   │   ├── savings-goals/page.js # Savings goals (CRUD + add funds)
│   │   └── profile/page.js    # User profile
│   ├── components/
│   │   └── Navbar.js         # Top navigation bar
│   └── utils/
│       └── api.js            # API client (fetch wrapper + auth headers)
├── package.json
└── next.config.mjs

test-report.md                # Comprehensive test report for portfolio
```

---

## Features

### Frontend
- **Dashboard** — Total balance, income/expense summary, budget alerts, recent transactions, savings progress, income-vs-expense line chart, expense distribution pie chart
- **Transactions** — Create income/expense, edit, delete, filter by account/type/date range, pagination, expandable detail rows
- **Accounts** — Create/edit/delete, supports 5 types (checking, savings, credit, cash, investment), summary cards, pull-to-refresh on mobile, optional local notes
- **Budget** — Create/edit/delete per category, summary cards (Total Budgeted, Spent, Remaining, Avg Usage), SVG circular progress rings, spending alerts (warning ≥80%, danger ≥100%), pagination
- **Savings Goals** — Create/edit/delete, add savings incrementally, circular + horizontal progress bars
- **Auth** — Register, login, JWT token refresh, auth guards on all protected pages, logout with confirmation
- **Navigation** — Top navbar (desktop + mobile hamburger), dashboard sidebar with navigation buttons

### Backend API
- `POST /api/register/` — User registration
- `POST /api/login/` — Login (returns JWT tokens)
- `POST /api/token/refresh/` — Refresh access token
- `CRUD /api/accounts/` — Account management
- `GET /api/categories/` — Read-only category list (30+ seeded categories)
- `CRUD /api/transactions/` — Transactions with atomic balance updates
- `CRUD /api/budgets/` — Budgets with auto-calculated spent/remaining
- `CRUD /api/savings-goals/` — Savings goals + `POST /<id>/add/` endpoint

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (optional — SQLite works out of the box)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables (or use defaults)
export SECRET_KEY="your-secret-key"
export DEBUG=True

# Run migrations and seed default categories
python manage.py migrate

# Start server
python manage.py runserver 0.0.0.0:8000
```

### Frontend Setup
```bash
cd frontend
npm install

# Create .env.local with your backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000), register an account, and start tracking finances.

---

## Running Tests

### Backend Tests (65 integration tests)
```bash
cd backend
python manage.py test finance.tests.test_all
# or
pytest finance/tests/test_all.py -v
```

### Frontend Tests (111 E2E tests)
```bash
pip install pytest-playwright
playwright install chromium

# In separate terminals:
# Terminal 1: cd backend && python manage.py runserver 0.0.0.0:8000
# Terminal 2: cd frontend && npm run dev

# Terminal 3:
cd backend
pytest finance/tests/test_frontend.py --headed   # Watch in browser
pytest finance/tests/test_frontend.py -v         # Headless
```

### All Tests
```bash
cd backend
pytest finance/tests/test_all.py finance/tests/test_frontend.py -v
```

---

## Test Coverage Summary

| Area | Tests | Scope |
|---|---|---|
| **Models** | 20 | Account, Category, Budget (incl. spending alerts), Transaction, SavingsGoal |
| **Auth API** | 6 | Register, login, refresh, duplicate user, invalid creds, unauthenticated access |
| **Account API** | 6 | CRUD, user isolation, balance updates |
| **Category API** | 3 | List (read-only), public access |
| **Transaction API** | 14 | CRUD, atomic balance, budget deduction, user isolation, filters, type changes, deletions, null category |
| **Budget API** | 7 | CRUD, spent calculations, atomic updates, user isolation |
| **Savings Goal API** | 9 | CRUD, add/ endpoint, negative/zero validation, user isolation |
| **Registration** | 4 | Full flow, password mismatch, duplicate user, empty fields |
| **Login / Logout** | 8 | Success, invalid, blank, logout clears session, cancel keeps session, state persists, nav links |
| **Navbar** | 20 | Hidden/visible states, all 5 links, active highlight, mobile toggle, SPA persistence |
| **Auth Guards** | 9 | 6 protected pages redirect, 2 public pages accessible, expired token |
| **Accounts CRUD** | 13 | Empty state, create (all types + notes + zero), edit, delete, cancel, summary, refresh, validation |
| **Transactions CRUD** | 10 | Empty, create income/expense, edit, delete, filter (account + type), clear, pagination, expand |
| **Budget CRUD** | 8 | Create, edit, delete, summary cards, circular progress, spending alert, pagination, validation |
| **Savings Goals CRUD** | 8 | Empty, create, edit, delete, modal, add saving, multi-add, progress bar |
| **Dashboard** | 14 | Stat cards, navigation, transactions, savings, budget alert, charts, sidebar, profile, logout, greeting, empty state |
| **Token Refresh** | 3 | Valid, invalid, empty |
| **Non-Functional** | 11 | Network error, z-index regression, mobile, page title, back button, large numbers, balance cascade, tab isolation |
| **System** | 3 | Seed categories, CORS, health check |

**Total: 176 tests across 23 test classes.**

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | (required) | Django secret key |
| `DEBUG` | `False` | Django debug mode |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database connection string |
| `NEXT_PUBLIC_API_URL` | (required) | Backend URL for frontend API calls |
| `BACKEND_URL` | `http://localhost:8000` | Used by frontend tests |
| `FRONTEND_URL` | `http://localhost:3000` | Used by frontend tests |

---

## API Endpoints

All API endpoints are prefixed with `/api/`. Auth endpoints use `AllowAny`; all others require `Authorization: Bearer <access_token>`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register/` | Register new user |
| `POST` | `/api/login/` | Log in |
| `POST` | `/api/token/refresh/` | Refresh access token |
| `GET/POST` | `/api/accounts/` | List / Create account |
| `GET/PUT/DELETE` | `/api/accounts/<id>/` | Retrieve / Update / Delete account |
| `GET` | `/api/categories/` | List categories (public) |
| `GET/POST` | `/api/transactions/` | List / Create transaction |
| `GET/PUT/DELETE` | `/api/transactions/<id>/` | Retrieve / Update / Delete transaction |
| `GET/POST` | `/api/budgets/` | List / Create budget |
| `GET/PUT/DELETE` | `/api/budgets/<id>/` | Retrieve / Update / Delete budget |
| `GET/POST` | `/api/savings-goals/` | List / Create savings goal |
| `GET/PUT/DELETE` | `/api/savings-goals/<id>/` | Retrieve / Update / Delete savings goal |
| `POST` | `/api/savings-goals/<id>/add/` | Add funds to savings goal |

---

## Deployment

### Backend (Render / Railway / Fly.io)
```bash
cd backend
pip install -r requirements.txt
gunicorn main.wsgi
```
Set `SECRET_KEY`, `DEBUG=False`, and `DATABASE_URL` to your PostgreSQL connection string.

### Frontend (Vercel)
```bash
cd frontend
npm run build
```
Set `NEXT_PUBLIC_API_URL` to your deployed backend URL. See `next.config.mjs` for custom configuration.

---

## Git History

```
1388d2a test: 111 comprehensive frontend E2E tests with Playwright
02f795d fix: accounts page pull-to-refresh overlay blocking navbar clicks
4a7b7c5 fix: critical bugs, add budget tracking/alerting, comprehensive tests, frontend fixes
9cfbb5f Add APITrailingSlashMiddleware
987690f Remove trailing slashes from login/register URL patterns
cbd79ed Remove trailing_slash from action decorator
cbc3e68 Fix trailing slash issue causing 500 on PUT requests
1e6139c Add migration for account_type, transaction_type, updated_at
... and 30+ earlier commits
```

---

## Bugs Caught by Tests

1. **`transaction_type` missing from serializer** — Field wasn't exposed in API output
2. **`budget_id` field leaked in serializer** — Stale field caused 500 errors
3. **Non-atomic balance updates** — Balance and transaction not wrapped in `transaction.atomic()`
4. **Pull-to-refresh overlay blocked Navbar** — `z-40` div intercepted all Navbar clicks
5. **`/profile` route 404** — Navbar link existed but no page was created
6. **Null category crash** — `tx.category?.type` threw on null category
7. **Budget `remaining_amount` uninitialized** — Null instead of zero for new budgets
