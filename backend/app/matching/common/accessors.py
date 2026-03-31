from __future__ import annotations


def get_payment_id(payment):
    return payment.id


def get_payment_amount(payment):
    return payment.amount


def get_payment_currency(payment):
    return payment.currency_code


def get_payment_expected_date(payment):
    return payment.expected_payment_date


def get_payment_reference_normalized(payment):
    return payment.reference_text_normalized


def get_payment_customer_name_normalized(payment):
    return payment.customer_name_normalized


def get_bank_id(bank):
    return bank.id


def get_bank_amount(bank):
    return bank.amount


def get_bank_currency(bank):
    return bank.currency_code


def get_bank_booking_date(bank):
    return bank.booking_date


def get_bank_reference_normalized(bank):
    return bank.reference_text_normalized


def get_bank_counterparty_name_normalized(bank):
    return bank.counterparty_text_normalized


def get_bank_description_normalized(bank):
    return bank.transaction_description_normalized


def get_bank_direction(bank):
    return bank.direction


def get_bank_is_reversal(bank):
    return bool(bank.is_reversal)