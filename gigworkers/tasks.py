from django.utils import timezone
from datetime import timedelta
from .models import *
import logging

def calculate_daily_interest():
    """Calculate daily interest for all active EWA transactions."""
    today = timezone.now().date()
    active_transactions = EWATransaction.objects.filter(
        status='COMPLETED',
        repayment_status__in=['PENDING', 'PARTIAL'],
        due_date__gte=today
    )
    for transaction in active_transactions:
        #--------------Calculate daily interest
        daily_interest_rate = transaction.interest_rate / 100
        daily_interest = transaction.amount * daily_interest_rate

        # Log the daily interest charge
        EWAInterestLog.objects.create(
            transaction=transaction,
            event_type='DAILY_INTEREST',
            amount=daily_interest,
            event_date=today,
            description=f"Daily interest charge for transaction {transaction.transaction_id}."
        )

        #-----------------Update the total payable amount
        transaction.total_payable += daily_interest
        transaction.save()