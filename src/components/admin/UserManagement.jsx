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
    
    try {
      const updateData = { ...formData };
      if (!updateData.password) {
        delete updateData.password; // Don't update password if not provided
      }
      
      const response = await axios.put(`${API_URL}/users/${selectedUser.id}`, updateData, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setUsers(users.map(user => 
          user.id === selectedUser.id ? response.data.user : user
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

  if (loading) return <div className="loading">Loading users...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="user-management">
      <div className="user-management-header">
        <h2>User Management</h2>
        {hasPermission('manage_users') && (
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
              <th>Status</th>
              <th>Last Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
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
                  {hasPermission('manage_users') && (
                    <>
                      <button 
                        className="btn btn-sm btn-secondary"
                        onClick={() => openEditModal(user)}
                      >
                        Edit
                      </button>
                      <button 
                        className={`btn btn-sm ${user.active ? 'btn-warning' : 'btn-success'}`}
                        onClick={() => handleToggleStatus(user.id)}
                        disabled={user.id === currentUser.id}
                      >
                        {user.active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button 
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDeleteUser(user.id)}
                        disabled={user.id === currentUser.id}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
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
                >
                  {Object.entries(roles).map(([key, role]) => (
                    <option key={key} value={key}>{role.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
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
              <h3>Edit User: {selectedUser.username}</h3>
              <button className="close-btn" onClick={closeModal}>&times;</button>
            </div>
            <form onSubmit={handleUpdateUser}>
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
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Update User
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