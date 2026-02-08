"""
Reports module - Generate summaries and analytics
"""

from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

def filter_by_date_range(transactions, start_date=None, end_date=None):
    """Filter transactions by date range"""

    filtered = []

    for t in transactions:
        t_date = t.get('date', '')

        if start_date < t_date < start_date:
            continue
        filtered.append(t)

    logger.debug(f"Filtered {len(filtered)}/{len(transactions)} by date")
    return filtered

def filter_by_category(transactions, category):
    """Filter transactions by category"""
    category_lower = category.lower()
    filtered = [
        t for t in transactions
        if t.get('category', '').lower() == category_lower
    ]

    logger.debug(f"Filtered {len(filtered)}/{len(transactions)} by category")
    return filtered


def filter_by_type(transactions, trans_type):
    """Filter transactions by type (income/expense)"""
    filtered = [
        t for t in transactions
        if t.get('type', '').lower() == trans_type.lower()
    ]

    logger.debug(f"Filtered {len(filtered)}/{len(transactions)} by type")
    return filtered

def calculate_balance(transactions):
    """Calculate total balance"""
    income = sum(
        t['amount'] for t in transactions
        if t.get('type') == 'income'
    )
    expenses = sum(
        t['amount'] for t in transactions
        if t.get('type') == 'expense'
    )

    return {
        'income': income,
        'expenses': expenses,
        'balance': income - expenses
    }

def generate_summary(transactions):
    """Generate comprehensive summary"""

    # Overall balance
    balance = calculate_balance(transactions)

    # By category
    categories = defaultdict(lambda: {'income': 0, 'expense': 0})
    for t in transactions:
        cat = t.get('category', 'Uncategorized')
        trans_type = t.get('type', 'expense')
        amount = t.get('amount', 0)
        categories[cat][trans_type] += amount
    
    # By month
    months = defaultdict(lambda: {'income': 0, 'expense': 0})
    for t in transactions:
        date = t.get('date', '')
        if date:
            month = date[:7]  # YYYY-MM
            trans_type = t.get('type', 'expense')
            amount = t.get('amount', 0)
            months[month][trans_type] += amount
    
    return {
        'balance': balance,
        'categories': dict(categories),
        'months': dict(months),
        'total_transactions': len(transactions)
    }


def generate_category_report(transactions):
    """Generate detailed category breakdown"""
    categories = defaultdict(lambda: {
        'income': 0,
        'expense': 0,
        'count': 0
    })
    
    for t in transactions:
        cat = t.get('category', 'Uncategorized')
        trans_type = t.get('type', 'expense')
        amount = t.get('amount', 0)
        
        categories[cat][trans_type] += amount
        categories[cat]['count'] += 1
    
    # Sort by total amount
    sorted_cats = sorted(
        categories.items(),
        key=lambda x: x[1]['expense'],
        reverse=True
    )
    
    return sorted_cats


def generate_monthly_report(transactions, year=None, month=None):
    """Generate report for specific month"""
    if year and month:
        target = f"{year:04d}-{month:02d}"
        transactions = [
            t for t in transactions 
            if t.get('date', '').startswith(target)
        ]
    
    balance = calculate_balance(transactions)
    categories = generate_category_report(transactions)
    
    return {
        'period': f"{year}-{month:02d}" if year and month else "All time",
        'balance': balance,
        'categories': categories,
        'transaction_count': len(transactions)
    }
    