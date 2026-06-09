"""
Comprehensive frontend E2E tests using Playwright.

Covers: registration, login, logout, navbar, auth guards,
accounts CRUD, transactions CRUD, budget CRUD, savings goals CRUD,
dashboard, token refresh, non-functional, and edge cases.

Prerequisites:
  pip install pytest-playwright
  playwright install chromium

Usage:
  # Terminal 1: Backend
  cd backend && python manage.py runserver 0.0.0.0:8000

  # Terminal 2: Frontend
  cd frontend && npm run dev

  # Terminal 3: Tests
  cd backend
  pytest finance/tests/test_frontend.py --headed   # headed mode
  pytest finance/tests/test_frontend.py -v         # headless + verbose

  # Auto-start servers (slower startup):
  CI=1 pytest finance/tests/test_frontend.py --headed
"""

import json
import os
import subprocess
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

SESSION_ID = uuid.uuid4().hex[:8]
TEST_USER = {
    "username": f"pwt_{SESSION_ID}",
    "password": "Testpass123!",
    "first_name": "Test",
    "last_name": f"User_{SESSION_ID}",
    "email": f"pwt_{SESSION_ID}@test.com",
}

PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _wait_for_server(url, timeout=45, interval=1.5):
    for _ in range(int(timeout / interval)):
        try:
            urlopen(url, timeout=3)
            return True
        except Exception:
            time.sleep(interval)
    return False


