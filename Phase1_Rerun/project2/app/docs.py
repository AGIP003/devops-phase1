from flask_restx import Api, Namespace, Resource, fields

#Api object - for generating the Swagger UI at /api/docs
api = Api(
    title='Moneytiqx API',
    version='1.0',
    description='Finance Tracker API - authentication, transactions, admin',
    doc='/api/docs', # Where swagger lives
    prefix='/api', # all namespaces are prefixed with /api
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Bearer {token}"'
        }
    },
    security='Bearer'
)

# NAMESPACES
auth_ns = Namespace('auth', description='Authentication - register, login, password reset')
transactions_ns = Namespace('transactions', description='Transactions CRUD operations')

# MODELS (request/response shapes)
user_model = auth_ns.model('UserData', {
    'user_id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='User email address'),
    'role': fields.String(description='User role'),
})

token_response = auth_ns.model('TokenResponse', {
    'message': fields.String(required=True, description='Status message'),
    'token': fields.String(required=True, description='JWT token'),
    'user': fields.Nested(user_model),
})

register_model = auth_ns.model('RegisterRequest', {
    'username': fields.String(required=True, description='Chosen username'),
    'email': fields.String(required=True, description='User email address'),
    'password': fields.String(required=True, description='Min 8 chars, uppercase, number'),
})

login_model = auth_ns.model('LoginRequest', {
    'email': fields.String(required=True, description='Registered email'),
    'password': fields.String(required=True, description='Account password'),
})

password_reset_request_model = auth_ns.model('PasswordResetRequest', {
    'email': fields.String(required=True, description='Registered email'),
})

password_reset_verify_model = auth_ns.model('PasswordResetVerifyRequest', {
    'token': fields.String(required=True, description='Password reset token'),
    'new_password': fields.String(required=True, description='New password'),
})

transaction_response = transactions_ns.model('TransactionResponse', {
    'id': fields.Integer(description='Transaction ID'),
    'user_id': fields.Integer(description='User ID'),
    'category_id': fields.Integer(description='Category ID'),
    'payment_method_id': fields.Integer(description='Payment method ID'),
    'amount': fields.Float(description='Transaction amount'),
    'date': fields.String(description='Transaction date'),
    'description': fields.String(description='Transaction description'),
})

transaction_input = transactions_ns.model('TransactionInput', {
    'description': fields.String(required=True, description='What this transaction was for'),
    'amount': fields.Float(required=True, description='Amount in KES'),
    'type': fields.String(required=True, description='income or expense'),
    'category': fields.String(required=True, description='Category name'),
    'date': fields.String(required=True, description='YYYY-MM-DD format'),
    'payment_method': fields.String(required=True, description='e.g. m-pesa, cash, bank transfer'),
})

# DOCUMENTATION-ONLY RESOURCE CLASSES
#Describes the existing routes does not replace them
@auth_ns.route('/register')
class RegisterDoc(Resource):
    @auth_ns.expect(register_model)
    @auth_ns.response(201, 'User created successfully', token_response)
    @auth_ns.response(409, 'Email already registered')
    @auth_ns.response(400, 'Validation error')
    def post(self):
        """Register a new user account"""
        pass  # real logic is in auth_routes.py

@auth_ns.route('/login')
class LoginDoc(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful', token_response)
    @auth_ns.response(401, 'Invalid credentials')
    @auth_ns.response(429, 'Too many attempts — rate limited')
    def post(self):
        """Login and receive a JWT token"""
        pass

@auth_ns.route('/password_reset_request')
class PasswordResetRequestDoc(Resource):
    @auth_ns.expect(password_reset_request_model)
    @auth_ns.response(200, 'Reset email sent if account exists')
    @auth_ns.response(429, 'Rate limited')
    def post(self):
        """Request a password reset email"""
        pass

@auth_ns.route('/password-reset-verify')
class PasswordResetVerifyDoc(Resource):
    @auth_ns.expect(password_reset_verify_model)
    @auth_ns.response(200, 'Password reset successfully')
    @auth_ns.response(400, 'Invalid token or validation error')
    def post(self):
        """Verify password reset token and set a new password"""
        pass

@transactions_ns.route('')
class TransactionListDoc(Resource):
    @transactions_ns.response(200, 'List of transactions', [transaction_response])
    @transactions_ns.response(401, 'Missing or invalid token')
    def get(self):
        """Get all transactions for the authenticated user — requires Bearer token"""
        pass

    @transactions_ns.expect(transaction_input)
    @transactions_ns.response(201, 'Transaction created', transaction_response)
    @transactions_ns.response(400, 'Validation error')
    @transactions_ns.response(401, 'Unauthorized')
    def post(self):
        """Create a new transaction — requires Bearer token"""
        pass

@transactions_ns.route('/<int:id>')
class TransactionDetailDoc(Resource):
    @transactions_ns.response(200, 'Transaction detail', transaction_response)
    @transactions_ns.response(403, 'Not your transaction')
    @transactions_ns.response(404, 'Transaction not found')
    def get(self, id):
        """Get a single transaction by ID"""
        pass

    @transactions_ns.expect(transaction_input)
    @transactions_ns.response(200, 'Transaction updated', transaction_response)
    @transactions_ns.response(403, 'Not your transaction')
    def put(self, id):
        """Update a transaction — must own it"""
        pass

    @transactions_ns.response(200, 'Transaction deleted')
    @transactions_ns.response(403, 'Not your transaction')
    def delete(self, id):
        """Delete a transaction — must own it"""
        pass

# Register namespaces onto the Api object
api.add_namespace(auth_ns, path='/auth')
api.add_namespace(transactions_ns, path='/transactions')