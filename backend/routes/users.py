from flask import Blueprint, jsonify, request
from datetime import datetime
from utils.auth import (
    verify_password, hash_password, generate_jwt_token, 
    require_permission, require_auth, get_user_permissions,
    validate_user_data, get_current_user_from_token
)
from utils.file_ops import (
    load_users, save_users, find_user_by_username, find_user_by_id,
    create_user, update_user, delete_user
)
from config import USER_ROLES, ADMIN_USERNAME, ADMIN_PASSWORD

users_bp = Blueprint('users', __name__)

@users_bp.route("/auth/login", methods=["POST"])
def login():
    """User authentication endpoint"""
    try:
        data = request.json
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"success": False, "message": "Username and password required"}), 400
        
        username = data["username"]
        password = data["password"]
        
        # First try to find user in new user system
        user = find_user_by_username(username)
        
        if user:
            # New user system authentication
            if not user.get('active', True):
                return jsonify({"success": False, "message": "Account is deactivated"}), 401
            
            if verify_password(password, user['password']):
                token = generate_jwt_token(user)
                if token:
                    # Return user info without password
                    user_response = {k: v for k, v in user.items() if k != 'password'}
                    user_response['permissions'] = get_user_permissions(user)
                    
                    return jsonify({
                        "success": True, 
                        "message": "Authentication successful",
                        "token": token,
                        "user": user_response
                    })
                else:
                    return jsonify({"success": False, "message": "Error generating authentication token"}), 500
            else:
                return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
        # Fallback to legacy admin credentials for migration
        elif username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Create a temporary admin user object for legacy support
            legacy_admin = {
                "id": "legacy_admin",
                "username": username,
                "role": "super_admin",
                "full_name": "Legacy Admin",
                "email": "admin@example.com",
                "active": True
            }
            
            token = generate_jwt_token(legacy_admin)
            if token:
                legacy_admin['permissions'] = get_user_permissions(legacy_admin)
                return jsonify({
                    "success": True, 
                    "message": "Authentication successful (Legacy Mode)",
                    "token": token,
                    "user": legacy_admin,
                    "legacy_mode": True
                })
            else:
                return jsonify({"success": False, "message": "Error generating authentication token"}), 500
        
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "message": f"Authentication error: {str(e)}"}), 500

