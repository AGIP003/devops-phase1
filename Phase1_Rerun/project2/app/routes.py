import os
from datetime import date

from flask import abort, current_app, g, jsonify, request
from werkzeug.exceptions import HTTPException

from app.middleware import login_required, admin_required
from app.serializers import (
    budget_item_to_dict,
    budget_to_dict,
    debt_to_dict,
    recurring_commitment_to_dict,
    savings_goal_to_dict,
    transaction_to_dict,
)
from app.services.budget_service import (
    create_budget_for_user,
    delete_budget_for_user,
    get_budgets_for_user,
    update_budget_for_user,
    update_budget_item_checked_for_user,
)
from app.services.transaction_service import (
    create_transaction_for_user,
    get_transaction_for_user,
    list_all_transactions,
    list_transactions_for_user,
    soft_delete_transaction_for_user,
    update_transaction_for_user,
)
from app.importers import (
    ParsedFulizaNotice,
    ParsedTransactionMessage,
    UnsupportedFinancialMessageError,
    parse_financial_message,
)
from app.importers.contracts import TransactionDirection
from app.services.transaction_import_service import (
    DuplicateTransactionImportError,
    TransactionMessageNotImportableError,
    import_transaction_message_for_user,
    payment_method_for_provider,
)
from app.services.transaction_import_preview import (
    InvalidImportPreviewError,
    create_ai_import_preview_token,
    load_ai_import_preview_token,
)
from app.services.ai_budget_service import (
    AIBudgetExceededError,
    run_provider_import_ai,
)
from app.services.ai_support import (
    AIConfigurationError,
    AIInvalidResponseError,
    AIServiceUnavailableError,
)
from app.services.provider_import_ai import is_provider_message_candidate
from app.services.user_service import delete_user as delete_user_record, get_user_by_id
from app.services.forex_service import ForexUnavailableError, get_current_forex_rates
from app.services.analytics_service import (
    AnalyticsPeriodError,
    AnalyticsSearchError,
    build_analytics_summary,
    build_description_trend,
)
from app.services.provider_fee_service import (
    ProviderFeeError,
    update_provider_fee_for_user,
)
from app.services.provider_financing_service import (
    DuplicateFinancingEventError,
    record_financing_notice_for_user,
)
from app.services.fee_dashboard_service import (
    FeeEstimateError,
    build_fee_dashboard,
    estimate_public_tariff,
    get_fee_tariff_catalog,
)
from app.debt_validation import parse_debt_create_payload, parse_debt_entry_payload
from app.services.debt_service import (
    DebtValidationError,
    add_debt_entry_for_user,
    archive_debt_for_user,
    create_debt_for_user,
    get_debt_for_user,
    list_debts_for_user,
    update_debt_entry_for_user,
    update_debt_for_user,
)
from app.savings_goal_validation import (
    parse_savings_goal_create_payload,
    parse_savings_goal_entry_payload,
)
from app.services.savings_goal_service import (
    SavingsGoalValidationError,
    add_savings_goal_entry_for_user,
    archive_savings_goal_for_user,
    create_savings_goal_for_user,
    get_savings_goal_for_user,
    list_savings_goals_for_user,
    update_savings_goal_entry_for_user,
    update_savings_goal_for_user,
)
from app.recurring_commitment_validation import (
    parse_commitment_cycle_payload,
    parse_commitment_status_payload,
    parse_recurring_commitment_create_payload,
)
from app.services.recurring_commitment_service import (
    RecurringCommitmentValidationError,
    archive_recurring_commitment_for_user,
    create_recurring_commitment_for_user,
    get_recurring_commitment_for_user,
    list_recurring_commitments_for_user,
    resolve_commitment_cycle_for_user,
    set_recurring_commitment_status_for_user,
    update_commitment_occurrence_for_user,
    update_recurring_commitment_for_user,
)
from finance_tracker.utils.validations import (
    validate_amount, validate_category, validate_date, validate_description, 
    validate_payment_method, ValidationError, validate_transaction_type
)


