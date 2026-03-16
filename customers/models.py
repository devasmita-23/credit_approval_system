from django.db import models

# Create your models here.

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=15)

    monthly_income = models.FloatField()
    approved_limit = models.FloatField()
    current_debt = models.FloatField(default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"