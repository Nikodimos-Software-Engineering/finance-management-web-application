
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets, permissions
from rest_framework import exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Account, Category, Budget, Transaction, SavingsGoal
from decimal import Decimal, InvalidOperation
from .serializers import (
	RegistrationSerializer,
	LoginSerializer,
	AccountSerializer,
	CategorySerializer,
	BudgetSerializer,
	TransactionSerializer,
    SavingsGoalSerializer,
)

from .serializers import RegistrationSerializer, LoginSerializer


User = get_user_model()


class RegisterView(APIView):

	permission_classes = [AllowAny]

	def post(self, request):
		serializer = RegistrationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()

		refresh = RefreshToken.for_user(user)
		return Response(
			{
				"user": RegistrationSerializer(user).data,
				"refresh": str(refresh),
				"access": str(refresh.access_token),
			},
			status=status.HTTP_201_CREATED,
		)


class LoginView(APIView):

	permission_classes = [AllowAny]

	def post(self, request):
		serializer = LoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data["user"]

		refresh = RefreshToken.for_user(user)
		return Response(
			{
				"user": RegistrationSerializer(user).data,
				"refresh": str(refresh),
				"access": str(refresh.access_token),
			},
			status=status.HTTP_200_OK,
		)


class AccountViewSet(viewsets.ModelViewSet):
	serializer_class = AccountSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Account.objects.filter(user=self.request.user)

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer
	permission_classes = [permissions.AllowAny]


class BudgetViewSet(viewsets.ModelViewSet):
	serializer_class = BudgetSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Budget.objects.filter(user=self.request.user)

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
	serializer_class = TransactionSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Transaction.objects.filter(user=self.request.user).order_by("-date", "-created_at")

	def perform_create(self, serializer):
		
		budget = serializer.validated_data.get("budget") if hasattr(serializer, "validated_data") else None
		if budget is not None and budget.user != self.request.user:
			raise exceptions.ValidationError({"budget": "Invalid budget"})
		serializer.save(user=self.request.user)

	def perform_update(self, serializer):
		budget = serializer.validated_data.get("budget") if hasattr(serializer, "validated_data") else None
		if budget is not None and budget.user != self.request.user:
			raise exceptions.ValidationError({"budget": "Invalid budget"})
		serializer.save()


class SavingsGoalViewSet(viewsets.ModelViewSet):
	
	serializer_class = SavingsGoalSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return SavingsGoal.objects.filter(user=self.request.user).order_by("-created_at")

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

	@action(detail=True, methods=["post"])
	def add(self, request, pk=None):
		
		goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
		amount = request.data.get("amount")
		
		try:
			amount = Decimal(str(amount))
		except (InvalidOperation, TypeError, ValueError):
			return Response({"detail": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

		if amount <= Decimal("0"):
			return Response({"detail": "Amount must be positive"}, status=status.HTTP_400_BAD_REQUEST)

		goal.current_amount = (goal.current_amount or Decimal("0")) + amount
		goal.save()
		return Response(SavingsGoalSerializer(goal).data, status=status.HTTP_200_OK)
