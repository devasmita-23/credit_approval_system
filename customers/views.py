from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Customer


@api_view(['GET'])
def api_home(request):
    """Welcome endpoint - prevents 404 when visiting root URL."""
    return Response({
        "message": "Credit Approval System API",
        "version": "1.0",
        "endpoints": {
            "register": "/register/ (POST)",
            "check_eligibility": "/check-eligibility/ (POST)",
            "create_loan": "/create-loan/ (POST)",
            "view_loan": "/view-loan/<loan_id>/ (GET)",
            "view_loans": "/view-loans/<customer_id>/ (GET)",
            "admin": "/admin/ (Django Admin)",
        }
    })


@api_view(['POST'])
def register_customer(request):
    """Add a new customer. approved_limit = 36 * monthly_income (rounded to nearest lakh)."""
    required = ['first_name', 'last_name', 'age', 'monthly_income', 'phone_number']
    for field in required:
        if field not in request.data:
            return Response(
                {'error': f'Missing required field: {field}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    try:
        salary = float(request.data['monthly_income'])
        age = int(request.data['age'])
    except (ValueError, TypeError):
        return Response(
            {'error': 'monthly_income and age must be valid numbers'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Rounded to nearest lakh (100,000)
    approved_limit = round(36 * salary, -5)

    customer = Customer.objects.create(
        first_name=request.data['first_name'],
        last_name=request.data['last_name'],
        age=age,
        phone_number=str(request.data['phone_number']),
        monthly_income=salary,
        approved_limit=approved_limit
    )

    return Response({
        "customer_id": customer.id,
        "name": f"{customer.first_name} {customer.last_name}",
        "age": customer.age,
        "monthly_income": customer.monthly_income,
        "approved_limit": approved_limit,
        "phone_number": customer.phone_number
    }, status=status.HTTP_201_CREATED)