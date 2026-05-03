"""
Authentication Routes
Handles user registration, login, token refresh, and profile management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
import re

from src.models.base import get_db_session
from src.models.user import User, UserRole
from src.api.auth import create_tokens, get_current_user, admin_required
from src.utils.logger import get_logger, get_audit_logger

logger = get_logger(__name__)
audit_logger = get_audit_logger()

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

class UserRegister(BaseModel):
    """User registration schema"""
    username: str
    email: EmailStr
    password: str
    role: str = 'viewer'

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['admin', 'researcher', 'data_scientist', 'viewer']
        if v.lower() not in valid_roles:
            raise ValueError(f'Invalid role. Must be one of: {", ".join(valid_roles)}')
        return v.lower()


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str


class PasswordChange(BaseModel):
    """Password change schema"""
    old_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account"""
    try:
        data = request.get_json()
        validated = UserRegister(**data)

        session = get_db_session()

        # Check if username already exists
        existing_user = session.query(User).filter_by(username=validated.username).first()
        if existing_user:
            session.close()
            return jsonify({
                'status': 'error',
                'error_code': 'USERNAME_EXISTS',
                'error_message': 'Username already taken'
            }), 409

        # Check if email already exists
        existing_email = session.query(User).filter_by(email=validated.email).first()
        if existing_email:
            session.close()
            return jsonify({
                'status': 'error',
                'error_code': 'EMAIL_EXISTS',
                'error_message': 'Email already registered'
            }), 409

        # Create new user
        role_enum = UserRole[validated.role.upper()]
        user = User(
            username=validated.username,
            email=validated.email,
            password=validated.password,
            role=role_enum,
            is_active=True,
            is_verified=False  # Require email verification
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        # Audit log
        audit_logger.log_user_action(
            user_id=user.id,
            action='user_registered',
            details={'username': user.username, 'email': user.email}
        )

        logger.info(f"New user registered: {user.username} ({user.email})")

        user_dict = user.to_dict()
        session.close()

        return jsonify({
            'status': 'success',
            'message': 'User registered successfully. Please verify your email.',
            'data': {
                'user': user_dict
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 201

    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error_code': 'VALIDATION_ERROR',
            'error_message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error during registration: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'REGISTRATION_ERROR',
            'error_message': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = request.get_json()
        validated = UserLogin(**data)

        session = get_db_session()

        # Find user
        user = session.query(User).filter_by(username=validated.username).first()

        if not user or not user.check_password(validated.password):
            session.close()
            return jsonify({
                'status': 'error',
                'error_code': 'INVALID_CREDENTIALS',
                'error_message': 'Invalid username or password'
            }), 401

        if not user.is_active:
            session.close()
            return jsonify({
                'status': 'error',
                'error_code': 'ACCOUNT_DISABLED',
                'error_message': 'Account is disabled'
            }), 403

        # Update last login
        user.update_last_login()
        session.commit()

        # Create tokens
        tokens = create_tokens(user)

        # Audit log
        audit_logger.log_user_action(
            user_id=user.id,
            action='user_login',
            details={'username': user.username}
        )

        logger.info(f"User logged in: {user.username}")

        user_dict = user.to_dict()
        session.close()

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user': user_dict,
                'tokens': tokens
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'LOGIN_ERROR',
            'error_message': str(e)
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        user_id = get_jwt_identity()

        session = get_db_session()
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            session.close()
            return jsonify({
                'status': 'error',
                'error_code': 'USER_NOT_FOUND',
                'error_message': 'User not found'
            }), 404

        if not user.is_active:
            session.close()
            return jsonify({
                'status': 'error',
                'error_code': 'ACCOUNT_DISABLED',
                'error_message': 'Account is disabled'
            }), 403

        # Create new tokens
        tokens = create_tokens(user)
        session.close()

        return jsonify({
            'status': 'success',
            'message': 'Token refreshed successfully',
            'data': {
                'tokens': tokens
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'TOKEN_REFRESH_ERROR',
            'error_message': str(e)
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user = get_current_user()

        if not user:
            return jsonify({
                'status': 'error',
                'error_code': 'USER_NOT_FOUND',
                'error_message': 'User not found'
            }), 404

        return jsonify({
            'status': 'success',
            'data': {
                'user': user.to_dict()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'PROFILE_ERROR',
            'error_message': str(e)
        }), 500


@auth_bp.route('/me/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        validated = PasswordChange(**data)

        user = get_current_user()

        if not user:
            return jsonify({
                'status': 'error',
                'error_code': 'USER_NOT_FOUND',
                'error_message': 'User not found'
            }), 404

        # Verify old password
        if not user.check_password(validated.old_password):
            return jsonify({
                'status': 'error',
                'error_code': 'INVALID_PASSWORD',
                'error_message': 'Current password is incorrect'
            }), 401

        # Update password
        session = get_db_session()
        db_user = session.query(User).filter_by(id=user.id).first()
        db_user.set_password(validated.new_password)
        session.commit()
        session.close()

        # Audit log
        audit_logger.log_user_action(
            user_id=user.id,
            action='password_changed',
            details={'username': user.username}
        )

        logger.info(f"Password changed for user: {user.username}")

        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error_code': 'VALIDATION_ERROR',
            'error_message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error changing password: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'PASSWORD_CHANGE_ERROR',
            'error_message': str(e)
        }), 500


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (admin only)"""
    try:
        session = get_db_session()
        users = session.query(User).all()

        users_data = [user.to_dict() for user in users]
        session.close()

        return jsonify({
            'status': 'success',
            'data': {
                'users': users_data,
                'total': len(users_data)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'LIST_USERS_ERROR',
            'error_message': str(e)
        }), 500


@auth_bp.route('/users/<user_id>/deactivate', methods=['PUT'])
@admin_required
def deactivate_user(user_id):
    """Deactivate a user account (admin only)"""
    try:
        session = get_db_session()
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            session.close()
            return jsonify({
                'status': 'error',
                'error_code': 'USER_NOT_FOUND',
                'error_message': 'User not found'
            }), 404

        user.is_active = False
        session.commit()

        # Audit log
        current_user = get_current_user()
        audit_logger.log_user_action(
            user_id=current_user.id,
            action='user_deactivated',
            details={'target_user_id': user_id, 'target_username': user.username}
        )

        logger.info(f"User deactivated: {user.username} by {current_user.username}")

        user_dict = user.to_dict()
        session.close()

        return jsonify({
            'status': 'success',
            'message': 'User deactivated successfully',
            'data': {'user': user_dict},
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error deactivating user: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error_code': 'DEACTIVATE_ERROR',
            'error_message': str(e)
        }), 500


def register_auth_routes(app):
    """Register authentication routes to the Flask app"""
    app.register_blueprint(auth_bp)
    logger.info("Authentication routes registered successfully")
