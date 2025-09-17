import hashlib
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from config import JWT_SECRET_KEY, JWT_EXPIRATION_HOURS, USER_ROLES
from utils.file_ops import find_user_by_id, update_user

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password

def generate_jwt_token(user_data):
    """Generate a JWT token for a user"""
    try:
        payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'role': user_data['role'],
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        
        # Update user's last login
        update_user(user_data['id'], {'last_login': datetime.now().isoformat()})
        
        return token
    except Exception as e:
        print(f"Error generating JWT token: {e}")
        return None

def decode_jwt_token(token):
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

def get_current_user_from_token():
    """Extract current user from JWT token in request headers"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = decode_jwt_token(token)
        
        if isinstance(payload, tuple):  # Error case
            return None
        
        # Get full user data
        user = find_user_by_id(payload['user_id'])
        if not user or not user.get('active', True):
            return None
        
        return user
    except Exception as e:
        print(f"Error getting current user from token: {e}")
        return None

def has_permission(user, permission):
    """Check if a user has a specific permission"""
    if not user or not user.get('active', True):
        return False
    
    user_role = user.get('role')
    if not user_role or user_role not in USER_ROLES:
        return False
    
    role_permissions = USER_ROLES[user_role]['permissions']
    
    # Super admin has all permissions
    if '*' in role_permissions:
        return True
    
    return permission in role_permissions

def require_permission(permission):
    """Decorator to require a specific permission for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user_from_token()
            
            if not user:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
            if not has_permission(user, permission):
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
            
            # Add user to request context
            request.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_auth():
    """Decorator to require authentication for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user_from_token()
            
            if not user:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
            # Add user to request context
            request.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_role(required_role):
    """Decorator to require a specific role for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user_from_token()
            
            if not user:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
            if user.get('role') != required_role:
                return jsonify({'success': False, 'message': f'Role {required_role} required'}), 403
            
            # Add user to request context
            request.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_user_permissions(user):
    """Get all permissions for a user"""
    if not user or not user.get('active', True):
        return []
    
    user_role = user.get('role')
    if not user_role or user_role not in USER_ROLES:
        return []
    
    role_permissions = USER_ROLES[user_role]['permissions']
    
    # Super admin has all permissions
    if '*' in role_permissions:
        all_permissions = set()
        for role_data in USER_ROLES.values():
            if role_data['permissions'] != ['*']:
                all_permissions.update(role_data['permissions'])
        return list(all_permissions)
    
    return role_permissions

def validate_user_data(user_data, is_update=False):
    """Validate user data for creation or update"""
    errors = []
    
    # Required fields for creation
    if not is_update:
        required_fields = ['username', 'password', 'role', 'full_name', 'email']
        for field in required_fields:
            if not user_data.get(field, '').strip():
                errors.append(f"{field} is required")
    
    # Validate role
    if 'role' in user_data and user_data['role'] not in USER_ROLES:
        errors.append(f"Invalid role. Must be one of: {', '.join(USER_ROLES.keys())}")
    
    # Validate email format
    if 'email' in user_data and user_data['email']:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, user_data['email']):
            errors.append("Invalid email format")
    
    # Validate username uniqueness (if creating or changing username)
    if 'username' in user_data and user_data['username']:
        from utils.file_ops import find_user_by_username
        existing_user = find_user_by_username(user_data['username'])
        if existing_user and (not is_update or existing_user['id'] != user_data.get('id')):
            errors.append("Username already exists")
    
    return errors 