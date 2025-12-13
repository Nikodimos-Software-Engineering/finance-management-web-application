from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Account(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")
	name = models.CharField(max_length=255)
	balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.user})"


class Category(models.Model):
	TYPE_INCOME = "income"
	TYPE_EXPENSE = "expense"
	TYPE_CHOICES = [
		(TYPE_INCOME, "Income"),
		(TYPE_EXPENSE, "Expense"),
	]

	name = models.CharField(max_length=255)
	type = models.CharField(max_length=10, choices=TYPE_CHOICES)

	def __str__(self):
		return f"{self.name} ({self.type})"


class Budget(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
	allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

	def save(self, *args, **kwargs):
		if self.pk is None:
			self.remaining_amount = self.allocated_amount
		super().save(*args, **kwargs)

	class Meta:
		unique_together = ("user", "category")

	def __str__(self):
		return f"Budget {self.category} for {self.user}"


class Transaction(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
	account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
	budget = models.ForeignKey('Budget', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
	description = models.TextField(blank=True)
	date = models.DateField(default=timezone.now)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.category} {self.amount} ({self.user})"

	def apply_effect(self):
		if self.category.type == Category.TYPE_INCOME:
			self.account.balance = (self.account.balance or 0) + self.amount
			self.account.save()
		else:
			self.account.balance = (self.account.balance or 0) - self.amount
			self.account.save()
			
			budget = None
			if self.budget_id:
				try:
					budget = Budget.objects.select_for_update().get(pk=self.budget_id, user=self.user)
				except Budget.DoesNotExist:
					budget = None
			else:
				try:
					budget = Budget.objects.select_for_update().get(user=self.user, category=self.category)
				except Budget.DoesNotExist:
					budget = None

			if budget:
				budget.remaining_amount = (budget.remaining_amount or 0) - self.amount
				budget.save()

	def reverse_effect(self):
		if self.category.type == Category.TYPE_INCOME:
			self.account.balance = (self.account.balance or 0) - self.amount
			self.account.save()
		else:
			self.account.balance = (self.account.balance or 0) + self.amount
			self.account.save()
			budget = None
			if self.budget_id:
				try:
					budget = Budget.objects.select_for_update().get(pk=self.budget_id, user=self.user)
				except Budget.DoesNotExist:
					budget = None
			else:
				try:
					budget = Budget.objects.select_for_update().get(user=self.user, category=self.category)
				except Budget.DoesNotExist:
					budget = None

			if budget:
				budget.remaining_amount = (budget.remaining_amount or 0) + self.amount
				budget.save()

	def save(self, *args, **kwargs):
		with transaction.atomic():
			if self.pk:
				old = Transaction.objects.select_for_update().get(pk=self.pk)
				old.reverse_effect()
			super().save(*args, **kwargs)
			self.apply_effect()

	def delete(self, *args, **kwargs):
		with transaction.atomic():
			self.reverse_effect()
			super().delete(*args, **kwargs)


class SavingsGoal(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_goals")
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	target_amount = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.user})"
