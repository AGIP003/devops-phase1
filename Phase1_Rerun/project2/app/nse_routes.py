from flask import Blueprint, abort, jsonify

from app.middleware import login_required
from app.services.nse_client import NseDataError
from app.services.nse_service import (
    NseUnavailableError,
    get_nse_stock,
    get_nse_stocks,
)


nse_bp = Blueprint("nse", __name__, url_prefix="/api/nse")


def _market_response(result, key):
    rows = result.payload if isinstance(result.payload, list) else [result.payload]
    currencies = sorted({
        row.get("currency")
        for row in rows
        if isinstance(row, dict) and row.get("currency")
    })
    response = jsonify({
        key: result.payload,
        "exchange": "NSE",
        "currencies": currencies,
        "source": {
            "name": "mystocks.africa",
            "url": "https://mystocks.africa/exchanges/nse-kenya",
            "license": "CC BY 4.0",
            "quoteType": "Delayed or end-of-day",
        },
        "sourceUpdatedAt": (
            result.source_updated_at.isoformat()
            if result.source_updated_at
            else None
        ),
        "fetchedAt": result.fetched_at.isoformat(),
        "stale": result.stale,
    })
    response.headers["Cache-Control"] = "private, max-age=60"
    return response, 200


@nse_bp.get("/stocks")
@login_required
def list_nse_stocks():
    try:
        result = get_nse_stocks()
    except NseUnavailableError:
        abort(503, description="NSE market data is temporarily unavailable")
    return _market_response(result, "stocks")


@nse_bp.get("/stocks/<string:symbol>")
@login_required
def get_nse_stock_detail(symbol):
    try:
        result = get_nse_stock(symbol)
    except NseDataError:
        abort(400, description="Invalid NSE security symbol")
    except NseUnavailableError:
        abort(503, description="NSE company data is temporarily unavailable")
    return _market_response(result, "stock")
