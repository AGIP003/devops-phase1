"""
Personal Finance Tracker - Main CLI
"""
import argparse
import sys
import logging
from datetime import datetime

from utils.storage import Storage
from utils.validations import (
    validate_amount, validate_transaction_type,
    validate_category, validate_date, validate_description,
    ValidationError
)
from utils.reports import (
    generate_summary, generate_category_report,
    generate_monthly_report, filter_by_date_range,
    filter_by_category
)

def setup_logging():
    """Configure logging"""
    import os
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO
    )

