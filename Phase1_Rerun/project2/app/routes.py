from flask import request, jsonify
from finance_tracker.utils.storage import Storage
from finance_tracker.utils.reports import generate_summary
from finance_tracker.utils.validations import validate_amount, validate_category, validate_date, validate_description, validate_payment_method,ValidationError, validate_transaction_type

# Instantiate storage for the web app
storage = Storage()

def register_routes(app):
    
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "Finance Tracker API", "endpoints": ["/transactions"]}), 200
        
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
        
    @app.route("/transactions/<transaction_id>", methods=["GET"])
    def get_transaction_by_id(transaction_id):
        try:
            transaction = storage.get_by_id(transaction_id)
            if not transaction:
                return({"error": "Transaction not found"}), 404
            return jsonify(transaction), 200
        
        except Exception as e:
            app.logger.exception("Failed to retrieve transaction")
            return jsonify({"error": "Server Error"}), 500
        
    @app.route("/transactions", methods=["GET"])
    def get_transaction():
        try:    
            query = request.args.get("query")
        
            if query:
                transactions = storage.search(query)
            else:
                transactions = storage.read_all()
            return jsonify(transactions), 200
        
        except Exception as e:
            app.logger.exception("Failed to search transaction")
            return jsonify({"Error": "Server Error"}), 500
        
    @app.route("/transactions/<transaction_id>", methods=["DELETE"])
    def delete_transaction(transaction_id):
        try:
            transaction = storage.delete(transaction_id)
            if not transaction:
                return jsonify({"error": "Transaction not found"}), 404      
            return jsonify({"message": "deleted successfully"}), 200
        except Exception as e:
            app.logger.exception("Failed to delete transaction")
            return jsonify({"error": "Server Error"}), 500
            
    @app.route("/transactions/<transaction_id>", methods=["PUT"])
    def update_transaction(transaction_id):
        print(f"UPDATE: Raw request data: {request.data}")
        print(f"DEBUG: CONTENT-TYPE: {request.content_type}")
        try:
            data = request.get_json(force=True)
            print(f"DEBUG: PAssed JSON: {data}")
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            field = data.get("field")
            updates = data.get("updates")
            if not field or updates is None:
                return jsonify({"error": "Both field and updates are required"}), 400
            transaction = storage.update(transaction_id, field, updates)

            if not transaction:
                return jsonify({"error": "Transaction not found"}), 404      
            return jsonify({"message": "updated successfully"}), 200
        except Exception as e:
            app.logger.exception("Failed to update transaction")
            return jsonify({"error": "Server Error"}), 500
         

        