def _api(method, endpoint, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = Request(
        f"{BACKEND_URL}/{endpoint.lstrip('/')}",
        data=body, headers=headers, method=method,
    )
    with urlopen(req) as resp:
        content = resp.read()
        return json.loads(content) if content else None


def _api_get(endpoint, token=None):
    return _api("GET", endpoint, token=token)


def _api_post(endpoint, data, token=None):
    return _api("POST", endpoint, data=data, token=token)


def _api_delete(endpoint, token):
    return _api("DELETE", endpoint, token=token)


# ---------------------------------------------------------------------------
# Auth & data helpers
# ---------------------------------------------------------------------------

CATEGORIES_CACHE = None


def _get_categories():
    global CATEGORIES_CACHE
    if CATEGORIES_CACHE is None:
        CATEGORIES_CACHE = _api_get("api/categories/")
    return CATEGORIES_CACHE


def _cat_id(name):
    cats = _get_categories()
    for c in cats:
        if c["name"] == name:
            return c["id"]
    return None


def _setup_auth(page, test_user):
    page.goto(FRONTEND_URL)
    page.evaluate(
        """(access, refresh, user) => {
            localStorage.setItem("access", access);
            localStorage.setItem("refresh", refresh);
            localStorage.setItem("user", JSON.stringify(user));
        }""",
        test_user["access"], test_user["refresh"], test_user["user"],
    )


def _login_form(page):
    page.goto(f"{FRONTEND_URL}/login")
    page.fill("input[name=username]", TEST_USER["username"])
    page.fill("input[name=password]", TEST_USER["password"])
    page.click("button:has-text('Sign in')")
    page.wait_for_url(f"{FRONTEND_URL}/dashboard")


def _reset_user_data(token):
    for ep in ["transactions", "budgets", "savings-goals", "accounts"]:
        try:
            items = _api_get(f"api/{ep}/", token) or []
            for item in items:
                try:
                    _api_delete(f"api/{ep}/{item['id']}/", token)
                except Exception:
                    pass
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Session fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def servers():
    ci = os.environ.get("CI")
    procs = []
    if ci:
        bdir = os.path.join(PROJECT_ROOT, "backend")
        fdir = os.path.join(PROJECT_ROOT, "frontend")
        p = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"],
            cwd=bdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(p)
        assert _wait_for_server(f"{BACKEND_URL}/api/categories/"), "Django startup failed"
        p = subprocess.Popen(
            ["npx", "next", "dev", "-p", "3000"],
            cwd=fdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(p)
        assert _wait_for_server(FRONTEND_URL), "Next.js startup failed"
        yield
    else:
        assert _wait_for_server(BACKEND_URL, timeout=8), f"Backend {BACKEND_URL} unreachable"
        assert _wait_for_server(FRONTEND_URL, timeout=8), f"Frontend {FRONTEND_URL} unreachable"
        yield
    for p in procs:
        p.terminate()
        p.wait()


@pytest.fixture(scope="session")
def test_user(servers):
    try:
        return _api_post("api/register/", TEST_USER)
    except Exception:
        return _api_post("api/login/", {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"],
        })


@pytest.fixture
def desktop_page(page):
    page.set_viewport_size({"width": 1280, "height": 800})
    return page


@pytest.fixture
def mobile_page(desktop_page):
    desktop_page.set_viewport_size({"width": 375, "height": 667})
    return desktop_page


@pytest.fixture
def auth_page(desktop_page, test_user):
    _setup_auth(desktop_page, test_user)
    return desktop_page


# ============================================================================
# REGISTRATION
# ============================================================================

class TestRegistration:
    REG = {
        "username": f"pwt_reg_{SESSION_ID}",
        "password": "RegPass789!",
        "password2": "RegPass789!",
        "first_name": "Reg",
        "last_name": "Tester",
        "email": f"pwt_reg_{SESSION_ID}@test.com",
    }

    def test_register_new_user(self, page, servers):
        page.goto(FRONTEND_URL)
        page.click("text=Register")
        page.wait_for_url(f"{FRONTEND_URL}/register")
        for f in ["username", "first_name", "last_name", "email", "password", "password2"]:
            page.fill(f"input[name={f}]", self.REG[f])
        page.click("button:has-text('Register')")
        page.wait_for_url(f"{FRONTEND_URL}/dashboard")
        assert page.url == f"{FRONTEND_URL}/dashboard"

    def test_register_password_mismatch(self, page, servers):
        page.goto(f"{FRONTEND_URL}/register")
        page.fill("input[name=username]", "mismatch_test")
        page.fill("input[name=password]", "Pass123!")
        page.fill("input[name=password2]", "Pass456!")
        page.click("button:has-text('Register')")
        err = page.locator("text=password").first
        assert err.is_visible()

    def test_register_duplicate_username(self, page, servers):
        page.goto(f"{FRONTEND_URL}/register")
        for f in ["username", "first_name", "last_name", "password", "password2"]:
            page.fill(f"input[name={f}]", self.REG[f])
        page.fill("input[name=email]", f"dup_{self.REG['email']}")
        page.click("button:has-text('Register')")
        page.wait_for_timeout(500)
        assert page.locator("text=already exists").count() >= 1

    def test_register_empty_fields(self, page, servers):
        page.goto(f"{FRONTEND_URL}/register")
        page.click("button:has-text('Register')")
        page.wait_for_timeout(500)
        assert page.locator("text=required").count() >= 1 or \
               page.locator("text=blank").count() >= 1


# ============================================================================
# LOGIN / LOGOUT
# ============================================================================

class TestLoginLogout:
    def test_login_success(self, page, servers, test_user):
        page.goto(f"{FRONTEND_URL}/login")
        page.fill("input[name=username]", TEST_USER["username"])
        page.fill("input[name=password]", TEST_USER["password"])
        page.click("button:has-text('Sign in')")
        page.wait_for_url(f"{FRONTEND_URL}/dashboard")
        assert page.url == f"{FRONTEND_URL}/dashboard"

    def test_login_invalid_credentials(self, page, servers):
        page.goto(f"{FRONTEND_URL}/login")
        page.fill("input[name=username]", "bad_user")
        page.fill("input[name=password]", "bad_pass")
        page.click("button:has-text('Sign in')")
        page.wait_for_timeout(1000)
        err_texts = ["Unable", "Invalid", "No active", "credentials"]
        assert any(page.locator(f"text={t}").count() >= 1 for t in err_texts)

    def test_login_blank_submit(self, page, servers):
        page.goto(f"{FRONTEND_URL}/login")
        page.click("button:has-text('Sign in')")
        page.wait_for_timeout(500)
        assert page.locator("text=required").count() >= 1 or \
               page.locator("text=blank").count() >= 1

    def test_logout_clears_session(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Logout")
        auth_page.click("button:has-text('Logout')")
        auth_page.wait_for_url(FRONTEND_URL)
        assert auth_page.url.rstrip("/") == FRONTEND_URL
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.url.rstrip("/") == FRONTEND_URL

    def test_logout_cancel_keeps_session(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Logout")
        auth_page.click("button:has-text('Cancel')")
        auth_page.wait_for_timeout(500)
        assert auth_page.url == f"{FRONTEND_URL}/dashboard"

    def test_login_preserves_state_after_refresh(self, page, servers, test_user):
        _login_form(page)
        page.reload()
        page.wait_for_load_state("networkidle")
        assert page.url == f"{FRONTEND_URL}/dashboard"

    def test_login_from_home_link(self, page, servers):
        page.goto(FRONTEND_URL)
        page.click("text=Login")
        page.wait_for_url(f"{FRONTEND_URL}/login")

    def test_register_link_from_home(self, page, servers):
        page.goto(FRONTEND_URL)
        page.click("text=Register")
        page.wait_for_url(f"{FRONTEND_URL}/register")


# ============================================================================
# NAVBAR
# ============================================================================

class TestNavbar:
    def test_navbar_hidden_on_dashboard(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("header.bg-white.shadow").count() == 0

    def test_navbar_hidden_on_login(self, page, servers):
        page.goto(f"{FRONTEND_URL}/login")
        assert page.locator("header.bg-white.shadow").count() == 0

    def test_navbar_hidden_on_register(self, page, servers):
        page.goto(f"{FRONTEND_URL}/register")
        assert page.locator("header.bg-white.shadow").count() == 0

    def test_navbar_hidden_on_root(self, page, servers):
        page.goto(FRONTEND_URL)
        assert page.locator("header.bg-white.shadow").count() == 0

    @pytest.mark.parametrize("path,label", [
        ("transactions", "Transaction"),
        ("accounts", "Accounts"),
        ("budget", "Budget"),
        ("savings-goals", "Savings Goals"),
    ])
    def test_navbar_visible_on_pages(self, auth_page, test_user, path, label):
        auth_page.goto(f"{FRONTEND_URL}/{path}")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("header.bg-white.shadow").count() == 1

    def test_navbar_all_five_links_present(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        for lbl in ["Dashboard", "Transaction", "Budget", "Accounts", "Savings Goals"]:
            assert auth_page.locator(f"header nav a:has-text('{lbl}')").count() >= 1

    @pytest.mark.parametrize("target,expected", [
        ("Dashboard", "dashboard"),
        ("Transaction", "transactions"),
        ("Budget", "budget"),
        ("Accounts", "accounts"),
        ("Savings Goals", "savings-goals"),
    ])
    def test_navbar_each_link_navigates(self, auth_page, test_user, target, expected):
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click(f"header a:has-text('{target}')")
        auth_page.wait_for_url(f"{FRONTEND_URL}/{expected}")

    def test_navbar_active_link_highlighted(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        active = auth_page.locator("header nav a.font-semibold")
        assert active.count() >= 1
        assert "Accounts" in active.text_content()

    def test_navbar_persists_during_spa_navigation(self, auth_page, test_user):
        pages = ["accounts", "budget", "savings-goals", "transactions", "accounts"]
        for p in pages:
            auth_page.goto(f"{FRONTEND_URL}/{p}")
            auth_page.wait_for_load_state("networkidle")
            assert auth_page.locator("header.bg-white.shadow").count() == 1

    def test_navbar_mobile_hamburger_toggles_panel(self, mobile_page, servers, test_user):
        _setup_auth(mobile_page, test_user)
        mobile_page.goto(f"{FRONTEND_URL}/accounts")
        mobile_page.wait_for_load_state("networkidle")
        btn = mobile_page.locator("button[aria-label='Toggle menu']")
        assert btn.is_visible()
        btn.click()
        mobile_page.wait_for_timeout(300)
        panel = mobile_page.locator("header >> div.border-t")
        assert panel.is_visible()
        panel.locator("a:has-text('Budget')").click()
        mobile_page.wait_for_url(f"{FRONTEND_URL}/budget")

    def test_navbar_mobile_hamburger_closes_on_link_click(self, mobile_page, servers, test_user):
        _setup_auth(mobile_page, test_user)
        mobile_page.goto(f"{FRONTEND_URL}/accounts")
        mobile_page.wait_for_load_state("networkidle")
        mobile_page.locator("button[aria-label='Toggle menu']").click()
        mobile_page.wait_for_timeout(200)
        mobile_page.locator("header >> div.border-t a:has-text('Transaction')").click()
        mobile_page.wait_for_url(f"{FRONTEND_URL}/transactions")

    def test_navbar_logo_links_home(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("header a:has-text('Finance Tracker')")
        auth_page.wait_for_url(FRONTEND_URL)

    def test_navbar_title_renders(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("header:has-text('Finance Tracker')").count() >= 1


# ============================================================================
# AUTH GUARDS
# ============================================================================

class TestAuthGuards:
    @pytest.mark.parametrize("path", [
        "accounts", "transactions", "budget",
        "savings-goals", "dashboard", "profile",
    ])
    def test_all_protected_pages_redirect(self, page, servers, path):
        page.goto(f"{FRONTEND_URL}/{path}")
        page.wait_for_load_state("networkidle")
        assert page.url.rstrip("/") == FRONTEND_URL

    @pytest.mark.parametrize("path", ["login", "register"])
    def test_public_pages_accessible(self, page, servers, path):
        page.goto(f"{FRONTEND_URL}/{path}")
        page.wait_for_load_state("networkidle")
        assert path in page.url

    def test_expired_token_triggers_redirect(self, page, servers, test_user):
        page.goto(FRONTEND_URL)
        page.evaluate("localStorage.setItem('access', 'invalid-token')")
        page.goto(f"{FRONTEND_URL}/accounts")
        page.wait_for_load_state("networkidle")
        assert page.url.rstrip("/") == FRONTEND_URL


# ============================================================================
# ACCOUNTS CRUD
# ============================================================================

class TestAccountsCRUD:
    def test_empty_state(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=No accounts yet").count() >= 1

    def test_create_account(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Add account']")
        auth_page.fill("input[placeholder*='Chase']", "Main Checking")
        auth_page.fill("input[placeholder='0.00']", "1000")
        auth_page.select_option("select", "checking")
        auth_page.click("button:has-text('Save')")
        assert auth_page.locator("text=Main Checking").wait_for(timeout=5000)
        assert auth_page.locator("text=$1,000.00").count() >= 1 or \
               auth_page.locator("text=1000.00").count() >= 1

    def test_create_account_all_types(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        for atype in ["checking", "savings", "credit", "cash", "investment"]:
            acct = _api_post("api/accounts/", {
                "name": f"Type-{atype}", "balance": "100", "account_type": atype,
            }, token)
            assert acct["account_type"] == atype

    def test_create_account_with_notes(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Add account']")
        auth_page.fill("input[placeholder*='Chase']", "Noted Account")
        auth_page.fill("input[placeholder='0.00']", "250")
        auth_page.select_option("select", "savings")
        auth_page.fill("textarea", "My private notes")
        auth_page.click("button:has-text('Save')")
        assert auth_page.locator("text=Noted Account").wait_for(timeout=5000)
        assert auth_page.locator("text=My private notes").count() >= 1

    def test_create_account_zero_balance(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Add account']")
        auth_page.fill("input[placeholder*='Chase']", "Zero Account")
        auth_page.fill("input[placeholder='0.00']", "0")
        auth_page.select_option("select", "cash")
        auth_page.click("button:has-text('Save')")
        assert auth_page.locator("text=Zero Account").wait_for(timeout=5000)

    def test_edit_account(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/accounts/", {"name": "Edit Me", "balance": "500", "account_type": "checking"}, token)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Edit Edit Me']")
        auth_page.fill("input[placeholder*='Chase']", "Edited Name")
        auth_page.fill("input[placeholder='0.00']", "999")
        auth_page.click("button:has-text('Save')")
        assert auth_page.locator("text=Edited Name").wait_for(timeout=5000)
        assert auth_page.locator("text=$999.00").count() >= 1 or \
               auth_page.locator("text=999.00").count() >= 1

    def test_edit_account_balance_negative(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        acct = _api_post("api/accounts/", {"name": "Neg Test", "balance": "100", "account_type": "credit"}, token)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click(f"button[aria-label='Edit Neg Test']")
        auth_page.fill("input[placeholder='0.00']", "-50")
        auth_page.click("button:has-text('Save')")
        assert auth_page.locator("text=-$50.00").count() >= 1 or \
               auth_page.locator("text=-50.00").count() >= 1

    def test_delete_account(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/accounts/", {"name": "Delete Me", "balance": "50", "account_type": "checking"}, token)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Delete Delete Me']")
        auth_page.locator("text=Delete account?").wait_for(timeout=3000)
        auth_page.click("button:has-text('Delete Account')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=Delete Me").count() == 0

    def test_delete_account_cancel(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/accounts/", {"name": "Keep Me", "balance": "75", "account_type": "checking"}, token)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Delete Keep Me']")
        auth_page.locator("text=Delete account?").wait_for(timeout=3000)
        auth_page.click("button:has-text('Cancel')")
        auth_page.wait_for_timeout(500)
        assert auth_page.locator("text=Keep Me").count() >= 1

    def test_summary_cards(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/accounts/", {"name": "A", "balance": "200", "account_type": "checking"}, token)
        _api_post("api/accounts/", {"name": "B", "balance": "300", "account_type": "savings"}, token)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Total Accounts").is_visible()
        assert auth_page.locator("text=Total Balance").is_visible()

    def test_refresh_button(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("button:has-text('Refresh')").is_visible()

    def test_create_empty_name_disabled(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Add account']")
        save_btn = auth_page.locator("button:has-text('Save')")
        assert save_btn.is_disabled()

    def test_accounts_initial_create_button(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        first_btn = auth_page.locator("button:has-text('Add Your First Account')")
        assert first_btn.is_visible()


# ============================================================================
# TRANSACTIONS CRUD
# ============================================================================

class TestTransactionsCRUD:
    def _seed(self, token):
        _reset_user_data(token)
        acct = _api_post("api/accounts/", {
            "name": "TX Base", "balance": "5000", "account_type": "checking",
        }, token)
        return acct

    def test_empty_state(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=No transactions").count() >= 1

    def test_create_income(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button:has-text('+')")
        auth_page.click("text=Income")
        auth_page.select_option("select[name=account]", str(acct["id"]))
        auth_page.wait_for_timeout(300)
        auth_page.select_option("select[name=category]", str(_cat_id("Salary")))
        auth_page.fill("input[name=date]", "2026-06-01")
        auth_page.fill("input[name=amount]", "5000")
        auth_page.fill("input[name=description]", "Monthly salary")
        auth_page.click("button:has-text('Save')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=INCOME").count() >= 1

    def test_create_expense(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button:has-text('+')")
        auth_page.select_option("select[name=account]", str(acct["id"]))
        auth_page.wait_for_timeout(300)
        auth_page.select_option("select[name=category]", str(_cat_id("Groceries")))
        auth_page.fill("input[name=date]", "2026-06-02")
        auth_page.fill("input[name=amount]", "75.50")
        auth_page.fill("input[name=description]", "Groceries")
        auth_page.click("button:has-text('Save')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=EXPENSE").count() >= 1

    def test_edit_transaction(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Salary"),
            "amount": "100", "transaction_type": "income", "date": "2026-06-03",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=100")
        auth_page.wait_for_timeout(300)
        auth_page.click("button:has-text('Edit')")
        auth_page.wait_for_timeout(300)
        auth_page.fill("input[name=amount]", "250")
        auth_page.click("button:has-text('Save')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=250").count() >= 1

    def test_delete_transaction(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Salary"),
            "amount": "999", "transaction_type": "income", "date": "2026-06-04",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=999")
        auth_page.wait_for_timeout(300)
        auth_page.click("button:has-text('Delete')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=999").count() == 0

    def test_filter_by_account(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Salary"),
            "amount": "300", "transaction_type": "income", "date": "2026-06-05",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        select = auth_page.locator("select").first
        select.select_option(str(acct["id"]))
        auth_page.wait_for_timeout(500)
        assert auth_page.locator("text=300").count() >= 1

    def test_filter_by_type_income(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Salary"),
            "amount": "400", "transaction_type": "income", "date": "2026-06-06",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        selects = auth_page.locator("select")
        selects.nth(1).select_option("income")
        auth_page.wait_for_timeout(500)
        assert auth_page.locator("text=INCOME").count() >= 1

    def test_filter_clear(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Salary"),
            "amount": "500", "transaction_type": "income", "date": "2026-06-07",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.locator("select").first.select_option(str(acct["id"]))
        auth_page.wait_for_timeout(300)
        auth_page.click("button:has-text('Clear')")
        auth_page.wait_for_timeout(500)
        assert auth_page.locator("text=500").count() >= 1

    def test_pagination(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        for i in range(6):
            _api_post("api/transactions/", {
                "account_id": acct["id"], "category_id": _cat_id("Salary"),
                "amount": str((i + 1) * 10), "transaction_type": "income",
                "date": f"2026-06-{i+10:02d}",
            }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Page 1").count() >= 1
        auth_page.click("button:has-text('Next')")
        assert auth_page.locator("text=Page 2").count() >= 1
        auth_page.click("button:has-text('Prev')")
        assert auth_page.locator("text=Page 1").count() >= 1

    def test_expand_details(self, auth_page, test_user):
        token = test_user["access"]
        acct = self._seed(token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Salary"),
            "amount": "777", "transaction_type": "income",
            "date": "2026-06-15", "description": "Hidden detail",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=777")
        auth_page.wait_for_timeout(300)
        assert auth_page.locator("text=Hidden detail").count() >= 1


# ============================================================================
# BUDGET CRUD
# ============================================================================

class TestBudgetCRUD:
    def test_budget_create(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Add budget']")
        auth_page.wait_for_timeout(300)
        auth_page.select_option("select", str(_cat_id("Groceries")))
        auth_page.fill("input[type=number]", "500")
        auth_page.click("button:has-text('Save')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=Groceries").count() >= 1
        assert auth_page.locator("text=$500.00").count() >= 1

    def test_budget_edit(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/budgets/", {
            "category_id": _cat_id("Eating Out"), "allocated_amount": "300",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button:has-text('Edit')")
        auth_page.wait_for_timeout(300)
        auth_page.fill("input[type=number]", "600")
        auth_page.click("button:has-text('Save')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=$600.00").count() >= 1

    def test_budget_delete(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/budgets/", {
            "category_id": _cat_id("Utilities"), "allocated_amount": "200",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button:has-text('Delete')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=Utilities").count() == 0

    def test_summary_cards(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/budgets/", {
            "category_id": _cat_id("Groceries"), "allocated_amount": "400",
        }, token)
        _api_post("api/budgets/", {
            "category_id": _cat_id("Eating Out"), "allocated_amount": "200",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        for label in ["Total Budgeted", "Total Spent", "Remaining", "Average Usage"]:
            assert auth_page.locator(f"text={label}").count() >= 1
        assert auth_page.locator("text=$600.00").count() >= 1

    def test_circular_progress_renders(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/budgets/", {
            "category_id": _cat_id("Groceries"), "allocated_amount": "500",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("svg").count() >= 1
        assert auth_page.locator("text=Spent 0%").count() >= 1

    def test_spending_alert_high_percentage(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        acct = _api_post("api/accounts/", {
            "name": "Budget Alert Acct", "balance": "5000", "account_type": "checking",
        }, token)
        cat_id = _cat_id("Groceries")
        _api_post("api/budgets/", {"category_id": cat_id, "allocated_amount": "100"}, token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": cat_id,
            "amount": "95", "transaction_type": "expense", "date": "2026-06-10",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Spent 95%").count() >= 1

    def test_pagination(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        cat_names = ["Rent / Mortgage", "Utilities", "Groceries",
                     "Eating Out", "Transportation", "Fuel", "Insurance"]
        for name in cat_names:
            cid = _cat_id(name)
            if cid:
                _api_post("api/budgets/", {"category_id": cid, "allocated_amount": "100"}, token)
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Page 1").count() >= 1

    def test_create_no_category_alert(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/budget")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button[aria-label='Add budget']")
        auth_page.wait_for_timeout(300)
        auth_page.fill("input[type=number]", "100")
        auth_page.click("button:has-text('Save')")
        assert auth_page.locator("text=Select a category").count() >= 1


# ============================================================================
# SAVINGS GOALS CRUD
# ============================================================================

class TestSavingsGoalsCRUD:
    def test_empty_state(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=No savings goals yet").count() >= 1

    def test_create_goal(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button:has-text('Add Goal')")
        auth_page.wait_for_timeout(300)
        inputs = auth_page.locator("input")
        inputs.nth(0).fill("New Car Fund")
        inputs.nth(1).fill("25000")
        inputs.nth(2).fill("Saving for a new car down payment")
        auth_page.click("button:has-text('Create')")
        assert auth_page.locator("text=New Car Fund").wait_for(timeout=5000)
        assert auth_page.locator("text=$0.00").count() >= 1

    def test_edit_goal(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/savings-goals/", {
            "name": "Old Name", "target_amount": "5000", "description": "Old",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Old Name")
        auth_page.wait_for_timeout(300)
        auth_page.click("button:has-text('Edit Goal')")
        auth_page.wait_for_timeout(300)
        inputs = auth_page.locator("input")
        inputs.nth(0).fill("New Name")
        inputs.nth(1).fill("10000")
        auth_page.click("button:has-text('Save')")
        assert auth_page.locator("text=New Name").wait_for(timeout=5000)

    def test_delete_goal(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/savings-goals/", {
            "name": "Delete Goal", "target_amount": "1000", "description": "Del",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Delete Goal")
        auth_page.wait_for_timeout(300)
        auth_page.once("dialog", lambda d: d.accept())
        auth_page.click("button:has-text('Delete Goal')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=Delete Goal").count() == 0

    def test_goal_card_click_opens_modal(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/savings-goals/", {
            "name": "Modal Test", "target_amount": "3000", "description": "Check modal",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Modal Test")
        auth_page.wait_for_timeout(300)
        assert auth_page.locator("text=Edit Goal").is_visible()

    def test_add_saving(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/savings-goals/", {
            "name": "Add Saving Goal", "target_amount": "5000", "description": "Add",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Add Saving Goal")
        auth_page.wait_for_timeout(300)
        auth_page.click("button:has-text('Add Saving')")
        auth_page.wait_for_timeout(300)
        auth_page.locator("input[type=number]").first.fill("250")
        auth_page.click("button:has-text('Add')")
        auth_page.wait_for_timeout(1000)
        assert auth_page.locator("text=$250.00").count() >= 1 or \
               auth_page.locator("text=250").count() >= 1

    def test_add_saving_multiple(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        goal = _api_post("api/savings-goals/", {
            "name": "Multi Add", "target_amount": "10000", "description": "Multi",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Multi Add")
        auth_page.wait_for_timeout(300)
        for amt in ["100", "200", "300"]:
            auth_page.click("button:has-text('Add Saving')")
            auth_page.wait_for_timeout(200)
            auth_page.locator("input[type=number]").first.fill(amt)
            auth_page.click("button:has-text('Add')")
            auth_page.wait_for_timeout(500)
        final = _api_get(f"api/savings-goals/{goal['id']}/", token)
        assert float(final["current_amount"]) == 600.0

    def test_progress_bar_renders(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/savings-goals/", {
            "name": "Progress", "target_amount": "1000", "description": "Bar",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/savings-goals")
        auth_page.wait_for_load_state("networkidle")
        bars = auth_page.locator("div.w-full.bg-gray-200")
        assert bars.count() >= 1


# ============================================================================
# DASHBOARD
# ============================================================================

class TestDashboard:
    def _seed(self, token):
        _reset_user_data(token)
        acct = _api_post("api/accounts/", {
            "name": "Dash Base", "balance": "5000", "account_type": "checking",
        }, token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Salary"),
            "amount": "3000", "transaction_type": "income", "date": "2026-06-01",
        }, token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": _cat_id("Groceries"),
            "amount": "200", "transaction_type": "expense", "date": "2026-06-02",
        }, token)
        _api_post("api/budgets/", {
            "category_id": _cat_id("Groceries"), "allocated_amount": "500",
        }, token)
        _api_post("api/savings-goals/", {
            "name": "Vacation", "target_amount": "5000", "description": "Trip",
        }, token)
        return acct

    def test_stat_cards_displayed(self, auth_page, test_user):
        token = test_user["access"]
        self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        for lbl in ["Total Balance", "Total Income", "Total Expenses", "Remaining Budget"]:
            assert auth_page.locator(f"text={lbl}").count() >= 1

    def test_stat_card_navigates_to_accounts(self, auth_page, test_user):
        token = test_user["access"]
        self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Total Balance")
        auth_page.wait_for_url(f"{FRONTEND_URL}/accounts")

    def test_stat_card_navigates_to_transactions(self, auth_page, test_user):
        token = test_user["access"]
        self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Total Income")
        auth_page.wait_for_url(f"{FRONTEND_URL}/transactions")

    def test_recent_transactions_section(self, auth_page, test_user):
        token = test_user["access"]
        self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Recent transactions").count() >= 1

    def test_view_all_navigates(self, auth_page, test_user):
        token = test_user["access"]
        self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button:has-text('View All')")
        auth_page.wait_for_url(f"{FRONTEND_URL}/transactions")

    def test_savings_progress_section(self, auth_page, test_user):
        token = test_user["access"]
        self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Savings Progress").count() >= 1

    def test_budget_alert_appears(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        acct = _api_post("api/accounts/", {
            "name": "Alert Test", "balance": "5000", "account_type": "checking",
        }, token)
        cat_id = _cat_id("Groceries")
        _api_post("api/budgets/", {"category_id": cat_id, "allocated_amount": "100"}, token)
        _api_post("api/transactions/", {
            "account_id": acct["id"], "category_id": cat_id,
            "amount": "95", "transaction_type": "expense", "date": "2026-06-10",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Alert").count() >= 1

    def test_charts_render(self, auth_page, test_user):
        token = test_user["access"]
        self._seed(token)
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Income vs Expense").count() >= 1
        assert auth_page.locator("text=Expense distribution").count() >= 1

    def test_sidebar_navigates_to_all_pages(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        targets = {
            "Transactions": "transactions",
            "Budgets": "budget",
            "Savings Goals": "savings-goals",
            "Accounts": "accounts",
        }
        for label, path in targets.items():
            auth_page.click(f"text={label}")
            auth_page.wait_for_url(f"{FRONTEND_URL}/{path}")
            auth_page.go_back()
            auth_page.wait_for_load_state("networkidle")

    def test_sidebar_profile_link(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Profile")
        auth_page.wait_for_url(f"{FRONTEND_URL}/profile")

    def test_sidebar_logout_modal_cancel(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Logout")
        assert auth_page.locator("text=Confirm logout").is_visible()
        auth_page.click("button:has-text('Cancel')")
        auth_page.wait_for_timeout(500)
        assert auth_page.locator("text=Confirm logout").count() == 0

    def test_sidebar_logout_confirmed(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("text=Logout")
        auth_page.click("button:has-text('Logout')")
        auth_page.wait_for_url(FRONTEND_URL)
        assert auth_page.url.rstrip("/") == FRONTEND_URL

    def test_dashboard_user_greeting(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        greeting = auth_page.locator("text=Hello")
        assert greeting.count() >= 1

    def test_dashboard_empty_state_no_data(self, auth_page, test_user):
        _reset_user_data(test_user["access"])
        auth_page.goto(f"{FRONTEND_URL}/dashboard")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=No recent transactions").count() >= 1


# ============================================================================
# TOKEN REFRESH
# ============================================================================

class TestTokenRefresh:
    def test_refresh_valid(self, servers, test_user):
        resp = _api_post("api/token/refresh/", {"refresh": test_user["refresh"]})
        assert "access" in resp
        assert len(resp["access"]) > 0

    def test_refresh_invalid(self, servers):
        with pytest.raises(HTTPError):
            _api_post("api/token/refresh/", {"refresh": "invalid_token"})

    def test_refresh_empty(self, servers):
        with pytest.raises(HTTPError):
            _api_post("api/token/refresh/", {})


# ============================================================================
# NON-FUNCTIONAL / EDGE CASES
# ============================================================================

class TestNonFunctional:
    def test_error_state_network_failure(self, auth_page, test_user):
        def fail(route):
            route.abort("connectionrefused")
        auth_page.route("**/api/accounts/**", fail)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=Failed to load accounts").count() >= 1

    def test_navbar_accounts_regression(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("header a:has-text('Savings')")
        auth_page.wait_for_url(f"{FRONTEND_URL}/savings-goals")

    def test_navbar_clickable_on_all_visible_pages(self, auth_page, test_user):
        for path in ["transactions", "accounts", "budget", "savings-goals"]:
            auth_page.goto(f"{FRONTEND_URL}/{path}")
            auth_page.wait_for_load_state("networkidle")
            auth_page.click("header a:has-text('Accounts')")
            auth_page.wait_for_url(f"{FRONTEND_URL}/accounts")
            assert auth_page.url == f"{FRONTEND_URL}/accounts"

    def test_mobile_fab_visible(self, mobile_page, servers, test_user):
        _setup_auth(mobile_page, test_user)
        mobile_page.goto(f"{FRONTEND_URL}/accounts")
        mobile_page.wait_for_load_state("networkidle")
        fab = mobile_page.locator("button[aria-label='Add account']")
        assert fab.is_visible()

    def test_mobile_budget_fab_visible(self, mobile_page, servers, test_user):
        _setup_auth(mobile_page, test_user)
        mobile_page.goto(f"{FRONTEND_URL}/budget")
        mobile_page.wait_for_load_state("networkidle")
        fab = mobile_page.locator("button[aria-label='Add budget']")
        assert fab.is_visible()

    def test_page_title(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert "Finance" in auth_page.title()

    def test_browser_back_button(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        auth_page.go_back()
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.url == f"{FRONTEND_URL}/transactions"

    def test_profile_page_accessible(self, auth_page, test_user):
        auth_page.goto(f"{FRONTEND_URL}/profile")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.url == f"{FRONTEND_URL}/profile"

    def test_large_number_display(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        _api_post("api/accounts/", {
            "name": "Large Balance", "balance": "9999999.99", "account_type": "checking",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=9999999.99").count() >= 1 or \
               auth_page.locator("text=9,999,999.99").count() >= 1

    def test_transaction_affects_account_balance(self, auth_page, test_user):
        token = test_user["access"]
        _reset_user_data(token)
        acct = _api_post("api/accounts/", {
            "name": "Bal Test", "balance": "1000", "account_type": "checking",
        }, token)
        auth_page.goto(f"{FRONTEND_URL}/transactions")
        auth_page.wait_for_load_state("networkidle")
        auth_page.click("button:has-text('+')")
        auth_page.select_option("select[name=account]", str(acct["id"]))
        auth_page.wait_for_timeout(300)
        auth_page.select_option("select[name=category]", str(_cat_id("Groceries")))
        auth_page.fill("input[name=date]", "2026-06-20")
        auth_page.fill("input[name=amount]", "300")
        auth_page.fill("input[name=description]", "Balance effect test")
        auth_page.click("button:has-text('Save')")
        auth_page.wait_for_timeout(1000)
        auth_page.goto(f"{FRONTEND_URL}/accounts")
        auth_page.wait_for_load_state("networkidle")
        assert auth_page.locator("text=$700.00").count() >= 1 or \
               auth_page.locator("text=700.00").count() >= 1

    def test_parallel_tab_isolation(self, context, servers, test_user):
        tab1 = context.new_page()
        _setup_auth(tab1, test_user)
        tab1.goto(f"{FRONTEND_URL}/dashboard")
        tab1.wait_for_load_state("networkidle")
        assert "/dashboard" in tab1.url
        tab1.close()
        tab2 = context.new_page()
        tab2.goto(f"{FRONTEND_URL}/accounts")
        tab2.wait_for_load_state("networkidle")
        assert tab2.url.rstrip("/") == FRONTEND_URL
        tab2.close()


# ============================================================================
# MIGRATION & SYSTEM
# ============================================================================

class TestSystem:
    def test_categories_seeded(self, servers):
        cats = _api_get("api/categories/")
        assert len(cats) >= 30
        names = [c["name"] for c in cats]
        assert "Salary" in names
        assert "Groceries" in names
        assert "Rent / Mortgage" in names

    def test_cors_headers_present(self, servers):
        req = Request(f"{BACKEND_URL}/api/categories/")
        with urlopen(req) as resp:
            origin = resp.headers.get("Access-Control-Allow-Origin")
            assert origin == "*" or origin is not None

    def test_backend_health(self, servers):
        req = Request(f"{BACKEND_URL}/api/categories/")
        with urlopen(req) as resp:
            assert resp.status == 200
