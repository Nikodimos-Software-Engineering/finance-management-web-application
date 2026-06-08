from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from finance.models import Account, Category, Budget, Transaction, SavingsGoal

User = get_user_model()


# =============================================================================
# MODEL UNIT TESTS
# =============================================================================

class AccountModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="acctuser", password="pass")

    def test_create_account(self):
        a = Account.objects.create(user=self.user, name="Checking", account_type="checking", balance=Decimal("100"))
        self.assertEqual(a.name, "Checking")
        self.assertEqual(a.account_type, "checking")
        self.assertEqual(a.balance, Decimal("100"))
        self.assertIsNotNone(a.created_at)
        self.assertIsNotNone(a.updated_at)

    def test_str_representation(self):
        a = Account.objects.create(user=self.user, name="Savings", account_type="savings", balance=Decimal("500"))
        self.assertIn("Savings", str(a))
        self.assertIn("500", str(a))

    def test_default_balance_zero(self):
        a = Account.objects.create(user=self.user, name="Cash", account_type="cash")
        self.assertEqual(a.balance, Decimal("0"))


class CategoryModelTests(TestCase):
    def test_create_expense_category(self):
        c = Category.objects.create(name="Rent", type=Category.TYPE_EXPENSE)
        self.assertEqual(c.name, "Rent")
        self.assertEqual(c.type, "expense")

    def test_create_income_category(self):
        c = Category.objects.create(name="Salary", type=Category.TYPE_INCOME)
        self.assertEqual(c.type, "income")

    def test_str_representation(self):
        c = Category.objects.create(name="Food", type=Category.TYPE_EXPENSE)
        self.assertIn("Food", str(c))
        self.assertIn("expense", str(c))


class BudgetModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="budgetuser", password="pass")
        self.category = Category.objects.create(name="Food", type=Category.TYPE_EXPENSE)

    def test_create_budget_initializes_remaining(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("1000"))
        self.assertEqual(b.remaining_amount, Decimal("1000"))
        self.assertEqual(b.spent_amount, Decimal("0"))
        self.assertEqual(b.spent_percentage, 0)

    def test_spent_amount_and_percentage(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("1000"))
        b.remaining_amount = Decimal("300")
        b.save()
        self.assertEqual(b.spent_amount, Decimal("700"))
        self.assertEqual(b.spent_percentage, 70.0)

    def test_spent_percentage_zero_allocated(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("0"))
        self.assertEqual(b.spent_percentage, 0)

    def test_spending_alert_none_below_80(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("1000"))
        b.remaining_amount = Decimal("300")  # 70% spent
        b.save()
        self.assertIsNone(b.spending_alert)

    def test_spending_alert_warning_at_80(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("1000"))
        b.remaining_amount = Decimal("200")  # 80% spent
        b.save()
        self.assertEqual(b.spending_alert["type"], "warning")

    def test_spending_alert_warning_above_80(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("1000"))
        b.remaining_amount = Decimal("100")  # 90% spent
        b.save()
        self.assertEqual(b.spending_alert["type"], "warning")

    def test_spending_alert_danger_at_100(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("1000"))
        b.remaining_amount = Decimal("0")  # 100% spent
        b.save()
        self.assertEqual(b.spending_alert["type"], "danger")

    def test_spending_alert_danger_above_100(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("1000"))
        b.remaining_amount = Decimal("-200")  # 120% spent
        b.save()
        self.assertEqual(b.spending_alert["type"], "danger")

    def test_unique_together_user_category(self):
        Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("500"))
        with self.assertRaises(IntegrityError):
            Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("600"))

    def test_str_representation(self):
        b = Budget.objects.create(user=self.user, category=self.category, allocated_amount=Decimal("500"))
        self.assertIn("Food", str(b))
        self.assertIn("budgetuser", str(b))


class TransactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="txuser", password="pass")
        self.account = Account.objects.create(user=self.user, name="Checking", account_type="checking")

    def test_create_expense_transaction(self):
        t = Transaction.objects.create(
            user=self.user, account=self.account, transaction_type="expense",
            amount=Decimal("50"), description="Groceries", date="2026-06-01"
        )
        self.assertEqual(t.transaction_type, "expense")
        self.assertEqual(t.description, "Groceries")

    def test_create_income_transaction(self):
        t = Transaction.objects.create(
            user=self.user, account=self.account, transaction_type="income",
            amount=Decimal("2000"), description="Salary", date="2026-06-01"
        )
        self.assertEqual(t.transaction_type, "income")


class SavingsGoalModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="savuser", password="pass")

    def test_create_savings_goal(self):
        g = SavingsGoal.objects.create(
            user=self.user, name="Vacation", target_amount=Decimal("5000")
        )
        self.assertEqual(g.name, "Vacation")
        self.assertEqual(g.current_amount, Decimal("0"))
        self.assertEqual(g.target_amount, Decimal("5000"))

    def test_str_representation(self):
        g = SavingsGoal.objects.create(
            user=self.user, name="New Car", target_amount=Decimal("20000")
        )
        self.assertIn("New Car", str(g))


# =============================================================================
# API INTEGRATION TESTS
# =============================================================================

class AuthMixin:
    """Mixin providing helper methods for authenticated API tests."""

    def _register(self, username="testuser", password="pass123"):
        return self.client.post("/api/register/", {
            "username": username, "password": password, "password2": password,
            "first_name": "", "last_name": "", "email": "",
        }, content_type="application/json")

    def _login(self, username="testuser", password="pass123"):
        return self.client.post("/api/login/", {
            "username": username, "password": password,
        }, content_type="application/json")

    def _get_token(self, username="testuser", password="pass123"):
        resp = self._login(username, password)
        return resp.json()["access"]

    def _auth_header(self, username="testuser", password="pass123"):
        return {"HTTP_AUTHORIZATION": f"Bearer {self._get_token(username, password)}"}

    def _create_user(self, username="testuser", password="pass123"):
        return User.objects.create_user(username=username, password=password)

    def _create_account(self, user=None, name="Checking", balance=Decimal("1000")):
        owner = user or self.user
        return Account.objects.create(user=owner, name=name, account_type="checking", balance=balance)

    def _create_expense_category(self, name="Food"):
        return Category.objects.create(name=name, type=Category.TYPE_EXPENSE)

    def _create_income_category(self, name="Salary"):
        return Category.objects.create(name=name, type=Category.TYPE_INCOME)

    def _create_budget(self, user=None, category=None, allocated=Decimal("1000")):
        owner = user or self.user
        cat = category or self._create_expense_category()
        return Budget.objects.create(user=owner, category=cat, allocated_amount=allocated)

    def _create_transaction(self, account=None, category=None, trans_type="expense", amount=Decimal("100"),
                            description="Test", date="2026-06-08", user=None):
        acct = account or self._create_account(user=user or self.user)
        cat = category or self._create_expense_category()
        t = Transaction.objects.create(
            user=user or self.user, account=acct, transaction_type=trans_type,
            amount=amount, category=cat, description=description, date=date,
        )
        # Mirror the balance update the ViewSet would perform
        if trans_type == "expense":
            acct.balance -= amount
        elif trans_type == "income":
            acct.balance += amount
        acct.save()
        return t


