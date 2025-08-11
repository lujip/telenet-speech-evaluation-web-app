import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Admin.css';
import AdminDetailsModal from './AdminDetailsModal';
import AdminQuestions from './AdminQuestions';

const Admin = () => {
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedApplicant, setSelectedApplicant] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  });
  
  const [activeTab, setActiveTab] = useState('applicants'); // 'applicants' or 'questions'

  useEffect(() => {
    // Check if already authenticated
    const authStatus = localStorage.getItem('adminAuthenticated');
    if (authStatus === 'true') {
      setIsAuthenticated(true);
      fetchApplicants();
    } else {
      setLoading(false);
    }
  }, []);

  const handleDeleteApplicant = async (applicantId) => {
    if (!window.confirm('Are you sure you want to delete this applicant? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await axios.delete(`http://localhost:5000/admin/applicants/${applicantId}`);
      if (response.data.success) {
        setApplicants(applicants.filter(a => a.id !== applicantId));
        alert('Applicant deleted successfully!');
      } else {
        alert('Error deleting applicant: ' + response.data.message);
      }
    } catch (err) {
      console.error('Delete error:', err);
      if (err.response && err.response.data && err.response.data.message) {
        alert('Error deleting applicant: ' + err.response.data.message);
      } else if (err.response && err.response.status === 404) {
        alert('Applicant not found. It may have already been deleted or doesn\'t exist.');
        // Refresh the applicants list to sync with backend
        fetchApplicants();
      } else {
        alert('Error deleting applicant: ' + err.message);
      }
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    
    try {
      const response = await axios.post('http://localhost:5000/admin/auth', {
        username: loginForm.username,
        password: loginForm.password
      });
      
      if (response.data.success) {
        setIsAuthenticated(true);
        localStorage.setItem('adminAuthenticated', 'true');
        fetchApplicants();
      } else {
        setLoginError(response.data.message || 'Authentication failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err.response && err.response.data && err.response.data.message) {
        setLoginError(err.response.data.message);
      } else {
        setLoginError('Authentication failed. Please try again.');
      }
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('adminAuthenticated');
    setApplicants([]);
    setSelectedApplicant(null);
    setSearchTerm('');
  };

  const fetchApplicants = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:5000/admin/applicants');
      setApplicants(response.data.applicants || []);
    } catch (err) {
      console.error('Error fetching applicants:', err);
      setError('Failed to load applicant data');
    } finally {
      setLoading(false);
    }
  };

  const filteredApplicants = applicants.filter(applicant => {
    const matchesSearch = applicant.applicant_info?.fullName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         applicant.applicant_info?.email?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const getAverageScore = (evaluations) => {
    if (!evaluations || evaluations.length === 0) return 0;
    const totalScore = evaluations.reduce((sum, evalItem) => sum + (evalItem.evaluation?.score || 0), 0);
    return (totalScore / evaluations.length).toFixed(1);
  };

  const getTypingTestStats = (evaluations) => {
    if (!evaluations || evaluations.length === 0) return null;
    
    const typingTests = evaluations.filter(evaluation => evaluation.type === 'typing');
    if (typingTests.length === 0) return null;
    
    const totalWPM = typingTests.reduce((sum, test) => sum + (test.words_per_minute || 0), 0);
    const totalAccuracy = typingTests.reduce((sum, test) => sum + (test.accuracy_percentage || 0), 0);
    const averageWPM = (totalWPM / typingTests.length).toFixed(1);
    const averageAccuracy = (totalAccuracy / typingTests.length).toFixed(1);
    
    return {
      count: typingTests.length,
      averageWPM,
      averageAccuracy
    };
  };

  const getCompletionStatus = (applicant) => {
    if (!applicant.evaluations) return 'Not Started';
    if (applicant.evaluations.length === 0) return 'Not Started';
    if (applicant.completion_timestamp) return 'Completed';
    return 'In Progress';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed': return '#10b981';
      case 'In Progress': return '#f59e0b';
      case 'Not Started': return '#6b7280';
      default: return '#6b7280';
    }
  };

  // Login Form
  if (!isAuthenticated) {
    return (
      <div className="admin-container">
        <div className="login-container">
          <div className="login-card">
            <div className="login-header">
              <h1>Admin Login</h1>
              <p>Enter your credentials to access the admin dashboard</p>
            </div>
            
            <form onSubmit={handleLogin} className="login-form">
              <div className="form-group">
                <label htmlFor="username">Username</label>
                <input
                  type="text"
                  id="username"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
                  placeholder="Enter username"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                  placeholder="Enter password"
                  required
                />
              </div>
              
              {loginError && (
                <div className="login-error">
                  {loginError}
                </div>
              )}
              
              <button type="submit" className="login-button">
                Login
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="admin-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-container">
        <div className="error-message">{error}</div>
        <button onClick={fetchApplicants} className="retry-button">Retry</button>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <div className="header-content">
          <h1>📊 Admin Dashboard</h1>
          <p>Manage and review applicant evaluations</p>
        </div>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </div>

      <div className="admin-tabs">
        <button 
          className={`tab-button ${activeTab === 'applicants' ? 'active' : ''}`}
          onClick={() => setActiveTab('applicants')}
        >
          📋 Applicants
        </button>
        <button 
          className={`tab-button ${activeTab === 'questions' ? 'active' : ''}`}
          onClick={() => setActiveTab('questions')}
        >
          ❓ Questions
        </button>
      </div>

      {activeTab === 'applicants' && (
        <>
          <div className="admin-stats">
            <div className="stat-card">
              <h3>Total Applicants</h3>
              <span className="stat-number">{applicants.length}</span>
            </div>
            <div className="stat-card">
              <h3>Completed</h3>
              <span className="stat-number">
                {applicants.filter(a => getCompletionStatus(a) === 'Completed').length}
              </span>
            </div>
            <div className="stat-card">
              <h3>In Progress</h3>
              <span className="stat-number">
                {applicants.filter(a => getCompletionStatus(a) === 'In Progress').length}
              </span>
            </div>
            <div className="stat-card">
              <h3>Not Started</h3>
              <span className="stat-number">
                {applicants.filter(a => getCompletionStatus(a) === 'Not Started').length}
              </span>
            </div>
          </div>

          <div className="admin-controls">
            <div className="search-section">
              <input
                type="text"
                placeholder="Search by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>
            
            <button onClick={fetchApplicants} className="refresh-button">
              Refresh
            </button>
          </div>

          <div className="applicants-grid">
            {filteredApplicants.length === 0 ? (
              <div className="no-applicants">
                <p>No applicants found matching your criteria.</p>
              </div>
            ) : (
              filteredApplicants.map((applicant, index) => {
                const typingStats = getTypingTestStats(applicant.evaluations);
                
                return (
                  <div key={`${applicant.id}_${index}`} className="applicant-card">
                    <div className="applicant-header">
                      <h3>{applicant.applicant_info?.fullName || 'Unknown'}</h3>
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(getCompletionStatus(applicant)) }}
                      >
                        {getCompletionStatus(applicant)}
                      </span>
                    </div>
                    
                    <div className="applicant-info">
                      <p><strong>Email:</strong> {applicant.applicant_info?.email || 'N/A'}</p>
                      <p><strong>Role:</strong> {applicant.applicant_info?.role || 'N/A'}</p>
                      <p><strong>Phone:</strong> {applicant.applicant_info?.phone || 'N/A'}</p>
                      <p><strong>Experience:</strong> {applicant.applicant_info?.experience || 'N/A'}</p>
                      <p><strong>Current Company:</strong> {applicant.applicant_info?.currentCompany || 'N/A'}</p>
                      <p><strong>Applied:</strong> {formatDate(applicant.application_timestamp)}</p>
                      {applicant.completion_timestamp && (
                        <p><strong>Completed:</strong> {formatDate(applicant.completion_timestamp)}</p>
                      )}
                    </div>

                    <div className="applicant-stats">
                      <div className="stat-item">
                        <span>Questions:</span>
                        <span>{applicant.evaluations?.length || 0}/{applicant.total_questions || 0}</span>
                      </div>
                      <div className="stat-item">
                        <span>Average Score:</span>
                        <span>{getAverageScore(applicant.evaluations)}/10</span>
                      </div>
                      {typingStats && (
                        <>
                          <div className="stat-item">
                            <span>Typing Tests:</span>
                            <span>{typingStats.count}</span>
                          </div>
                          <div className="stat-item">
                            <span>Avg WPM:</span>
                            <span>{typingStats.averageWPM}</span>
                          </div>
                        </>
                      )}
                    </div>

                    <div className="applicant-actions">
                      <button
                        onClick={() => setSelectedApplicant(applicant)}
                        className="view-details-button"
                      >
                        📋 Details
                      </button>
                      <button
                        onClick={() => handleDeleteApplicant(applicant.id)}
                        className="delete-applicant-button"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </>
      )}

      {activeTab === 'questions' && (
        <AdminQuestions />
      )}

      {/* Modal for detailed view */}
      <AdminDetailsModal 
        applicant={selectedApplicant}
        onClose={() => setSelectedApplicant(null)}
      />

        {/* Modal for editing questions */}
        {/* This block is removed as per the edit hint */}
      </div>
    );
  };

export default Admin;