@users_bp.route("/auth/verify", methods=["GET"])
@require_auth()
def verify_token():
    """Verify authentication token and return user info"""
    try:
        user = request.current_user
        
        # Return user info without password
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['permissions'] = get_user_permissions(user)
        
        return jsonify({
            "success": True,
            "user": user_response
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Token verification error: {str(e)}"}), 500

@users_bp.route("/users", methods=["GET"])
@require_permission("view_users")
def get_users():
    """Get all users (requires user management permission)"""
    try:
        users = load_users()
        
        # Remove passwords from response
        users_response = []
        for user in users:
            user_data = {k: v for k, v in user.items() if k != 'password'}
            user_data['role_name'] = USER_ROLES.get(user.get('role'), {}).get('name', 'Unknown')
            users_response.append(user_data)
        
        return jsonify({"success": True, "users": users_response})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving users: {str(e)}"}), 500

@users_bp.route("/users", methods=["POST"])
@require_permission("manage_users")
def create_new_user():
    """Create a new user (requires user management permission)"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No user data provided"}), 400
        
        # Validate user data
        errors = validate_user_data(data)
        if errors:
            return jsonify({"success": False, "message": "Validation errors", "errors": errors}), 400
        
        # Hash password
        data['password'] = hash_password(data['password'])
        data['active'] = data.get('active', True)
        data['created_by'] = request.current_user['id']
        
        # Create user
        new_user = create_user(data)
        if new_user:
            # Return user info without password and _id
            user_response = {k: v for k, v in new_user.items() if k not in ['password', '_id']}
            user_response['role_name'] = USER_ROLES.get(new_user.get('role'), {}).get('name', 'Unknown')
            
            return jsonify({
                "success": True, 
                "message": "User created successfully",
                "user": user_response
            })
        else:
            return jsonify({"success": False, "message": "Error creating user"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error creating user: {str(e)}"}), 500

@users_bp.route("/users/<user_id>", methods=["PUT"])
@require_permission("manage_users")
def update_existing_user(user_id):
    """Update an existing user (requires user management permission)"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No update data provided"}), 400
        
        # Check if user exists
        existing_user = find_user_by_id(user_id)
        if not existing_user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Validate update data
        data['id'] = user_id  # For validation
        errors = validate_user_data(data, is_update=True)
        if errors:
            return jsonify({"success": False, "message": "Validation errors", "errors": errors}), 400
        
        # Hash password if provided
        if 'password' in data and data['password']:
            data['password'] = hash_password(data['password'])
        else:
            # Remove password from update if not provided
            data.pop('password', None)
        
        data['updated_by'] = request.current_user['id']
        
        # Update user
        updated_user = update_user(user_id, data)
        if updated_user:
            # Return user info without password and _id
            user_response = {k: v for k, v in updated_user.items() if k not in ['password', '_id']}
            user_response['role_name'] = USER_ROLES.get(updated_user.get('role'), {}).get('name', 'Unknown')
            
            return jsonify({
                "success": True, 
                "message": "User updated successfully",
                "user": user_response
            })
        else:
            return jsonify({"success": False, "message": "Error updating user"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error updating user: {str(e)}"}), 500

@users_bp.route("/users/<user_id>", methods=["DELETE"])
@require_permission("manage_users")
def delete_existing_user(user_id):
    """Delete a user (requires user management permission)"""
    try:
        # Check if trying to delete self
        if user_id == request.current_user['id']:
            return jsonify({"success": False, "message": "Cannot delete your own account"}), 400
        
        success, message = delete_user(user_id)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error deleting user: {str(e)}"}), 500

@users_bp.route("/users/<user_id>/toggle-status", methods=["PUT"])
@require_permission("manage_users")
def toggle_user_status(user_id):
    """Toggle user active status (requires user management permission)"""
    try:
        # Check if trying to deactivate self
        if user_id == request.current_user['id']:
            return jsonify({"success": False, "message": "Cannot deactivate your own account"}), 400
        
        user = find_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        new_status = not user.get('active', True)
        
        # Don't allow deactivating the last super admin
        if not new_status and user.get('role') == 'super_admin':
            users = load_users()
            active_super_admins = [u for u in users if u.get('role') == 'super_admin' and u.get('active', True)]
            if len(active_super_admins) <= 1:
                return jsonify({"success": False, "message": "Cannot deactivate the last super admin"}), 400
        
        updated_user = update_user(user_id, {
            'active': new_status,
            'updated_by': request.current_user['id']
        })
        
        if updated_user:
            user_response = {k: v for k, v in updated_user.items() if k != 'password'}
            user_response['role_name'] = USER_ROLES.get(updated_user.get('role'), {}).get('name', 'Unknown')
            
            status = "activated" if new_status else "deactivated"
            return jsonify({
                "success": True, 
                "message": f"User {status} successfully",
                "user": user_response
            })
        else:
            return jsonify({"success": False, "message": "Error updating user status"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error toggling user status: {str(e)}"}), 500

@users_bp.route("/roles", methods=["GET"])
@require_auth()
def get_roles():
    """Get all available roles"""
    try:
        current_user = request.current_user
        
        # Super admins can see all roles, others see limited roles
        if current_user.get('role') == 'super_admin':
            available_roles = USER_ROLES
        else:
            # Non-super-admins can only assign roles below their level
            available_roles = {
                k: v for k, v in USER_ROLES.items() 
                if k not in ['super_admin']
            }
        
        return jsonify({"success": True, "roles": available_roles})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving roles: {str(e)}"}), 500

@users_bp.route("/profile", methods=["GET"])
@require_auth()
def get_profile():
    """Get current user's profile"""
    try:
        user = request.current_user
        
        # Return user info without password
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['permissions'] = get_user_permissions(user)
        user_response['role_name'] = USER_ROLES.get(user.get('role'), {}).get('name', 'Unknown')
        
        return jsonify({"success": True, "user": user_response})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving profile: {str(e)}"}), 500

@users_bp.route("/profile", methods=["PUT"])
@require_auth()
def update_profile():
    """Update current user's profile"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No update data provided"}), 400
        
        user_id = request.current_user['id']
        
        # Only allow updating certain fields in profile
        allowed_fields = ['full_name', 'email', 'password']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({"success": False, "message": "No valid fields to update"}), 400
        
        # Validate email if provided
        if 'email' in update_data and update_data['email']:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, update_data['email']):
                return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        # Hash password if provided
        if 'password' in update_data and update_data['password']:
            update_data['password'] = hash_password(update_data['password'])
        
        update_data['updated_by'] = user_id
        
        # Update user
        updated_user = update_user(user_id, update_data)
        if updated_user:
            # Return user info without password
            user_response = {k: v for k, v in updated_user.items() if k != 'password'}
            user_response['permissions'] = get_user_permissions(updated_user)
            user_response['role_name'] = USER_ROLES.get(updated_user.get('role'), {}).get('name', 'Unknown')
            
            return jsonify({
                "success": True, 
                "message": "Profile updated successfully",
                "user": user_response
            })
        else:
            return jsonify({"success": False, "message": "Error updating profile"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error updating profile: {str(e)}"}), 500 