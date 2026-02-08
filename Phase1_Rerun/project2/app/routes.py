from flask import request, jsonify
from finance_tracker.utils.storage import Storage
from finance_tracker.utils.reports import generate_summary
from finance_tracker.utils.validations import validate_amount, validate_category, validate_date, validate_description, validate_payment_method,ValidationError, validate_transaction_type

# Instantiate storage for the web app
storage = Storage()

def validate_transaction(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be an object")
    
        

def register_routes(app):
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "Finance Tracker API", "endpoints": ["/transactions"]}), 200

    @app.route("/transactions", methods=["GET"])
    def get_transactions():
        try:
            data = storage.read_all()
            return jsonify(data), 200
        
        except Exception as e:
            app.logger.exception("Failed to load transactions")
            return jsonify(error="Internal server error"), 500
        
    @app.route("/transactions", methods=["POST"])
    def create_transaction_route():
        payload = request.get_json()

        if payload is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        if not isinstance(payload, dict):
            raise ValidationError("Payload must be an object")
        try: 
            
            #clean_data = {
            #    "date": payload.get("date", "").strip(),
            #    "description": payload.get("description", "").strip().lower(),
            #    "type": payload.get("type", "").strip().lower(),
            #    "category": payload.get("category", "").strip().lower(),
            #    "amount": payload.get("amount", ""),
            #    "payment method": payload.get("payment method", "").strip().lower()
            #}
            saved_record = storage.add(payload)
            if not saved_record:
                return jsonify({"error": "Failed to save transaction"}), 500
            return jsonify({"data": saved_record, "status": "success"}), 201
       
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        
        except Exception as e:
            app.logger.exception("Failed to create transction")
            return jsonify({"error": "Server Error"})
        
    @app.route("/transactions/<transactions_id>", methods=["GET"])
    def get_transaction_by_id(transactions_id):
        try:
            data = storage.read_all()
            record = data.get(transactions_id)
            if not record:
                return jsonify({"error": "Transaction not found"}), 404
            return jsonify(record), 200
        except Exception:
            app.logger.exception("Failed to retrieve transaction")
            return jsonify({"error": "Server Error"}), 500


