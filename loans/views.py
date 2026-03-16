"""
Loan API views - check-eligibility, create-loan, view-loan, view-loans
"""
from datetime import date, timedelta
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from customers.models import Customer
from loans.models import Loan
from loans.credit_score import calculate_credit_score
from loans.utilis import calculate_emi


# Interest rate slabs by credit rating (lowest rate for each slab)
CREDIT_SLABS = {
    'high': 0,      # credit > 50: any rate ok
    'medium': 12,   # 30 < credit <= 50: min 12%
    'low': 16,      # 10 < credit <= 30: min 16%
    'very_low': 999  # credit <= 10: no approval
}


def _get_eligibility(customer_id, loan_amount, interest_rate, tenure):
    """
    Check loan eligibility. Returns (approval, corrected_interest_rate, monthly_installment).
    """
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return None, None, None  # Customer not found

    credit_score = calculate_credit_score(customer)

    # Current loans (not yet ended)
    today = date.today()
    current_loans = Loan.objects.filter(
        customer=customer,
        end_date__gte=today
    )

    # Sum of current EMIs
    total_current_emi = sum(
        loan.monthly_installment for loan in current_loans
    )

    # If sum of current EMIs > 50% of monthly salary, don't approve
    if total_current_emi > (customer.monthly_income * 0.5):
        emi = calculate_emi(loan_amount, interest_rate, tenure)
        return False, interest_rate, round(emi, 2)

    # Determine slab and min interest rate
    if credit_score > 50:
        slab = 'high'
        min_rate = 0
    elif credit_score > 30:
        slab = 'medium'
        min_rate = 12
    elif credit_score > 10:
        slab = 'low'
        min_rate = 16
    else:
        slab = 'very_low'
        emi = calculate_emi(loan_amount, interest_rate, tenure)
        return False, interest_rate, round(emi, 2)

    # Correct interest rate if below slab
    corrected_rate = max(interest_rate, min_rate)
    emi = calculate_emi(loan_amount, corrected_rate, tenure)

    approval = interest_rate >= min_rate if slab != 'high' else True
    return approval, corrected_rate, round(emi, 2)


@api_view(['POST'])
def check_eligibility(request):
    """Check loan eligibility based on credit score."""
    customer_id = request.data.get('customer_id')
    loan_amount = request.data.get('loan_amount')
    interest_rate = request.data.get('interest_rate')
    tenure = request.data.get('tenure')

    if customer_id is None or loan_amount is None or interest_rate is None or tenure is None:
        return Response(
            {'error': 'Missing required fields: customer_id, loan_amount, interest_rate, tenure'},
            status=status.HTTP_400_BAD_REQUEST
        )

    approval, corrected_rate, monthly_installment = _get_eligibility(
        customer_id, float(loan_amount), float(interest_rate), int(tenure)
    )

    if approval is None:
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'customer_id': customer_id,
        'approval': approval,
        'interest_rate': float(interest_rate),
        'corrected_interest_rate': float(corrected_rate),
        'tenure': tenure,
        'monthly_installment': monthly_installment
    })


@api_view(['POST'])
def create_loan(request):
    """Process a new loan based on eligibility."""
    customer_id = request.data.get('customer_id')
    loan_amount = request.data.get('loan_amount')
    interest_rate = request.data.get('interest_rate')
    tenure = request.data.get('tenure')

    if customer_id is None or loan_amount is None or interest_rate is None or tenure is None:
        return Response(
            {'error': 'Missing required fields: customer_id, loan_amount, interest_rate, tenure'},
            status=status.HTTP_400_BAD_REQUEST
        )

    approval, corrected_rate, monthly_installment = _get_eligibility(
        customer_id, float(loan_amount), float(interest_rate), int(tenure)
    )

    if approval is None:
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not approval:
        return Response({
            'loan_id': None,
            'customer_id': customer_id,
            'loan_approved': False,
            'message': 'Loan not approved based on eligibility criteria',
            'monthly_installment': monthly_installment
        }, status=status.HTTP_200_OK)

    # Create the loan
    customer = Customer.objects.get(id=customer_id)
    start_date = date.today()
    end_date = start_date + timedelta(days=tenure * 30)  # Approx monthly

    loan = Loan.objects.create(
        customer=customer,
        loan_amount=float(loan_amount),
        tenure=int(tenure),
        interest_rate=float(corrected_rate),
        monthly_installment=monthly_installment,
        emis_paid_on_time=0,
        start_date=start_date,
        end_date=end_date
    )

    return Response({
        'loan_id': loan.id,
        'customer_id': customer_id,
        'loan_approved': True,
        'message': 'Loan approved successfully',
        'monthly_installment': monthly_installment
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def view_loan(request, loan_id):
    """View single loan details with customer info."""
    try:
        loan = Loan.objects.select_related('customer').get(id=loan_id)
    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    customer = loan.customer
    return Response({
        'loan_id': loan.id,
        'customer': {
            'id': customer.id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone_number': customer.phone_number,
            'age': customer.age
        },
        'loan_amount': loan.loan_amount,
        'interest_rate': loan.interest_rate,
        'monthly_installment': loan.monthly_installment,
        'tenure': loan.tenure
    })


@api_view(['GET'])
def view_loans(request, customer_id):
    """View all current loans by customer ID."""
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    today = date.today()
    loans = Loan.objects.filter(
        customer=customer,
        end_date__gte=today
    )

    result = []
    for loan in loans:
        # EMIs left = tenure - emis_paid_on_time (simplified)
        repayments_left = max(0, loan.tenure - loan.emis_paid_on_time)
        result.append({
            'loan_id': loan.id,
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_installment': loan.monthly_installment,
            'repayments_left': repayments_left
        })

    return Response(result)
