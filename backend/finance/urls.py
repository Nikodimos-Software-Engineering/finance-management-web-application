
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, AccountViewSet, CategoryViewSet, BudgetViewSet, TransactionViewSet, SavingsGoalViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"budgets", BudgetViewSet, basename="budget")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"savings-goals", SavingsGoalViewSet, basename="savingsgoal")

urlpatterns = [
	path("register/", RegisterView.as_view(), name="register"),
	path("login/", LoginView.as_view(), name="login"),
	path("", include(router.urls)),
]
