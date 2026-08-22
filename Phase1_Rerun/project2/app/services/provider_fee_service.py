from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.transaction import Transaction
from app.models.transaction_import import TransactionImport


TARIFF_RULESET_VERSION = "provider-public-rules-2026-08-23"
SUPPORTED_FEE_SOURCES = {
    "unknown",
    "provider_reported",
    "estimated_tariff",
    "user_confirmed",
}


class ProviderFeeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FeeEstimate:
    amount: Decimal
    tariff_version: str
    reason: str


def estimate_provider_fee(import_record: TransactionImport) -> FeeEstimate | None:
    """Return only high-confidence, explainable estimates.

    Variable send-money, Paybill, bank and withdrawal bands deliberately stay
    unknown until a reviewed, dated provider tariff is installed. A missing fee
    is better than a confidently wrong financial total.
    """
    provider_type = (
        import_record.provider,
        import_record.provider_transaction_type,
    )
    if provider_type == ("mpesa", "buy_goods"):
        merchant = (import_record.transaction.merchant_name or "").casefold()
        fuel_markers = ("fuel", "petrol", "service station")
        if not any(marker in merchant for marker in fuel_markers):
            return FeeEstimate(
                amount=Decimal("0.00"),
                tariff_version=TARIFF_RULESET_VERSION,
                reason=(
                    "Standard Lipa na M-PESA Buy Goods customer payments are "
                    "zero-fee; fuel merchants are excluded from this estimate."
                ),
            )

    return None


def backfill_missing_provider_fees(
    *,
    apply_changes: bool = False,
    user_id: int | None = None,
) -> dict[str, object]:
    """Find explainable missing fees; write only when explicitly requested."""
    statement = (
        select(TransactionImport)
        .options(joinedload(TransactionImport.transaction))
        .join(Transaction, TransactionImport.transaction_id == Transaction.id)
        .where(
            TransactionImport.fee.is_(None),
            TransactionImport.fee_source == "unknown",
            Transaction.deleted_at.is_(None),
        )
        .order_by(TransactionImport.id)
    )
    if user_id is not None:
        statement = statement.where(TransactionImport.user_id == user_id)

    candidates = []
    skipped = 0
    try:
        for import_record in db.session.scalars(statement):
            estimate = estimate_provider_fee(import_record)
            if estimate is None:
                skipped += 1
                continue
            candidates.append({
                "transactionId": import_record.transaction_id,
                "provider": import_record.provider,
                "providerTransactionType": import_record.provider_transaction_type,
                "amount": str(estimate.amount),
                "tariffVersion": estimate.tariff_version,
                "reason": estimate.reason,
            })
            if apply_changes:
                import_record.fee = estimate.amount
                import_record.fee_source = "estimated_tariff"
                import_record.original_estimated_fee = estimate.amount
                import_record.fee_tariff_version = estimate.tariff_version

        if apply_changes:
            db.session.commit()
        else:
            db.session.rollback()
    except Exception:
        db.session.rollback()
        raise

    return {
        "mode": "apply" if apply_changes else "dry-run",
        "rulesetVersion": TARIFF_RULESET_VERSION,
        "candidateCount": len(candidates),
        "skippedUnknownCount": skipped,
        "candidates": candidates,
    }


def update_provider_fee_for_user(
    user_id: int,
    transaction_id: int,
    value,
) -> TransactionImport | None:
    """Confirm an editable fee while preserving the original estimate."""
    try:
        fee = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ProviderFeeError("Provider fee must be a number") from error
    if not fee.is_finite() or fee < 0:
        raise ProviderFeeError("Provider fee must be zero or greater")
    if fee != fee.quantize(Decimal("0.01")):
        raise ProviderFeeError("Provider fee cannot have more than 2 decimal places")
    if fee > Decimal("1000000.00"):
        raise ProviderFeeError("Provider fee is outside the supported range")

    statement = (
        select(TransactionImport)
        .join(Transaction, TransactionImport.transaction_id == Transaction.id)
        .where(
            TransactionImport.transaction_id == transaction_id,
            TransactionImport.user_id == user_id,
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    )
    import_record = db.session.scalar(statement)
    if import_record is None:
        return None
    if import_record.fee_source == "provider_reported":
        raise ProviderFeeError(
            "A provider-reported fee is retained as evidence and cannot be overwritten"
        )

    try:
        if (
            import_record.fee_source == "estimated_tariff"
            and import_record.original_estimated_fee is None
        ):
            import_record.original_estimated_fee = import_record.fee
        import_record.fee = fee
        import_record.fee_source = "user_confirmed"
        db.session.commit()
        return import_record
    except Exception:
        db.session.rollback()
        raise
