"""
URL configuration for credit_approval project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from customers.views import api_home, register_customer
from loans.views import check_eligibility, create_loan, view_loan, view_loans

urlpatterns = [
    path('', api_home),
    path('admin/', admin.site.urls),
    path('register/', register_customer, name='register'),
    path('register', RedirectView.as_view(url='/register/', permanent=False)),
    path('check-eligibility/', check_eligibility, name='check_eligibility'),
    path('check-eligibility', RedirectView.as_view(url='/check-eligibility/', permanent=False)),
    path('create-loan/', create_loan, name='create_loan'),
    path('create-loan', RedirectView.as_view(url='/create-loan/', permanent=False)),
    path('view-loan/<int:loan_id>/', view_loan, name='view_loan'),
    path('view-loans/<int:customer_id>/', view_loans, name='view_loans'),
]