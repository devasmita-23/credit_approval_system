from django.db import models

from customers.models import Customer

class Loan(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    loan_amount = models.FloatField()
    tenure = models.IntegerField()
    interest_rate = models.FloatField()

    monthly_installment = models.FloatField()

    emis_paid_on_time = models.IntegerField(default=0)

    start_date = models.DateField()
    end_date = models.DateField()