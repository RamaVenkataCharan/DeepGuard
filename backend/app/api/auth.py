"""
Authentication and RBAC API Blueprint.
Handles logins, token refresh, and registration.
"""
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from marshmallow import Schema, fields
from app.models.user import User
from app.extensions import db

# Define blueprint
auth_blp = Blueprint("auth", "auth", url_prefix="/api/auth", description="Authentication operations")

# Validation schemas
class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)
    full_name = fields.String(required=True)
    role = fields.String(required=True)

class TokenResponseSchema(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    user = fields.Dict()

@auth_blp.route("/login")
class LoginView(MethodView):
    
    @auth_blp.arguments(LoginSchema)
    @auth_blp.response(200, TokenResponseSchema)
    def post(self, login_data):
        """Authenticates user credentials and returns access/refresh tokens."""
        user = User.query.filter_by(email=login_data["email"]).first()
        if not user or not user.check_password(login_data["password"]):
            abort(401, message="Invalid email or password.")
            
        if not user.is_active:
            abort(403, message="This user account has been deactivated.")
            
        access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict()
        }

@auth_blp.route("/register")
class RegisterView(MethodView):
    
    @auth_blp.arguments(RegisterSchema)
    @jwt_required()
    def post(self, register_data):
        """Creates a new dashboard user account (Admin only)."""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role != "admin":
            abort(403, message="Admin privileges required for user registration.")
            
        if User.query.filter_by(email=register_data["email"]).first():
            abort(400, message="A user with that email already exists.")
            
        new_user = User(
            email=register_data["email"],
            full_name=register_data["full_name"],
            role=register_data["role"]
        )
        new_user.set_password(register_data["password"])
        
        db.session.add(new_user)
        db.session.commit()
        
        return {"message": "User registered successfully.", "user": new_user.to_dict()}, 201

@auth_blp.route("/refresh")
class RefreshView(MethodView):
    
    @jwt_required(refresh=True)
    def post(self):
        """Rotates expired access tokens using a valid refresh token."""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_active:
            abort(401, message="User not found or deactivated.")
            
        new_access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"access_token": new_access_token}, 200

@auth_blp.route("/me")
class MeView(MethodView):
    
    @jwt_required()
    def get(self):
        """Returns the profile object of the currently authenticated session."""
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        return user.to_dict(), 200
