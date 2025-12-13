
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from .models import Account, Category, Budget, Transaction, SavingsGoal


User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):

	password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
	password2 = serializers.CharField(write_only=True, required=True, label="Confirm password", style={"input_type": "password"})

	class Meta:
		model = User
		fields = ("id", "username", "first_name", "last_name", "email", "password", "password2")
		extra_kwargs = {"password": {"write_only": True}}

	def validate(self, data):
		if data.get("password") != data.get("password2"):
			raise serializers.ValidationError({"password": "Password fields didn't match."})
		return data

	def create(self, validated_data):
		validated_data.pop("password2", None)
		password = validated_data.pop("password")
		try:
			user = User.objects.create_user(password=password, **validated_data)
		except TypeError:
			user = User(**validated_data)
			user.set_password(password)
			user.save()
		return user


class LoginSerializer(serializers.Serializer):

	username = serializers.CharField(required=True)
	password = serializers.CharField(required=True, write_only=True, style={"input_type": "password"})

	def validate(self, data):
		username = data.get("username")
		password = data.get("password")

		if username and password:
			user = authenticate(username=username, password=password)
			if not user:
				raise serializers.ValidationError("Unable to log in with provided credentials.")
		else:
			raise serializers.ValidationError("Must include 'username' and 'password'.")

		data["user"] = user
		return data


class AccountSerializer(serializers.ModelSerializer):
	class Meta:
		model = Account
		fields = ("id", "name", "balance", "created_at")


class CategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = Category
		fields = ("id", "name", "type")


class BudgetSerializer(serializers.ModelSerializer):
	category = CategorySerializer(read_only=True)
	category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(type=Category.TYPE_EXPENSE), source="category", write_only=True)

	class Meta:
		model = Budget
		fields = ("id", "category", "category_id", "allocated_amount", "remaining_amount")


class TransactionSerializer(serializers.ModelSerializer):
	account = AccountSerializer(read_only=True)
	account_id = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), source="account", write_only=True)
	category = CategorySerializer(read_only=True)
	category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source="category", write_only=True)
	budget = serializers.SerializerMethodField(read_only=True)
	budget_id = serializers.PrimaryKeyRelatedField(queryset=Budget.objects.all(), source="budget", write_only=True, allow_null=True, required=False)

	class Meta:
		model = Transaction
		fields = ("id", "account", "account_id", "category", "category_id", "budget", "budget_id", "description", "date", "amount", "created_at")

	def create(self, validated_data):
		# user is set in the viewset perform_create
		return super().create(validated_data)

	def update(self, instance, validated_data):
		return super().update(instance, validated_data)

	def get_budget(self, obj):
		if not getattr(obj, "budget", None):
			return None
		return {"id": obj.budget.id, "category": obj.budget.category.id if obj.budget.category else None, "allocated_amount": obj.budget.allocated_amount, "remaining_amount": obj.budget.remaining_amount}


class SavingsGoalSerializer(serializers.ModelSerializer):
	class Meta:
		model = SavingsGoal
		fields = ("id", "name", "description", "current_amount", "target_amount", "created_at")

	def create(self, validated_data):
		return super().create(validated_data)

	def update(self, instance, validated_data):
		return super().update(instance, validated_data)
