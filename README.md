# Credit Approval System

Django 4+ REST API for credit approval based on customer data and loan eligibility.

## Requirements

- Python 3.11+
- Django 4+
- Django REST Framework
- PostgreSQL (for Docker)
- Redis (for Celery background workers)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/register/` | POST | Register new customer |
| `/check-eligibility/` | POST | Check loan eligibility |
| `/create-loan/` | POST | Create loan (if eligible) |
| `/view-loan/<loan_id>/` | GET | View single loan details |
| `/view-loans/<customer_id>/` | GET | View all loans by customer |
| `/admin/` | GET | Django admin |

## Local Development (SQLite)

```bash
cd credit_approval
pip install -r credit_approval/requirements.txt
python manage.py migrate
python manage.py runserver
```

## Docker (PostgreSQL + Redis + Celery)

Run everything with a single command:

```bash
cd credit_approval
docker-compose up --build
```

- API: http://localhost:8000
- Load data: Copy `customer_data.xlsx` and `loan_data.xlsx` into the container, then:
  ```bash
  docker-compose exec web python manage.py load_data /path/to/customer_data.xlsx /path/to/loan_data.xlsx
  ```

## Data Ingestion

Place `customer_data.xlsx` and `loan_data.xlsx` in the project directory, then:

```bash
# Synchronous (no Redis needed)
python manage.py load_data customer_data.xlsx loan_data.xlsx

# Asynchronous (requires Celery + Redis)
python manage.py load_data customer_data.xlsx loan_data.xlsx --async
```

## Run Tests

```bash
python manage.py test
```
