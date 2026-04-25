from flask import request, jsonify, abort, g
from finance_tracker.utils.validations import (
    validate_amount, validate_category, validate_date, validate_description, 
    validate_payment_method, ValidationError, validate_transaction_type
)
from app.db import (
    create_transactions, get_all_transactions, search_transactions, get_db_connection,  
    db_get_transaction_by_id, update_transactions, delete_transactions,
    get_payment_method_id, get_category_id
)
from app.middleware import login_required

def register_routes(app):
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "Finance Tracker API", "endpoints": ["/transactions"]}), 200
        
    @app.route("/transactions", methods=["POST"])
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
            txn_type = validate_transaction_type(data.get("type"))
            
            # Then validate category (depends on type)
            category_name = validate_category(txn_type, data.get("category"))
            
            # Validate other fields
            amount = validate_amount(data.get("amount"))
            date = validate_date(data.get("date"))
            description = validate_description(data.get("description", ""))
            payment_method = validate_payment_method(data.get("payment_method"))
            
            # Now lookup the IDs from database
            try:
                category_id = get_category_id(category_name)
                payment_method_id = get_payment_method_id(payment_method)
            except ValueError as e:
                abort(400, description=str(e))
            
            # database record 
            db_data = {
                "user_id": 4,  
                "category_id": category_id,
                "payment_method_id": payment_method_id,
                "amount": amount,
                "date": date,
                "description": description,
                "type": txn_type
            }
            saved_record = create_transactions(db_data)
            return jsonify({"data": saved_record, "status": "success"}), 201
            
        except ValidationError as e:
            abort(400, description=str(e))
        except Exception as e:
            abort(500, description=f"Server error: {str(e)}")
       
    @app.route("/transactions/<transaction_id>", methods=["GET"])
    def get_transaction_by_id(transaction_id):
        transaction = db_get_transaction_by_id(transaction_id)
        if not transaction:
            abort(404, description=f"Error!! Transaction with ID {transaction_id} not found")
        return jsonify(transaction), 200
        
    @app.route("/transactions", methods=["GET", "OPTIONS"])
    def get_transaction():    
        query = request.args.get("query")
    
        if query:
            transactions = search_transactions(query)
        else:
            transactions = get_all_transactions()
        return jsonify(transactions), 200
        
    @app.route("/transactions/<transaction_id>", methods=["DELETE"])
    def delete_transaction(transaction_id):
        transaction = delete_transactions(transaction_id)
        if not transaction:
            abort(404, description=f"Error!! Transaction with ID {transaction_id} not found")
        return jsonify({"message": "deleted successfully"}), 200
       
            
    @app.route("/transactions/<transaction_id>", methods=["PUT"])
    def update_transaction(transaction_id):
        data = request.get_json()
        
        if data is None:
            abort(400, description="Invalid JSON")
        
        if not isinstance(data, dict) or not data:
            abort(400, description="Request body is required")
        
        try:
            # Dictionary to hold validated updates
            validated_updates = {}
            
            # Validate each field if present
            if "amount" in data:
                validated_updates["amount"] = validate_amount(data["amount"])
            
            if "type" in data:
                validated_updates["type"] = validate_transaction_type(data["type"])
            
            if "category" in data:
                # If updating category, we need the type
                # Use the updated type if provided, otherwise require it
                txn_type = validated_updates.get("type")
                if not txn_type:
                    abort(400, description="Must provide 'type' when updating 'category'")
                validated_category = validate_category(txn_type, data["category"])
                category_id = get_category_id(validated_category)
                validated_updates["category_id"] = category_id
            
            if "date" in data:
                validated_updates["date"] = validate_date(data["date"])
            
            if "description" in data:
                validated_updates["description"] = validate_description(data["description"])
            
            if "payment_method" in data:
                validated_payment = validate_payment_method(data["payment_method"])
                payment_method_id = get_payment_method_id(validated_payment)
                validated_updates["payment_method_id"] = payment_method_id
            
            if not validated_updates:
                abort(400, description="No valid fields to update")
            
            row, error = update_transactions(transaction_id, validated_updates)
            if error:
                abort(400, description=error)
            
            return jsonify({"data": row, "message": "updated successfully", "status": "success"}), 200
            
        except ValidationError as e:
            abort(400, description=str(e))
        except ValueError as e:
            abort(400, description=str(e))
        except Exception as e:
            abort(500, description=f"Server error: {str(e)}")
      
         

