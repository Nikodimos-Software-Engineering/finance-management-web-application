
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
        transaction = serializer.save(user=self.request.user)
        
        # Update account balance when creating a new transaction
        account = transaction.account
        if transaction.transaction_type == 'expense':
            account.balance -= transaction.amount
        elif transaction.transaction_type == 'income':
            account.balance += transaction.amount
        account.save()

    def perform_update(self, serializer):
        # Get the original transaction before updating
        original_transaction = self.get_object()
        original_amount = original_transaction.amount
        original_type = original_transaction.transaction_type
        original_account = original_transaction.account
        
        # Update the transaction
        updated_transaction = serializer.save()
        new_amount = updated_transaction.amount
        new_type = updated_transaction.transaction_type
        new_account = updated_transaction.account
        
        # Calculate the adjustment
        adjustment = Decimal('0')
        
        # Case 1: Same account, same type
        if original_account == new_account and original_type == new_type:
            if original_type == 'expense':
                # Expense amount changed: original was subtracted, now subtract new
                # So we need to add back original and subtract new
                adjustment = original_amount - new_amount
            else:  # income
                # Income amount changed: original was added, now add new
                # So we need to subtract original and add new
                adjustment = new_amount - original_amount
        
        # Case 2: Same account, different type
        elif original_account == new_account and original_type != new_type:
            # Revert original transaction and apply new one
            if original_type == 'expense':
                # Add back the original expense, then apply new income
                adjustment = original_amount + new_amount
            else:  # original was income
                # Subtract original income, then apply new expense
                adjustment = -original_amount - new_amount
        
        # Case 3: Different accounts
        else:
            # Revert from original account
            if original_type == 'expense':
                original_account.balance += original_amount
            else:
                original_account.balance -= original_amount
            original_account.save()
            
            # Apply to new account
            if new_type == 'expense':
                new_account.balance -= new_amount
            else:
                new_account.balance += new_amount
            new_account.save()
            return
        
        # Apply adjustment for same account cases
        if adjustment != Decimal('0'):
            new_account.balance += adjustment
            new_account.save()

    def perform_destroy(self, instance):
        # Revert the transaction from account balance before deleting
        account = instance.account
        if instance.transaction_type == 'expense':
            account.balance += instance.amount  # Add back the expense
        else:  # income
            account.balance -= instance.amount  # Subtract the income
        account.save()
        instance.delete()


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
