"""
JWT Authentication Module
Handles JWT token generation, validation, and route protection
"""

from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import timedelta

from src.models.base import get_db_session
from src.models.user import User, UserRole
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_tokens(user):
    """
    Create access and refresh tokens for a user

    Args:
        user: User object

    Returns:
        dict with access_token and refresh_token
    """
    additional_claims = {
        'role': user.role.value if isinstance(user.role, UserRole) else user.role,
        'email': user.email
    }

    access_token = create_access_token(
        identity=user.id,
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=1)
    )

    refresh_token = create_refresh_token(
        identity=user.id,
        additional_claims={'role': additional_claims['role']},
        expires_delta=timedelta(days=30)
    )

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 3600  # 1 hour in seconds
    }


def get_current_user():
    """
    Get the current authenticated user from JWT token

    Returns:
        User object or None
    """
    try:
        user_id = get_jwt_identity()
        session = get_db_session()
        user = session.query(User).filter_by(id=user_id).first()
        session.close()
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


def role_required(*allowed_roles):
    """
    Decorator to require specific user roles for route access

    Args:
        *allowed_roles: UserRole enum values or role strings

    Usage:
        @role_required(UserRole.ADMIN, UserRole.RESEARCHER)
        def admin_only_route():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')

            # Convert allowed_roles to strings for comparison
            allowed_role_strings = [
                role.value if isinstance(role, UserRole) else role
                for role in allowed_roles
            ]

            if user_role not in allowed_role_strings:
                return jsonify({
                    'status': 'error',
                    'error_code': 'INSUFFICIENT_PERMISSIONS',
                    'error_message': f'Required role: {", ".join(allowed_role_strings)}. Your role: {user_role}'
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """
    Decorator to require admin role

    Usage:
        @admin_required
        def admin_route():
            pass
    """
    return role_required(UserRole.ADMIN)(fn)


def active_user_required(fn):
    """
    Decorator to ensure user account is active

    Usage:
        @active_user_required
        def protected_route():
            pass
    """
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if not user:
            return jsonify({
                'status': 'error',
                'error_code': 'USER_NOT_FOUND',
                'error_message': 'User account not found'
            }), 404

        if not user.is_active:
            return jsonify({
                'status': 'error',
                'error_code': 'ACCOUNT_DISABLED',
                'error_message': 'User account is disabled'
            }), 403

        return fn(*args, **kwargs)
    return wrapper


def verified_user_required(fn):
    """
    Decorator to require verified user account

    Usage:
        @verified_user_required
        def verified_only_route():
            pass
    """
    @wraps(fn)
    @active_user_required
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if not user.is_verified:
            return jsonify({
                'status': 'error',
                'error_code': 'ACCOUNT_NOT_VERIFIED',
                'error_message': 'User account email not verified'
            }), 403

        return fn(*args, **kwargs)
    return wrapper


def get_user_from_token():
    """
    Helper to get user object from current JWT token

    Returns:
        User object or None
    """
    return get_current_user()
