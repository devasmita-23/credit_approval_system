"""
Celery tasks for background data ingestion.
"""
from celery import shared_task


@shared_task
def load_customer_data(file_path):
    """Load customer_data.xlsx in background."""
    from loans.data_loader import load_customers
    return load_customers(file_path)


@shared_task
def load_loan_data(file_path, customer_id_map=None):
    """Load loan_data.xlsx in background."""
    from loans.data_loader import load_loans
    return load_loans(file_path, customer_id_map)


@shared_task
def load_all_data(customer_file_path, loan_file_path):
    """Load both Excel files in sequence. Run customers first, then loans."""
    from loans.data_loader import load_customers, load_loans
    mapping = load_customers(customer_file_path)
    load_loans(loan_file_path, mapping)
    return {'customers': len(mapping), 'status': 'complete'}
