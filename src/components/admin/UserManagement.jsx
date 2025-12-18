import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './UserManagement.css';

const API_URL = import.meta.env.VITE_API_URL;

const UserManagement = ({ currentUser, getAuthHeaders }) => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    full_name: '',
    email: '',
    role: 'viewer',
    active: true
  });

  const hasPermission = (permission) => {
    if (!currentUser || !currentUser.permissions) return false;
    return currentUser.permissions.includes(permission) || currentUser.permissions.includes('*');
  };

  useEffect(() => {
    if (hasPermission('view_users')) {
      fetchUsers();
      fetchRoles();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/users`, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setUsers(response.data.users);
      }
    } catch (err) {
      console.error('Error fetching users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await axios.get(`${API_URL}/roles`, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setRoles(response.data.roles);
      }
    } catch (err) {
      console.error('Error fetching roles:', err);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    // Prevent evaluators from creating users
    if (currentUser.role === 'evaluator') {
      alert('Evaluators cannot create users');
      return;
    }
    
    // Validate role creation permissions
    if ((formData.role === 'super_admin' || formData.role === 'admin') && currentUser.role !== 'super_admin') {
      alert('Only Super Admins can create Super Admin or Admin users');
      return;
    }
    
    try {
      const response = await axios.post(`${API_URL}/users`, formData, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setUsers([...users, response.data.user]);
        setShowCreateModal(false);
        resetForm();
        alert('User created successfully!');
      } else {
        alert('Error creating user: ' + response.data.message);
      }
    } catch (err) {
      console.error('Error creating user:', err);
      if (err.response && err.response.data && err.response.data.errors) {
        alert('Validation errors: ' + err.response.data.errors.join(', '));
      } else if (err.response && err.response.data && err.response.data.message) {
        alert('Error creating user: ' + err.response.data.message);
      } else {
        alert('Error creating user');
      }
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    
    // Prevent evaluators from editing other users
    if (currentUser.role === 'evaluator' && selectedUser.id !== currentUser.id) {
      alert('Evaluators can only edit their own user details');
      return;
    }
    
    // Prevent admins from editing super admins
    if (currentUser.role === 'admin' && selectedUser.role === 'super_admin') {
      alert('Only Super Admins can edit Super Admin users');
      return;
    }
    
    try {
      const updateData = { ...formData };
      if (!updateData.password) {
        delete updateData.password; // Don't update password if not provided
      }
      
      // Evaluators use the /profile endpoint, others use /users/<id>
      const endpoint = currentUser.role === 'evaluator' 
        ? `${API_URL}/profile`
        : `${API_URL}/users/${selectedUser.id}`;
      
      const response = await axios.put(endpoint, updateData, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        // Update user in the list
        const updatedUser = response.data.user;
        setUsers(users.map(user => 
          user.id === selectedUser.id ? updatedUser : user
        ));
        setShowEditModal(false);
        setSelectedUser(null);
        resetForm();
        alert('User updated successfully!');
      } else {
        alert('Error updating user: ' + response.data.message);
      }
    } catch (err) {
      console.error('Error updating user:', err);
      if (err.response && err.response.data && err.response.data.errors) {
        alert('Validation errors: ' + err.response.data.errors.join(', '));
      } else if (err.response && err.response.data && err.response.data.message) {
        alert('Error updating user: ' + err.response.data.message);
      } else {
        alert('Error updating user');
      }
    }
  };

  const handleDeleteUser = async (userId) => {
    // Prevent evaluators from deleting users
    if (currentUser.role === 'evaluator') {
      alert('Evaluators cannot delete users');
      return;
    }
    
    // Prevent admins from deleting super admins
    const userToDelete = users.find(u => u.id === userId);
    if (currentUser.role === 'admin' && userToDelete.role === 'super_admin') {
      alert('Only Super Admins can delete Super Admin users');
      return;
    }
    
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await axios.delete(`${API_URL}/users/${userId}`, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setUsers(users.filter(user => user.id !== userId));
        alert('User deleted successfully!');
      } else {
        alert('Error deleting user: ' + response.data.message);
      }
    } catch (err) {
      console.error('Error deleting user:', err);
      if (err.response && err.response.data && err.response.data.message) {
        alert('Error deleting user: ' + err.response.data.message);
      } else {
        alert('Error deleting user');
      }
    }
  };

  const handleToggleStatus = async (userId) => {
    // Prevent evaluators from toggling status
    if (currentUser.role === 'evaluator') {
      alert('Evaluators cannot change user status');
      return;
    }
    
    // Prevent admins from toggling super admin status
    const userToToggle = users.find(u => u.id === userId);
    if (currentUser.role === 'admin' && userToToggle.role === 'super_admin') {
      alert('Only Super Admins can change Super Admin user status');
      return;
    }
    
    try {
      const response = await axios.put(`${API_URL}/users/${userId}/toggle-status`, {}, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setUsers(users.map(user => 
          user.id === userId ? response.data.user : user
        ));
        alert(response.data.message);
      } else {
        alert('Error updating user status: ' + response.data.message);
      }
    } catch (err) {
      console.error('Error toggling user status:', err);
      if (err.response && err.response.data && err.response.data.message) {
        alert('Error updating user status: ' + err.response.data.message);
      } else {
        alert('Error updating user status');
      }
    }
  };

  const openEditModal = (user) => {
    // Check if evaluator is trying to edit another user
    if (currentUser.role === 'evaluator' && user.id !== currentUser.id) {
      alert('Evaluators can only edit their own user details');
      return;
    }
    
    setSelectedUser(user);
    setFormData({
      username: user.username,
      password: '', // Don't pre-fill password
      full_name: user.full_name,
      email: user.email,
      role: user.role,
      active: user.active
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      username: '',
      password: '',
      full_name: '',
      email: '',
      role: 'viewer',
      active: true
    });
  };

  const closeModal = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setSelectedUser(null);
    resetForm();
  };

  // Evaluators need special handling - they can view and edit only their own profile
  const isEvaluator = currentUser?.role === 'evaluator';
  const isViewer = currentUser?.role === 'viewer';
  
  if (!hasPermission('view_users')) {
    return (
      <div className="user-management">
        <div className="no-permission">
          <h3>Access Denied</h3>
          <p>You do not have permission to view user management.</p>
        </div>
      </div>
    );
  }
  
  // Viewers cannot see the user management page
  if (isViewer) {
    return (
      <div className="user-management">
        <div className="no-permission">
          <h3>Access Denied</h3>
          <p>Viewers do not have access to user management.</p>
        </div>
      </div>
    );
  }

  if (loading) return <div className="loading">Loading users...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="user-management">
      <div className="user-management-header">
        <h2>{isEvaluator ? 'My Profile' : 'User Management'}</h2>
        {hasPermission('manage_users') && (currentUser.role === 'super_admin' || currentUser.role === 'admin') && (
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            Add New User
          </button>
        )}
      </div>

      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Role</th>
              {!isEvaluator && <th>Status</th>}
              {!isEvaluator && <th>Last Login</th>}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {/* Evaluators only see their own profile */}
            {isEvaluator ? (
              users.filter(user => user.id === currentUser.id).map(user => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td className="full-name">{user.full_name}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`role-badge role-${user.role}`}>
                      {user.role_name}
                    </span>
                  </td>
                  <td className="actions">
                    <button 
                      className="btn btn-sm btn-secondary"
                      onClick={() => openEditModal(user)}
                    >
                      Edit Profile
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              /* Admins and Super Admins see all users */
              users.map(user => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td className="full-name">{user.full_name}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`role-badge role-${user.role}`}>
                      {user.role_name}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${user.active ? 'active' : 'inactive'}`}>
                      {user.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="actions">
                    {/* Admins cannot edit super admins, only super admins can */}
                    {(currentUser.role === 'super_admin' || user.role !== 'super_admin') && (
                      <button 
                        className="btn btn-sm btn-secondary"
                        onClick={() => openEditModal(user)}
                        title={`Edit ${user.username}`}
                      >
                        Edit
                      </button>
                    )}
                    
                    {/* Admins cannot toggle super admin status */}
                    {(currentUser.role === 'super_admin' || user.role !== 'super_admin') && (
                      <button 
                        className={`btn btn-sm ${user.active ? 'btn-warning' : 'btn-success'}`}
                        onClick={() => handleToggleStatus(user.id)}
                        disabled={user.id === currentUser.id}
                      >
                        {user.active ? 'Deactivate' : 'Activate'}
                      </button>
                    )}
                    
                    {/* Admins cannot delete super admins */}
                    {(currentUser.role === 'super_admin' || user.role !== 'super_admin') && (
                      <button 
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDeleteUser(user.id)}
                        disabled={user.id === currentUser.id}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Create New User</h3>
              <button className="close-btn" onClick={closeModal}>&times;</button>
            </div>
            <form onSubmit={handleCreateUser}>
              <div className="form-group">
                <label>Username:</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password:</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Full Name:</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Role:</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                  disabled={Object.keys(roles).length === 0}
                >
                  {Object.keys(roles).length === 0 ? (
                    <option value="">No roles available</option>
                  ) : (
                    Object.entries(roles).map(([key, role]) => (
                      <option key={key} value={key}>{role.name}</option>
                    ))
                  )}
                </select>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={Object.keys(roles).length === 0}>
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>{isEvaluator ? 'Edit My Profile' : `Edit User: ${selectedUser.username}`}</h3>
              <button className="close-btn" onClick={closeModal}>&times;</button>
            </div>
            <form onSubmit={handleUpdateUser}>
              {/* Username field - hidden for evaluators editing own profile */}
              {!isEvaluator && (
                <div className="form-group">
                  <label>Username:</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    required
                  />
                </div>
              )}
              
              <div className="form-group">
                <label>Password (leave blank to keep current):</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                />
              </div>
              
              <div className="form-group">
                <label>Full Name:</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              
              {/* Role field - hidden for evaluators */}
              {!isEvaluator && (
                <div className="form-group">
                  <label>Role:</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                  >
                    {Object.entries(roles).map(([key, role]) => (
                      <option key={key} value={key}>{role.name}</option>
                    ))}
                  </select>
                </div>
              )}
              
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {isEvaluator ? 'Update Profile' : 'Update User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement; 