"""
Unit tests for Credit Approval System APIs.
"""
from datetime import date, timedelta

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from customers.models import Customer
from loans.models import Loan
from loans.utilis import calculate_emi


class RegisterAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_customer_success(self):
        response = self.client.post('/register/', {
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'monthly_income': 50000,
            'phone_number': '9876543210'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('customer_id', data)
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['age'], 30)
        self.assertEqual(data['monthly_income'], 50000)
        self.assertEqual(data['approved_limit'], 1800000)  # 36 * 50000, rounded to lakh

    def test_register_missing_fields(self):
        response = self.client.post('/register/', {
            'first_name': 'John',
            'last_name': 'Doe',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CheckEligibilityAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name='Jane',
            last_name='Doe',
            age=25,
            monthly_income=60000,
            phone_number='9876543211',
            approved_limit=2000000
        )

    def test_check_eligibility_success(self):
        response = self.client.post('/check-eligibility/', {
            'customer_id': self.customer.id,
            'loan_amount': 100000,
            'interest_rate': 12,
            'tenure': 12
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('approval', data)
        self.assertIn('monthly_installment', data)
        self.assertIn('corrected_interest_rate', data)

    def test_check_eligibility_customer_not_found(self):
        response = self.client.post('/check-eligibility/', {
            'customer_id': 99999,
            'loan_amount': 100000,
            'interest_rate': 12,
            'tenure': 12
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CreateLoanAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name='Test',
            last_name='User',
            age=28,
            monthly_income=80000,
            phone_number='9876543212',
            approved_limit=3000000
        )

    def test_create_loan_missing_fields(self):
        response = self.client.post('/create-loan/', {
            'customer_id': self.customer.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ViewLoanAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name='View',
            last_name='Test',
            age=35,
            monthly_income=70000,
            phone_number='9876543213',
            approved_limit=2500000
        )
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=200000,
            tenure=24,
            interest_rate=10,
            monthly_installment=9231.62,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=720)
        )

    def test_view_loan_success(self):
        response = self.client.get(f'/view-loan/{self.loan.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['loan_id'], self.loan.id)
        self.assertEqual(data['loan_amount'], 200000)
        self.assertIn('customer', data)
        self.assertEqual(data['customer']['first_name'], 'View')

    def test_view_loan_not_found(self):
        response = self.client.get('/view-loan/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ViewLoansAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name='List',
            last_name='Test',
            age=40,
            monthly_income=90000,
            phone_number='9876543214',
            approved_limit=3200000
        )
        Loan.objects.create(
            customer=self.customer,
            loan_amount=100000,
            tenure=12,
            interest_rate=11,
            monthly_installment=8832.12,
            emis_paid_on_time=3,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365)
        )

    def test_view_loans_success(self):
        response = self.client.get(f'/view-loans/{self.customer.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('loan_id', data[0])
            self.assertIn('repayments_left', data[0])

    def test_view_loans_customer_not_found(self):
        response = self.client.get('/view-loans/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EMICalculationTest(TestCase):
    def test_calculate_emi(self):
        emi = calculate_emi(100000, 12, 12)
        self.assertIsInstance(emi, (int, float))
        self.assertGreater(emi, 0)
        self.assertLess(emi, 100000)
