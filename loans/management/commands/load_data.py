"""
Management command to ingest customer_data.xlsx and loan_data.xlsx.
Uses Celery background worker if available, otherwise runs synchronously.
Usage: python manage.py load_data path/to/customer_data.xlsx path/to/loan_data.xlsx
"""
import os
from django.core.management.base import BaseCommand

from loans.data_loader import load_customers, load_loans


class Command(BaseCommand):
    help = 'Load customer and loan data from Excel files. Run customers first, then loans.'

    def add_arguments(self, parser):
        parser.add_argument(
            'customer_file',
            nargs='?',
            default='customer_data.xlsx',
            help='Path to customer_data.xlsx'
        )
        parser.add_argument(
            'loan_file',
            nargs='?',
            default='loan_data.xlsx',
            help='Path to loan_data.xlsx'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='async_load',
            help='Run via Celery worker (requires Redis)'
        )

    def handle(self, *args, **options):
        customer_path = options['customer_file']
        loan_path = options['loan_file']

        if not os.path.exists(customer_path):
            self.stderr.write(self.style.ERROR(f'File not found: {customer_path}'))
            return

        if options.get('async_load'):
            try:
                from loans.tasks import load_all_data
                result = load_all_data.delay(customer_path, loan_path)
                self.stdout.write(
                    self.style.SUCCESS(f'Data load task queued. Task ID: {result.id}')
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'Celery unavailable, running synchronously: {e}')
                )
                self._run_sync(customer_path, loan_path)
        else:
            self._run_sync(customer_path, loan_path)

    def _run_sync(self, customer_path, loan_path):
        self.stdout.write('Loading customers...')
        mapping = load_customers(customer_path)
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(mapping)} customers'))

        if os.path.exists(loan_path):
            self.stdout.write('Loading loans...')
            load_loans(loan_path, mapping)
            count = sum(1 for _ in mapping.values())
            self.stdout.write(self.style.SUCCESS('Loans loaded'))
        else:
            self.stderr.write(self.style.WARNING(f'Loan file not found: {loan_path}'))
