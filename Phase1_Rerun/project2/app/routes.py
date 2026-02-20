from flask import request, jsonify, abort
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
            abort(400, description="error!! Invalid JSON")
        
        if not isinstance(payload, dict):
            raise ValidationError("Payload must be an object")
        
        saved_record = storage.add(payload)
        if not saved_record:
            abort(500)
        return jsonify({"data": saved_record, "status": "success"}), 201
       
    @app.route("/transactions/<transaction_id>", methods=["GET"])
    def get_transaction_by_id(transaction_id):
        transaction = storage.get_by_id(transaction_id)
        if not transaction:
            abort(404, description=f"Error!! Transaction with ID {transaction_id} not found")
        return jsonify(transaction), 200
        
    @app.route("/transactions", methods=["GET"])
    def get_transaction():    
        query = request.args.get("query")
    
        if query:
            transactions = storage.search(query)
        else:
            transactions = storage.read_all()
        return jsonify(transactions), 200
        
    @app.route("/transactions/<transaction_id>", methods=["DELETE"])
    def delete_transaction(transaction_id):
        transaction = storage.delete(transaction_id)
        if not transaction:
            abort(404, description=f"Error!! Transaction with ID {transaction_id} not found")
        return jsonify({"message": "deleted successfully"}), 200
       
            
    @app.route("/transactions/<transaction_id>", methods=["PUT"])
    def update_transaction(transaction_id):
        data = request.get_json(force=True)
        print(f"DEBUG: PAssed JSON: {data}")
        if not data:
            abort(400, description=f"The {data} has not been found")
        
        field = data.get("field")
        updates = data.get("updates")
        if not field or updates is None:
            abort(400, description="error!! Both field and updates are required")
        transaction = storage.update(transaction_id, field, updates)
        if not transaction:
            abort(404, description=f"Error!! Transaction with ID {transaction_id} not found")      
        return jsonify({"message": "updated successfully"}), 200
      
         

