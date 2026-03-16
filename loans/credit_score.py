"""
Credit score calculation based on assignment specification:
- Past loans paid on time
- No of loans taken in past
- Loan activity in current year
- Loan approved volume
- If sum of current loans > approved limit, credit score = 0
"""
from datetime import datetime

from loans.models import Loan


def calculate_credit_score(customer):
    """Calculate credit score (0-100) based on historical loan data."""
    # Current loans = loans that haven't ended yet (end_date >= today)
    today = datetime.now().date()
    all_loans = Loan.objects.filter(customer=customer)
    current_loans = all_loans.filter(end_date__gte=today)

    # If sum of current loans > approved limit, score = 0
    total_current_loan_amount = sum(
        loan.loan_amount for loan in current_loans
    )
    if total_current_loan_amount > customer.approved_limit:
        return 0

    if not all_loans.exists():
        return 50  # No history - neutral score

    # Component 1: Past loans paid on time (weight: 35 points)
    total_emis = sum(
        loan.tenure for loan in all_loans
    )
    emis_paid_on_time = sum(
        loan.emis_paid_on_time for loan in all_loans
    )
    repayment_ratio = emis_paid_on_time / total_emis if total_emis > 0 else 1
    repayment_score = min(35, int(repayment_ratio * 35))

    # Component 2: Number of loans (weight: 15 points) - moderate history is good
    loan_count = all_loans.count()
    count_score = min(15, loan_count * 3)  # Up to 5 loans = 15 pts

    # Component 3: Loan activity in current year (weight: 25 points)
    current_year = datetime.now().year
    current_year_loans = all_loans.filter(
        start_date__year=current_year
    )
    activity_score = min(25, current_year_loans.count() * 12)

    # Component 4: Loan approved volume (weight: 25 points)
    total_volume = sum(loan.loan_amount for loan in all_loans)
    volume_ratio = min(1.0, total_volume / max(customer.approved_limit, 1))
    volume_score = int(volume_ratio * 25)

    score = repayment_score + count_score + activity_score + volume_score
    return min(100, max(0, score))