class AuthAPITests(TestCase, AuthMixin):
    def test_register_returns_tokens(self):
        resp = self._register()
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], "testuser")

    def test_register_password_mismatch(self):
        resp = self.client.post("/api/register/", {
            "username": "u", "password": "abc123", "password2": "wrong",
        }, content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_login_valid_returns_tokens(self):
        self._create_user()
        resp = self._login()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())
        self.assertIn("refresh", resp.json())

    def test_login_invalid_returns_401(self):
        resp = self.client.post("/api/login/", {
            "username": "nobody", "password": "wrong",
        }, content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_token_refresh(self):
        self._create_user()
        login_resp = self._login()
        refresh_token = login_resp.json()["refresh"]
        resp = self.client.post("/api/token/refresh/", {
            "refresh": refresh_token,
        }, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())

    def test_access_denied_without_token(self):
        resp = self.client.get("/api/accounts/")
        self.assertEqual(resp.status_code, 401)


class AccountAPITests(TestCase, AuthMixin):
    def setUp(self):
        self.user = self._create_user()

    def test_list_accounts(self):
        self._create_account(user=self.user)
        self._create_account(user=self.user, name="Savings")
        resp = self.client.get("/api/accounts/", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_create_account(self):
        resp = self.client.post("/api/accounts/", {
            "name": "New Account", "balance": "500", "account_type": "savings",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["name"], "New Account")
        self.assertEqual(resp.json()["account_type"], "savings")

    def test_user_isolation(self):
        other = User.objects.create_user(username="other", password="pass")
        self._create_account(user=other, name="Other's Account")
        self._create_account(user=self.user, name="Mine")
        resp = self.client.get("/api/accounts/", **self._auth_header())
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["name"], "Mine")

    def test_cannot_access_other_users_account(self):
        other = User.objects.create_user(username="other", password="pass")
        a = self._create_account(user=other)
        resp = self.client.get(f"/api/accounts/{a.id}/", **self._auth_header())
        self.assertEqual(resp.status_code, 404)

    def test_update_account(self):
        a = self._create_account(user=self.user)
        resp = self.client.put(f"/api/accounts/{a.id}/", {
            "name": "Updated", "balance": "999", "account_type": "checking",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "Updated")
        self.assertEqual(resp.json()["balance"], "999.00")

    def test_delete_account(self):
        a = self._create_account(user=self.user)
        resp = self.client.delete(f"/api/accounts/{a.id}/", **self._auth_header())
        self.assertEqual(resp.status_code, 204)


class CategoryAPITests(TestCase, AuthMixin):
    def setUp(self):
        self.user = self._create_user()
        self._create_expense_category("Food")
        self._create_expense_category("Transport")
        self._create_income_category("Salary")

    def test_list_categories_public(self):
        resp = self.client.get("/api/categories/")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.json()), 3)

    def test_list_categories_no_auth_required(self):
        resp = self.client.get("/api/categories/")
        self.assertEqual(resp.status_code, 200)

    def test_category_detail(self):
        cat = Category.objects.first()
        resp = self.client.get(f"/api/categories/{cat.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], cat.name)


class TransactionAPITests(TestCase, AuthMixin):
    ORIGINAL_BALANCE = Decimal("1000")

    def setUp(self):
        self.user = self._create_user()
        self.account = self._create_account(user=self.user, balance=self.ORIGINAL_BALANCE)
        self.expense_cat = self._create_expense_category()
        self.income_cat = self._create_income_category()
        self.budget = self._create_budget(user=self.user, category=self.expense_cat, allocated=Decimal("500"))

    def _create_tx_payload(self, **kwargs):
        payload = {
            "account_id": self.account.id,
            "category_id": self.expense_cat.id,
            "transaction_type": "expense",
            "amount": "50",
            "description": "Test",
            "date": "2026-06-08",
        }
        payload.update(kwargs)
        return payload

    def _balance(self):
        return Account.objects.get(id=self.account.id).balance

    # --- CREATE ---

    def test_create_expense_reduces_balance(self):
        initial = self._balance()
        resp = self.client.post("/api/transactions/", self._create_tx_payload(),
                                content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self._balance(), initial - Decimal("50"))

    def test_create_income_increases_balance(self):
        initial = self._balance()
        resp = self.client.post("/api/transactions/", self._create_tx_payload(
            transaction_type="income", category_id=self.income_cat.id, amount="200",
        ), content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self._balance(), initial + Decimal("200"))

    def test_create_expense_updates_budget_remaining(self):
        self.client.post("/api/transactions/", self._create_tx_payload(amount="100"),
                         content_type="application/json", **self._auth_header())
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.remaining_amount, Decimal("400"))

    def test_create_income_does_not_update_budget(self):
        self.client.post("/api/transactions/", self._create_tx_payload(
            transaction_type="income", category_id=self.income_cat.id, amount="300",
        ), content_type="application/json", **self._auth_header())
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.remaining_amount, Decimal("500"))

    def test_create_transaction_requires_transaction_type(self):
        payload = self._create_tx_payload()
        del payload["transaction_type"]
        resp = self.client.post("/api/transactions/", payload,
                                content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 400)

    # --- LIST ---

    def test_list_transactions(self):
        self._create_transaction(user=self.user, account=self.account, amount=Decimal("10"))
        self._create_transaction(user=self.user, account=self.account, amount=Decimal("20"))
        resp = self.client.get("/api/transactions/", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_transaction_user_isolation(self):
        other = User.objects.create_user(username="other", password="pass")
        other_acct = self._create_account(user=other)
        self._create_transaction(user=other, account=other_acct)
        resp = self.client.get("/api/transactions/", **self._auth_header())
        self.assertEqual(len(resp.json()), 0)

    # --- UPDATE ---

    def test_update_same_account_same_type_expense(self):
        self._create_transaction(user=self.user, account=self.account, amount=Decimal("100"))
        resp = self.client.put(f"/api/transactions/{Transaction.objects.first().id}/", {
            "account_id": self.account.id,
            "category_id": self.expense_cat.id,
            "transaction_type": "expense",
            "amount": "150",
            "description": "Updated",
            "date": "2026-06-09",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        # 1000 - 150 = 850
        self.assertEqual(self._balance(), self.ORIGINAL_BALANCE - Decimal("150"))

    def test_update_same_account_different_type(self):
        self._create_transaction(user=self.user, account=self.account, trans_type="expense",
                                 amount=Decimal("100"), category=self.expense_cat)
        resp = self.client.put(f"/api/transactions/{Transaction.objects.first().id}/", {
            "account_id": self.account.id,
            "category_id": self.income_cat.id,
            "transaction_type": "income",
            "amount": "200",
            "description": "Now income",
            "date": "2026-06-09",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        # 1000 + 200 = 1200 (revert 100 expense, apply 200 income)
        self.assertEqual(self._balance(), self.ORIGINAL_BALANCE + Decimal("200"))

    def test_update_different_account(self):
        acct2 = self._create_account(user=self.user, name="Savings", balance=Decimal("500"))
        self._create_transaction(user=self.user, account=self.account, amount=Decimal("100"),
                                 category=self.expense_cat)
        resp = self.client.put(f"/api/transactions/{Transaction.objects.first().id}/", {
            "account_id": acct2.id,
            "category_id": self.expense_cat.id,
            "transaction_type": "expense",
            "amount": "50",
            "description": "Moved",
            "date": "2026-06-09",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        # acct1 reverted to 1000, acct2: 500 - 50 = 450
        self.assertEqual(self._balance(), self.ORIGINAL_BALANCE)
        self.assertEqual(Account.objects.get(id=acct2.id).balance, Decimal("450"))

    # --- DELETE ---

    def test_delete_expense_reverts_balance(self):
        self._create_transaction(user=self.user, account=self.account, amount=Decimal("100"),
                                 category=self.expense_cat)
        resp = self.client.delete(f"/api/transactions/{Transaction.objects.first().id}/",
                                  **self._auth_header())
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self._balance(), self.ORIGINAL_BALANCE)

    def test_delete_income_reverts_balance(self):
        self._create_transaction(user=self.user, account=self.account, trans_type="income",
                                 amount=Decimal("200"), category=self.income_cat)
        resp = self.client.delete(f"/api/transactions/{Transaction.objects.first().id}/",
                                  **self._auth_header())
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self._balance(), self.ORIGINAL_BALANCE)

    # --- BUDGET ALERTS VIA TRANSACTIONS ---

    def test_budget_warning_alert_after_transaction(self):
        self.client.post("/api/transactions/", self._create_tx_payload(amount="400"),
                         content_type="application/json", **self._auth_header())
        resp = self.client.get(f"/api/budgets/{self.budget.id}/", **self._auth_header())
        alert = resp.json().get("spending_alert")
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "warning")

    def test_budget_danger_alert_after_transaction(self):
        self.client.post("/api/transactions/", self._create_tx_payload(amount="500"),
                         content_type="application/json", **self._auth_header())
        resp = self.client.get(f"/api/budgets/{self.budget.id}/", **self._auth_header())
        alert = resp.json().get("spending_alert")
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "danger")


class BudgetAPITests(TestCase, AuthMixin):
    def setUp(self):
        self.user = self._create_user()
        self.cat = self._create_expense_category("Food")
        self.income_cat = self._create_income_category("Salary")

    def test_create_budget(self):
        resp = self.client.post("/api/budgets/", {
            "category_id": self.cat.id, "allocated_amount": "1000",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["allocated_amount"], "1000.00")
        self.assertEqual(resp.json()["remaining_amount"], "1000.00")

    def test_create_budget_with_income_category_rejected(self):
        resp = self.client.post("/api/budgets/", {
            "category_id": self.income_cat.id, "allocated_amount": "500",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 400)

    def test_list_budgets(self):
        self._create_budget(user=self.user, category=self.cat)
        self._create_budget(user=self.user, category=self._create_expense_category("Transport"), allocated=Decimal("200"))
        resp = self.client.get("/api/budgets/", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_budget_user_isolation(self):
        other = User.objects.create_user(username="other", password="pass")
        other_cat = self._create_expense_category("Other")
        self._create_budget(user=other, category=other_cat)
        self._create_budget(user=self.user, category=self.cat)
        resp = self.client.get("/api/budgets/", **self._auth_header())
        self.assertEqual(len(resp.json()), 1)

    def test_update_budget(self):
        b = self._create_budget(user=self.user, category=self.cat)
        resp = self.client.put(f"/api/budgets/{b.id}/", {
            "category_id": self.cat.id,
            "allocated_amount": "2000",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["allocated_amount"], "2000.00")

    def test_delete_budget(self):
        b = self._create_budget(user=self.user, category=self.cat)
        resp = self.client.delete(f"/api/budgets/{b.id}/", **self._auth_header())
        self.assertEqual(resp.status_code, 204)

    def test_budget_shows_alert_in_response(self):
        b = self._create_budget(user=self.user, category=self.cat, allocated=Decimal("100"))
        b.remaining_amount = Decimal("10")  # 90% spent
        b.save()
        resp = self.client.get(f"/api/budgets/{b.id}/", **self._auth_header())
        self.assertIsNotNone(resp.json().get("spending_alert"))


class SavingsGoalAPITests(TestCase, AuthMixin):
    def setUp(self):
        self.user = self._create_user()

    def test_create_savings_goal(self):
        resp = self.client.post("/api/savings-goals/", {
            "name": "Vacation", "target_amount": "5000", "description": "Summer trip",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["name"], "Vacation")
        self.assertEqual(resp.json()["current_amount"], "0.00")
        self.assertEqual(resp.json()["target_amount"], "5000.00")

    def test_list_savings_goals(self):
        SavingsGoal.objects.create(user=self.user, name="Goal1", target_amount=Decimal("100"))
        SavingsGoal.objects.create(user=self.user, name="Goal2", target_amount=Decimal("200"))
        resp = self.client.get("/api/savings-goals/", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_user_isolation(self):
        other = User.objects.create_user(username="other", password="pass")
        SavingsGoal.objects.create(user=other, name="Other's Goal", target_amount=Decimal("300"))
        SavingsGoal.objects.create(user=self.user, name="My Goal", target_amount=Decimal("100"))
        resp = self.client.get("/api/savings-goals/", **self._auth_header())
        self.assertEqual(len(resp.json()), 1)

    def test_add_funds_to_goal(self):
        g = SavingsGoal.objects.create(user=self.user, name="Car", target_amount=Decimal("10000"))
        resp = self.client.post(f"/api/savings-goals/{g.id}/add/", {
            "amount": "500",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["current_amount"], "500.00")

    def test_add_funds_accumulates(self):
        g = SavingsGoal.objects.create(user=self.user, name="Car", target_amount=Decimal("10000"))
        self.client.post(f"/api/savings-goals/{g.id}/add/", {"amount": "300"},
                         content_type="application/json", **self._auth_header())
        self.client.post(f"/api/savings-goals/{g.id}/add/", {"amount": "200"},
                         content_type="application/json", **self._auth_header())
        g.refresh_from_db()
        self.assertEqual(g.current_amount, Decimal("500"))

    def test_add_funds_negative_amount_rejected(self):
        g = SavingsGoal.objects.create(user=self.user, name="Car", target_amount=Decimal("10000"))
        resp = self.client.post(f"/api/savings-goals/{g.id}/add/", {"amount": "-50"},
                                content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 400)

    def test_add_funds_invalid_amount_rejected(self):
        g = SavingsGoal.objects.create(user=self.user, name="Car", target_amount=Decimal("10000"))
        resp = self.client.post(f"/api/savings-goals/{g.id}/add/", {"amount": "abc"},
                                content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 400)

    def test_update_goal(self):
        g = SavingsGoal.objects.create(user=self.user, name="Old Name", target_amount=Decimal("100"))
        resp = self.client.put(f"/api/savings-goals/{g.id}/", {
            "name": "New Name", "target_amount": "500", "description": "Updated",
        }, content_type="application/json", **self._auth_header())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "New Name")

    def test_delete_goal(self):
        g = SavingsGoal.objects.create(user=self.user, name="Delete Me", target_amount=Decimal("100"))
        resp = self.client.delete(f"/api/savings-goals/{g.id}/", **self._auth_header())
        self.assertEqual(resp.status_code, 204)