def register_routes(app):
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "Finance Tracker API", "endpoints": ["/transactions"]}), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        return {
            "status" : "ok",
            "environment": os.getenv("FLASK_ENV", "development")
        }, 200

    @app.route("/api/analytics/summary", methods=["GET"])
    @login_required
    def get_analytics_summary():
        """Return database-aggregated finance analytics for the signed-in user."""
        period = request.args.get("period", "12-months")
        try:
            summary = build_analytics_summary(
                g.current_user["user_id"],
                period,
            )
        except AnalyticsPeriodError as error:
            abort(400, description=str(error))

        response = jsonify(summary)
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/analytics/description-trend", methods=["GET"])
    @login_required
    def get_description_trend():
        """Return a calendar-aligned trend for an owned expense search."""
        query = request.args.get("query", "")
        period = request.args.get("period", "month")
        anchor_text = request.args.get("anchor")
        try:
            anchor = date.fromisoformat(anchor_text) if anchor_text else None
            result = build_description_trend(
                g.current_user["user_id"],
                query,
                period,
                anchor=anchor,
            )
        except (AnalyticsPeriodError, AnalyticsSearchError) as error:
            abort(400, description=str(error))
        except (TypeError, ValueError) as error:
            abort(400, description=f"Invalid analytics anchor date: {error}")

        response = jsonify(result)
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/fees/summary", methods=["GET"])
    @login_required
    def get_fee_summary():
        response = jsonify(build_fee_dashboard(g.current_user["user_id"]))
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/fees/tariffs", methods=["GET"])
    @login_required
    def get_fee_tariffs():
        response = jsonify(get_fee_tariff_catalog())
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/fees/estimate", methods=["POST"])
    @login_required
    def estimate_fee():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, description="Payload must be an object")
        try:
            estimate = estimate_public_tariff(
                data.get("provider"),
                data.get("service"),
                data.get("amount"),
            )
        except FeeEstimateError as error:
            abort(400, description=str(error))
        response = jsonify(estimate)
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/forex/rates", methods=["GET"])
    @login_required
    def get_forex_rates():
        try:
            result = get_current_forex_rates()
        except ForexUnavailableError:
            abort(503, description="Forex rates are temporarily unavailable")

        response = jsonify({
            "base": result.base,
            "provider": result.provider,
            "source": "Frankfurter",
            "rateDate": result.rate_date.isoformat(),
            "fetchedAt": result.fetched_at.isoformat(),
            "stale": result.stale,
            "rates": {
                "KES": "1",
                **{
                    quote: format(rate, "f")
                    for quote, rate in sorted(result.rates.items())
                },
            },
        })
        response.headers["Cache-Control"] = "private, max-age=300"
        return response, 200

    @app.route("/api/debts", methods=["GET"])
    @login_required
    def get_debts():
        debts = list_debts_for_user(g.current_user["user_id"])
        response = jsonify([debt_to_dict(debt) for debt in debts])
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/debts/<int:debt_id>", methods=["GET"])
    @login_required
    def get_debt(debt_id):
        debt = get_debt_for_user(g.current_user["user_id"], debt_id)
        if debt is None:
            abort(404, description="Debt not found")
        response = jsonify(debt_to_dict(debt))
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/debts", methods=["POST"])
    @login_required
    def create_debt():
        try:
            command = parse_debt_create_payload(request.get_json(silent=True))
            debt = create_debt_for_user(
                g.current_user["user_id"],
                command,
            )
        except DebtValidationError as error:
            abort(400, description=str(error))

        return jsonify({
            "data": debt_to_dict(debt),
            "status": "success",
        }), 201

    @app.route("/api/debts/<int:debt_id>/entries", methods=["POST"])
    @login_required
    def create_debt_entry(debt_id):
        try:
            command = parse_debt_entry_payload(request.get_json(silent=True))
            debt = add_debt_entry_for_user(
                g.current_user["user_id"],
                debt_id,
                command,
            )
        except DebtValidationError as error:
            abort(400, description=str(error))
        except ValueError as error:
            abort(400, description=str(error))

        if debt is None:
            abort(404, description="Debt not found")

        return jsonify({
            "data": debt_to_dict(debt),
            "status": "success",
        }), 201

    @app.route("/api/debts/<int:debt_id>", methods=["PATCH"])
    @login_required
    def update_debt(debt_id):
        try:
            command = parse_debt_create_payload(request.get_json(silent=True))
            debt = update_debt_for_user(
                g.current_user["user_id"],
                debt_id,
                command,
            )
        except DebtValidationError as error:
            abort(400, description=str(error))
        if debt is None:
            abort(404, description="Debt not found")
        return jsonify({"data": debt_to_dict(debt), "status": "success"}), 200

    @app.route(
        "/api/debts/<int:debt_id>/entries/<int:entry_id>",
        methods=["PATCH"],
    )
    @login_required
    def update_debt_entry(debt_id, entry_id):
        try:
            command = parse_debt_entry_payload(request.get_json(silent=True))
            debt = update_debt_entry_for_user(
                g.current_user["user_id"],
                debt_id,
                entry_id,
                command,
            )
        except (DebtValidationError, ValueError) as error:
            abort(400, description=str(error))
        if debt is None:
            abort(404, description="Debt activity not found")
        return jsonify({"data": debt_to_dict(debt), "status": "success"}), 200

    @app.route("/api/debts/<int:debt_id>", methods=["DELETE"])
    @login_required
    def archive_debt(debt_id):
        archived = archive_debt_for_user(
            g.current_user["user_id"],
            debt_id,
        )
        if not archived:
            abort(404, description="Debt not found")
        return jsonify({"message": "Debt archived", "status": "success"}), 200

    @app.route("/api/goals", methods=["GET"])
    @login_required
    def get_savings_goals():
        goals = list_savings_goals_for_user(g.current_user["user_id"])
        response = jsonify([savings_goal_to_dict(goal) for goal in goals])
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/goals/<int:goal_id>", methods=["GET"])
    @login_required
    def get_savings_goal(goal_id):
        goal = get_savings_goal_for_user(g.current_user["user_id"], goal_id)
        if goal is None:
            abort(404, description="Savings goal not found")
        response = jsonify(savings_goal_to_dict(goal))
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/goals", methods=["POST"])
    @login_required
    def create_savings_goal():
        try:
            command = parse_savings_goal_create_payload(
                request.get_json(silent=True)
            )
            goal = create_savings_goal_for_user(
                g.current_user["user_id"],
                command,
            )
        except SavingsGoalValidationError as error:
            abort(400, description=str(error))
        return jsonify({
            "data": savings_goal_to_dict(goal),
            "status": "success",
        }), 201

    @app.route("/api/goals/<int:goal_id>/entries", methods=["POST"])
    @login_required
    def create_savings_goal_entry(goal_id):
        try:
            command = parse_savings_goal_entry_payload(
                request.get_json(silent=True)
            )
            goal = add_savings_goal_entry_for_user(
                g.current_user["user_id"],
                goal_id,
                command,
            )
        except SavingsGoalValidationError as error:
            abort(400, description=str(error))
        if goal is None:
            abort(404, description="Savings goal not found")
        return jsonify({
            "data": savings_goal_to_dict(goal),
            "status": "success",
        }), 201

    @app.route("/api/goals/<int:goal_id>", methods=["PATCH"])
    @login_required
    def update_savings_goal(goal_id):
        try:
            command = parse_savings_goal_create_payload(
                request.get_json(silent=True)
            )
            goal = update_savings_goal_for_user(
                g.current_user["user_id"],
                goal_id,
                command,
            )
        except SavingsGoalValidationError as error:
            abort(400, description=str(error))
        if goal is None:
            abort(404, description="Savings goal not found")
        return jsonify({
            "data": savings_goal_to_dict(goal),
            "status": "success",
        }), 200

    @app.route(
        "/api/goals/<int:goal_id>/entries/<int:entry_id>",
        methods=["PATCH"],
    )
    @login_required
    def update_savings_goal_entry(goal_id, entry_id):
        try:
            command = parse_savings_goal_entry_payload(
                request.get_json(silent=True)
            )
            goal = update_savings_goal_entry_for_user(
                g.current_user["user_id"],
                goal_id,
                entry_id,
                command,
            )
        except SavingsGoalValidationError as error:
            abort(400, description=str(error))
        if goal is None:
            abort(404, description="Savings activity not found")
        return jsonify({
            "data": savings_goal_to_dict(goal),
            "status": "success",
        }), 200

    @app.route("/api/goals/<int:goal_id>", methods=["DELETE"])
    @login_required
    def archive_savings_goal(goal_id):
        archived = archive_savings_goal_for_user(
            g.current_user["user_id"],
            goal_id,
        )
        if not archived:
            abort(404, description="Savings goal not found")
        return jsonify({
            "message": "Savings goal archived",
            "status": "success",
        }), 200

    @app.route("/api/commitments", methods=["GET"])
    @login_required
    def get_recurring_commitments():
        commitments = list_recurring_commitments_for_user(
            g.current_user["user_id"]
        )
        response = jsonify([
            recurring_commitment_to_dict(commitment)
            for commitment in commitments
        ])
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/commitments/<int:commitment_id>", methods=["GET"])
    @login_required
    def get_recurring_commitment(commitment_id):
        commitment = get_recurring_commitment_for_user(
            g.current_user["user_id"],
            commitment_id,
        )
        if commitment is None:
            abort(404, description="Bill or subscription not found")
        response = jsonify(recurring_commitment_to_dict(commitment))
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/commitments", methods=["POST"])
    @login_required
    def create_recurring_commitment():
        try:
            command = parse_recurring_commitment_create_payload(
                request.get_json(silent=True)
            )
            commitment = create_recurring_commitment_for_user(
                g.current_user["user_id"],
                command,
            )
        except RecurringCommitmentValidationError as error:
            abort(400, description=str(error))
        return jsonify({
            "data": recurring_commitment_to_dict(commitment),
            "status": "success",
        }), 201

    @app.route("/api/commitments/<int:commitment_id>", methods=["PATCH"])
    @login_required
    def update_recurring_commitment(commitment_id):
        try:
            command = parse_recurring_commitment_create_payload(
                request.get_json(silent=True)
            )
            commitment = update_recurring_commitment_for_user(
                g.current_user["user_id"],
                commitment_id,
                command,
            )
        except RecurringCommitmentValidationError as error:
            abort(400, description=str(error))
        if commitment is None:
            abort(404, description="Bill or subscription not found")
        return jsonify({
            "data": recurring_commitment_to_dict(commitment),
            "status": "success",
        }), 200

    @app.route(
        "/api/commitments/<int:commitment_id>/cycles",
        methods=["POST"],
    )
    @login_required
    def resolve_commitment_cycle(commitment_id):
        try:
            command = parse_commitment_cycle_payload(
                request.get_json(silent=True)
            )
            commitment = resolve_commitment_cycle_for_user(
                g.current_user["user_id"],
                commitment_id,
                command,
            )
        except RecurringCommitmentValidationError as error:
            abort(400, description=str(error))
        if commitment is None:
            abort(404, description="Bill or subscription not found")
        return jsonify({
            "data": recurring_commitment_to_dict(commitment),
            "status": "success",
        }), 201

    @app.route(
        "/api/commitments/<int:commitment_id>/cycles/<int:occurrence_id>",
        methods=["PATCH"],
    )
    @login_required
    def update_commitment_cycle(commitment_id, occurrence_id):
        try:
            command = parse_commitment_cycle_payload(
                request.get_json(silent=True)
            )
            commitment = update_commitment_occurrence_for_user(
                g.current_user["user_id"],
                commitment_id,
                occurrence_id,
                command,
            )
        except RecurringCommitmentValidationError as error:
            abort(400, description=str(error))
        if commitment is None:
            abort(404, description="Payment history entry not found")
        return jsonify({
            "data": recurring_commitment_to_dict(commitment),
            "status": "success",
        }), 200

    @app.route(
        "/api/commitments/<int:commitment_id>/status",
        methods=["PATCH"],
    )
    @login_required
    def change_recurring_commitment_status(commitment_id):
        try:
            status = parse_commitment_status_payload(
                request.get_json(silent=True)
            )
            commitment = set_recurring_commitment_status_for_user(
                g.current_user["user_id"],
                commitment_id,
                status,
            )
        except RecurringCommitmentValidationError as error:
            abort(400, description=str(error))
        if commitment is None:
            abort(404, description="Bill or subscription not found")
        return jsonify({
            "data": recurring_commitment_to_dict(commitment),
            "status": "success",
        }), 200

    @app.route("/api/commitments/<int:commitment_id>", methods=["DELETE"])
    @login_required
    def archive_recurring_commitment(commitment_id):
        archived = archive_recurring_commitment_for_user(
            g.current_user["user_id"],
            commitment_id,
        )
        if not archived:
            abort(404, description="Bill or subscription not found")
        return jsonify({
            "message": "Bill or subscription archived",
            "status": "success",
        }), 200

    @app.route("/api/transactions", methods=["POST"])
    @login_required
    def create_transaction_route():
        data = request.get_json()

        if data is None:
            abort(400, description="error!! Invalid JSON")
        
        if not isinstance(data, dict):
            abort(400, description="Payload must be an object")
        
        # Check required fields exist
        required_fields = ["amount", "category", "type", "date", "payment_method"]
        for field in required_fields:
            if field not in data or data[field] is None:
                abort(400, description=f"Missing required field: {field}")
        
        try:
            # Validate type FIRST (required by category validation)
            transaction_type = validate_transaction_type(data.get("type"))
            
            # Then validate category (depends on type)
            category_name = validate_category(transaction_type, data.get("category"))
            
            # Validate other fields
            amount = validate_amount(data.get("amount"))
            transaction_date = validate_date(data.get("date"))
            description = validate_description(data.get("description", ""))
            merchant_name = data.get("merchant_name")
            payment_method_name = validate_payment_method(data.get("payment_method"))
            
            try:
                user_id = g.current_user["user_id"]
                saved_transaction = create_transaction_for_user(
                    user_id,
                    category_name,
                    transaction_type,
                    payment_method_name,
                    amount,
                    transaction_date,
                    description,
                    merchant_name,
                )
            except ValueError as e:
                abort(400, description=str(e))

            return jsonify({"data": transaction_to_dict(saved_transaction), "status": "success"}), 201
            
        except ValidationError as e:
            abort(400, description=str(e))
        except HTTPException:
            raise
        except Exception as e:
            abort(500, description=f"Server error: {str(e)}")

    @app.route("/api/transaction-imports/preview", methods=["POST"])
    @login_required
    def preview_transaction_import():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, description="Payload must be an object")

        raw_message = data.get("message")
        if not isinstance(raw_message, str) or not raw_message.strip():
            abort(400, description="A provider message is required")
        if len(raw_message) > 4000:
            abort(400, description="Provider message is too long")

        parser_strategy = "regex"
        preview_token = None
        confidence = None
        needs_review = False
        try:
            parsed = parse_financial_message(raw_message)
        except UnsupportedFinancialMessageError as error:
            if (
                not current_app.config["AI_FALLBACK_ENABLED"]
                or not is_provider_message_candidate(raw_message)
            ):
                abort(400, description=str(error))
            try:
                ai_result = run_provider_import_ai(raw_message)
            except AIBudgetExceededError as ai_error:
                abort(429, description=str(ai_error))
            except (
                AIConfigurationError,
                AIServiceUnavailableError,
            ):
                abort(
                    503,
                    description="Provider-message assistance is temporarily unavailable",
                )
            except AIInvalidResponseError:
                abort(422, description="That provider message could not be read safely")

            if not ai_result.extraction.can_parse or ai_result.parsed is None:
                abort(
                    400,
                    description=(
                        ai_result.extraction.reason
                        or "That provider message could not be read safely"
                    ),
                )
            parsed = ai_result.parsed
            parser_strategy = "ai"
            confidence = ai_result.extraction.transaction.confidence
            needs_review = True
            preview_token = create_ai_import_preview_token(
                user_id=g.current_user["user_id"],
                raw_message=raw_message,
                result=ai_result,
            )
            current_app.logger.info(
                "provider_import_ai_fallback request_id=%s "
                "format_signature=%s provider=%s needs_review=true",
                str(getattr(g, "request_id", "unavailable")),
                ai_result.format_signature,
                parsed.provider,
            )

        if isinstance(parsed, ParsedFulizaNotice):
            response = jsonify({
                "kind": "fuliza_notice",
                "importable": True,
                "provider": parsed.provider,
                "noticeType": parsed.notice_type.value,
                "amount": str(parsed.amount),
                "currency": parsed.currency,
                "financingFee": (
                    str(parsed.financing_fee)
                    if parsed.financing_fee is not None
                    else None
                ),
                "dailyMaintenanceFee": (
                    str(parsed.daily_maintenance_fee)
                    if parsed.daily_maintenance_fee is not None
                    else None
                ),
                "outstandingAmount": (
                    str(parsed.outstanding_amount)
                    if parsed.outstanding_amount is not None
                    else None
                ),
                "dueDate": (
                    parsed.due_date.isoformat()
                    if parsed.due_date is not None
                    else None
                ),
                "requiresDate": True,
                "message": (
                    "The financing event can be recorded. Principal is kept "
                    "separate from spending; only explicit fees affect expenses."
                ),
            })
            response.headers["Cache-Control"] = "private, no-store"
            return response, 200

        if not isinstance(parsed, ParsedTransactionMessage):
            abort(400, description="Unsupported financial message")
        importable = parsed.direction is not TransactionDirection.TRANSFER
        suggested_category = (
            "airtime"
            if parsed.provider_transaction_type
            in {"airtime", "airtime_topup", "data_bundle"}
            else None
        )
        response = jsonify({
            "kind": "transaction",
            "importable": importable,
            "provider": parsed.provider,
            "providerTransactionType": parsed.provider_transaction_type,
            "direction": parsed.direction.value,
            "amount": str(parsed.amount),
            "currency": parsed.currency,
            "occurredAt": (
                parsed.occurred_at.isoformat()
                if parsed.occurred_at is not None
                else None
            ),
            "requiresDate": parsed.occurred_at is None,
            "counterparty": parsed.counterparty,
            "fee": str(parsed.fee) if parsed.fee is not None else None,
            "paymentMethod": (
                payment_method_for_provider(parsed.provider)
                if importable
                else None
            ),
            "suggestedCategory": suggested_category,
            "parserStrategy": parser_strategy,
            "needsReview": needs_review,
            "confidence": confidence,
            "previewToken": preview_token,
            "message": (
                None
                if importable
                else "Cash withdrawals need account-to-account tracking first."
            ),
        })
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    @app.route("/api/transaction-imports", methods=["POST"])
    @login_required
    def create_transaction_import():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, description="Payload must be an object")

        raw_message = data.get("message")
        if not isinstance(raw_message, str) or not raw_message.strip():
            abort(400, description="A provider message is required")
        if len(raw_message) > 4000:
            abort(400, description="Provider message is too long")

        try:
            preview_token = data.get("previewToken")
            if preview_token is not None:
                parsed = load_ai_import_preview_token(
                    user_id=g.current_user["user_id"],
                    raw_message=raw_message,
                    token=preview_token,
                )
            else:
                parsed = parse_financial_message(raw_message)
            if not isinstance(parsed, ParsedTransactionMessage):
                raise TransactionMessageNotImportableError(
                    "Fuliza notices are informational and are not saved as transactions."
                )
            if parsed.direction is TransactionDirection.TRANSFER:
                raise TransactionMessageNotImportableError(
                    "Transfers need account-to-account tracking and cannot be imported yet."
                )

            validate_amount(parsed.amount)
            transaction_date = validate_date(
                parsed.occurred_at.date().isoformat()
                if parsed.occurred_at is not None
                else data.get("date")
            )
            description = validate_description(data.get("description"))
            if not description:
                abort(400, description="Describe what this transaction was for")
            category_name = validate_category(
                parsed.direction.value,
                data.get("category"),
            )
            remember_alias = data.get("rememberAlias")
            if remember_alias is not None:
                if not isinstance(remember_alias, str):
                    abort(400, description="Remembered alias must be text")
                remember_alias = " ".join(
                    remember_alias.strip().lower().split()
                )
                if not remember_alias:
                    remember_alias = None
                elif len(remember_alias) > 100:
                    abort(400, description="Remembered alias is too long")
            transaction, import_record = import_transaction_message_for_user(
                user_id=g.current_user["user_id"],
                raw_message=raw_message,
                parsed=parsed,
                transaction_date=transaction_date,
                description=description,
                category_name=category_name,
                remember_alias=remember_alias,
            )
        except UnsupportedFinancialMessageError as error:
            abort(400, description=str(error))
        except InvalidImportPreviewError as error:
            abort(400, description=str(error))
        except TransactionMessageNotImportableError as error:
            abort(400, description=str(error))
        except DuplicateTransactionImportError as error:
            return jsonify({
                "error": "Duplicate transaction import",
                "message": str(error),
                "transactionId": error.transaction_id,
            }), 409
        except ValidationError as error:
            abort(400, description=str(error))
        except HTTPException:
            raise

        response = jsonify({
            "data": transaction_to_dict(transaction),
            "import": {
                "provider": import_record.provider,
                "providerTransactionType": import_record.provider_transaction_type,
                "occurredAt": (
                    import_record.occurred_at.isoformat()
                    if import_record.occurred_at is not None
                    else None
                ),
                "fee": (
                    str(import_record.fee)
                    if import_record.fee is not None
                    else None
                ),
            },
            "status": "success",
            "rememberedAlias": remember_alias,
        })
        response.headers["Cache-Control"] = "private, no-store"
        return response, 201

    @app.route("/api/provider-financing-events", methods=["POST"])
    @login_required
    def create_provider_financing_event():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            abort(400, description="Payload must be an object")
        raw_message = data.get("message")
        if not isinstance(raw_message, str) or not raw_message.strip():
            abort(400, description="A financing provider message is required")
        if len(raw_message) > 4000:
            abort(400, description="Provider message is too long")

        try:
            parsed = parse_financial_message(raw_message)
            if not isinstance(parsed, ParsedFulizaNotice):
                abort(400, description="Message is not a supported financing notice")
            if not data.get("date"):
                abort(400, description="Financing notice date is required")
            recorded_on = validate_date(data["date"])
            event = record_financing_notice_for_user(
                g.current_user["user_id"],
                raw_message,
                parsed,
                recorded_on=recorded_on,
            )
        except UnsupportedFinancialMessageError as error:
            abort(400, description=str(error))
        except DuplicateFinancingEventError as error:
            return jsonify({
                "error": "Duplicate financing event",
                "message": str(error),
                "eventId": error.event_id,
            }), 409
        except ValidationError as error:
            abort(400, description=str(error))
        except HTTPException:
            raise

        response = jsonify({
            "data": {
                "id": event.id,
                "provider": event.provider,
                "eventType": event.event_type,
                "principalAmount": str(event.principal_amount),
                "financingFee": (
                    str(event.financing_fee)
                    if event.financing_fee is not None
                    else None
                ),
                "dailyMaintenanceFee": (
                    str(event.daily_maintenance_fee)
                    if event.daily_maintenance_fee is not None
                    else None
                ),
                "recordedOn": event.recorded_on.isoformat(),
            },
            "status": "success",
        })
        response.headers["Cache-Control"] = "private, no-store"
        return response, 201
       
    @app.route("/api/transactions/<int:transaction_id>", methods=["GET"])
    @login_required
    def get_transaction_by_id(transaction_id):
        user_id = g.current_user["user_id"]

        transaction = get_transaction_for_user(user_id, transaction_id)

        if not transaction:
            abort(404, description=f"Error!! Transaction with ID {transaction_id} not found")
        return jsonify(transaction_to_dict(transaction)), 200
        
    @app.route("/api/transactions", methods=["GET"])
    @login_required
    def get_transaction():    
        query = request.args.get("query")
        user_id = g.current_user["user_id"]

        transactions = list_transactions_for_user(user_id, query)

        return jsonify([
            transaction_to_dict(transaction)
            for transaction in transactions
        ]), 200

    @app.route("/api/budgets", methods=["GET"])
    @login_required
    def get_budgets():
        user_id = g.current_user["user_id"]
        budgets = get_budgets_for_user(user_id)
        response = jsonify([
            budget_to_dict(budget)
            for budget in budgets
        ])
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200

    def validate_budget_payload(data):
        if data is None:
            abort(400, description="Invalid JSON")

        if not isinstance(data, dict):
            abort(400, description="Payload must be an object")

        name = str(data.get("name", "")).strip()
        category = str(data.get("category", "General")).strip() or "General"
        items = data.get("items", [])

        if not name:
            abort(400, description="Budget name is required")

        try:
            target_amount = validate_amount(data.get("targetAmount"))
        except ValidationError as e:
            abort(400, description=str(e))

        if not isinstance(items, list) or not items:
            abort(400, description="At least one budget item is required")

        clean_items = []
        for item in items:
            if not isinstance(item, dict):
                abort(400, description="Each budget item must be an object")

            item_name = str(item.get("name", "")).strip()
            if not item_name:
                abort(400, description="Budget item name is required")

            try:
                estimated_amount = validate_amount(item.get("estimatedAmount", 0))
            except ValidationError as e:
                abort(400, description=str(e))

            clean_items.append({
                "name": item_name,
                "estimated_amount": estimated_amount,
                "checked": bool(item.get("checked", False)),
            })

        return name, category, target_amount, clean_items

    @app.route("/api/budgets", methods=["POST"])
    @login_required
    def create_budget():
        data = request.get_json()
        name, category, target_amount, clean_items = validate_budget_payload(data)

        budget = create_budget_for_user(
            user_id=g.current_user["user_id"],
            name=name,
            category=category,
            target_amount=target_amount,
            items=clean_items,
        )
        return jsonify({
            "data": budget_to_dict(budget),
            "status": "success",
        }), 201

    @app.route("/api/budgets/<int:budget_id>", methods=["PUT"])
    @login_required
    def update_budget(budget_id):
        data = request.get_json()
        name, category, target_amount, clean_items = validate_budget_payload(data)

        budget = update_budget_for_user(
            user_id=g.current_user["user_id"],
            budget_id=budget_id,
            name=name,
            category=category,
            target_amount=target_amount,
            items=clean_items,
        )
        if budget is None:
            abort(404, description="Budget not found")

        return jsonify({
            "data": budget_to_dict(budget),
            "status": "success",
        }), 200

    @app.route("/api/budgets/<int:budget_id>", methods=["DELETE"])
    @login_required
    def delete_budget(budget_id):
        deleted = delete_budget_for_user(
            g.current_user["user_id"],
            budget_id,
        )
        if not deleted:
            abort(404, description="Budget not found")

        return jsonify({"message": "Budget deleted", "status": "success"}), 200

    @app.route("/api/budget-items/<int:item_id>", methods=["PATCH"])
    @login_required
    def update_budget_item(item_id):
        data = request.get_json()
        if data is None:
            abort(400, description="Invalid JSON")

        if "checked" not in data or not isinstance(data["checked"], bool):
            abort(400, description="'checked' must be true or false")

        item = update_budget_item_checked_for_user(
            g.current_user["user_id"],
            item_id,
            data["checked"],
        )
        if item is None:
            abort(404, description="Budget item not found")

        return jsonify({
            "data": budget_item_to_dict(item),
            "status": "success",
        }), 200
        
    @app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
    @login_required
    def delete_transaction(transaction_id):
        deleted = soft_delete_transaction_for_user(
            user_id=g.current_user["user_id"],
            transaction_id=transaction_id,
        )

        if not deleted:
            abort(404, description="Transaction not found")
        
        return jsonify({"message": "deleted successfully"}), 200
            
    @app.route("/api/transactions/<int:transaction_id>", methods=["PUT"])
    @login_required
    def update_transaction(transaction_id):
        data = request.get_json()
        
        user_id = g.current_user["user_id"]
        if data is None:
            abort(400, description="Invalid JSON")
        
        if not isinstance(data, dict) or not data:
            abort(400, description="Request body is required")
        
        try:
            # Dictionary to hold validated updates
            amount = None
            transaction_date = None
            description = None
            transaction_type = None
            category_name = None
            payment_method_name = None
            merchant_name = None
            merchant_supplied = "merchant_name" in data
            
            # Validate each field if present
            if "amount" in data:
                amount = validate_amount(data["amount"])
            
            if "type" in data:
                transaction_type = validate_transaction_type(data["type"])
            
            if "category" in data:
                # If updating category, we need the type
                # Use the updated type if provided, otherwise require it
                if not transaction_type:
                    abort(400, description="Must provide 'type' when updating 'category'")
                category_name = validate_category(transaction_type, data["category"])
            
            if "date" in data:
                transaction_date = validate_date(data["date"])
            
            if "description" in data:
                description= validate_description(data["description"])
            
            if "payment_method" in data:
                payment_method_name = validate_payment_method(data["payment_method"])

            if merchant_supplied:
                merchant_name = data.get("merchant_name")


            transaction = update_transaction_for_user(
                user_id=user_id,
                transaction_id=transaction_id,
                amount=amount,
                transaction_date=transaction_date,
                description=description,
                category_name=category_name,
                transaction_type=transaction_type,
                payment_method_name=payment_method_name,
                merchant_name=merchant_name,
                merchant_supplied=merchant_supplied,
            )

            if transaction is None:
                abort(404, description="transaction not found")
            
            return jsonify({"data": transaction_to_dict(transaction), "message": "updated successfully", "status": "success"}), 200
            
        except ValidationError as e:
            abort(400, description=str(e))
        except ValueError as e:
            abort(400, description=str(e))
        except HTTPException:
            raise
        except Exception as e:
            abort(500, description=f"Server error: {str(e)}")

    @app.route(
        "/api/transactions/<int:transaction_id>/provider-fee",
        methods=["PATCH"],
    )
    @login_required
    def update_provider_fee(transaction_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or "fee" not in data:
            abort(400, description="Payload must contain fee")
        try:
            import_record = update_provider_fee_for_user(
                g.current_user["user_id"],
                transaction_id,
                data["fee"],
            )
        except ProviderFeeError as error:
            abort(400, description=str(error))
        if import_record is None:
            abort(404, description="Imported transaction not found")

        response = jsonify({
            "data": {
                "transactionId": import_record.transaction_id,
                "fee": str(import_record.fee),
                "feeSource": import_record.fee_source,
                "originalEstimatedFee": (
                    str(import_record.original_estimated_fee)
                    if import_record.original_estimated_fee is not None
                    else None
                ),
            },
            "status": "success",
        })
        response.headers["Cache-Control"] = "private, no-store"
        return response, 200
      
    @app.route("/admin/transactions", methods=["GET"])
    @login_required
    @admin_required         
    def admin_get_all_transactions():
        transactions = list_all_transactions()

        return jsonify([
            transaction_to_dict(transaction)
            for transaction in transactions
        ]), 200
    
    @app.route('/admin/users/<int:user_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def delete_user(user_id):
        """Deletes a user(cascades to their transactions)"""

        #Prevent self-deletion
        if user_id == g.current_user['user_id']:
            abort(400, description="Cannot delete yourself")
        
        #Check user in db
        user = get_user_by_id(user_id)

        #Validate
        if not user:
            return abort(404, description="User not found")
        
        #Get user id
        user_id = user.id

        delete_user_record(user)
        return jsonify({'message': f"User {user_id} deleted"}), 200        
