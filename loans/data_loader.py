"""
Data loader for customer_data.xlsx and loan_data.xlsx.
Ingest data into the system. Designed to be called from Celery background task.
"""
import pandas as pd
from datetime import datetime

from customers.models import Customer
from loans.models import Loan


def _normalize_columns(df):
    """Normalize column names for flexible matching."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
    return df


def load_customers(file_path):
    """
    Load customers from customer_data.xlsx.
    Columns: customer_id, first_name, last_name, phone_number, monthly_salary,
             approved_limit, current_debt
    Returns mapping of excel_customer_id -> Customer for loan loading.
    """
    df = pd.read_excel(file_path)
    df = _normalize_columns(df)

    mapping = {}
    for _, row in df.iterrows():
        cid = row.get('customer_id', None)
        first = str(row.get('first_name', ''))[:100]
        last = str(row.get('last_name', ''))[:100]
        phone = str(row.get('phone_number', ''))[:15]
        salary = float(row.get('monthly_salary', row.get('monthly_income', 0)))
        limit = float(row.get('approved_limit', 0))
        debt = float(row.get('current_debt', 0))

        customer = Customer.objects.create(
            first_name=first or 'Unknown',
            last_name=last or 'Unknown',
            age=0,  # Not in customer_data.xlsx
            phone_number=phone or '0',
            monthly_income=salary,
            approved_limit=limit,
            current_debt=debt
        )
        if cid is not None and not (isinstance(cid, float) and pd.isna(cid)):
            mapping[int(cid)] = customer
        else:
            # Fallback: assume order matches id
            mapping[customer.id] = customer

    return mapping


def load_loans(file_path, customer_id_map=None):
    """
    Load loans from loan_data.xlsx.
    Columns: customer_id, loan_id, loan_amount, tenure, interest_rate,
             monthly_repayment/emi, emis_paid_on_time, start_date, end_date
    """
    df = pd.read_excel(file_path)
    df = _normalize_columns(df)

    if customer_id_map is None:
        customer_id_map = {c.id: c for c in Customer.objects.all()}

    for _, row in df.iterrows():
        cid = row.get('customer_id', row.get('customerid', None))
        if cid is None or (isinstance(cid, float) and pd.isna(cid)):
            continue
        cid = int(cid)

        amount = float(row.get('loan_amount', row.get('loanamount', 0)))
        tenure = int(row.get('tenure', 0))
        rate = float(row.get('interest_rate', row.get('interestrate', 0)))
        emi = float(row.get('monthly_repayment', row.get('monthly_installment', row.get('emi', 0))))
        emis_paid = int(row.get('emis_paid_on_time', 0))
        start = row.get('start_date') or row.get('startdate')
        end = row.get('end_date') or row.get('enddate')

        if start is None or (isinstance(start, float) and pd.isna(start)):
            start = datetime.now().date()
        elif isinstance(start, str):
            start = datetime.strptime(str(start)[:10], '%Y-%m-%d').date()
        elif hasattr(start, 'date'):
            start = start.date()

        if end is None or (isinstance(end, float) and pd.isna(end)):
            end = start  # Fallback
        elif isinstance(end, str):
            end = datetime.strptime(str(end)[:10], '%Y-%m-%d').date()
        elif hasattr(end, 'date'):
            end = end.date()

        customer = customer_id_map.get(cid) or Customer.objects.filter(id=cid).first()
        if customer is None:
            continue

        Loan.objects.create(
            customer=customer,
            loan_amount=amount,
            tenure=tenure,
            interest_rate=rate,
            monthly_installment=emi,
            emis_paid_on_time=emis_paid,
            start_date=start,
            end_date=end
        )
