from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - ${self.balance}"


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

	@property
	def spent_amount(self):
		return self.allocated_amount - self.remaining_amount

	@property
	def spent_percentage(self):
		if self.allocated_amount == 0:
			return 0
		return float(self.spent_amount / self.allocated_amount * 100)

	@property
	def spending_alert(self):
		pct = self.spent_percentage
		if pct >= 100:
			return {"type": "danger", "message": f"Budget exceeded! Spending is {pct:.0f}% of allocated."}
		if pct >= 80:
			return {"type": "warning", "message": f"You've used {pct:.0f}% of your budget."}
		return None


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SavingsGoal(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_goals")
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	target_amount = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} ({self.user})"
