import os

from flask import request, jsonify, abort, g
from werkzeug.exceptions import HTTPException

from app.middleware import login_required, admin_required
from app.serializers import (
    budget_item_to_dict,
    budget_to_dict,
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
from app.services.user_service import delete_user as delete_user_record, get_user_by_id
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
            payment_method_name = validate_payment_method(data.get("payment_method"))
            
            try:
                user_id = g.current_user["user_id"]
                saved_transaction = create_transaction_for_user(user_id, category_name, transaction_type, payment_method_name, amount, transaction_date, description)
            except ValueError as e:
                abort(400, description=str(e))

            return jsonify({"data": transaction_to_dict(saved_transaction), "status": "success"}), 201
            
        except ValidationError as e:
            abort(400, description=str(e))
        except HTTPException:
            raise
        except Exception as e:
            abort(500, description=f"Server error: {str(e)}")
       
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


            transaction = update_transaction_for_user(
                user_id=user_id,
                transaction_id=transaction_id,
                amount=amount,
                transaction_date=transaction_date,
                description=description,
                category_name=category_name,
                transaction_type=transaction_type,
                payment_method_name=payment_method_name,
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
