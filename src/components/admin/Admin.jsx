import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import './Admin.css';
import AdminDetailsModal from './AdminDetailsModal';
import AdminQuestions from './AdminQuestions';
import AdminListeningQuestions from './AdminListeningQuestions';
import UserManagement from './UserManagement';

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
  const [currentUser, setCurrentUser] = useState(null);
  
  const [activeTab, setActiveTab] = useState('applicants'); // 'applicants', 'questions', 'listening-questions', 'users'
  const [viewMode, setViewMode] = useState('list'); // 'grid' or 'list'
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(6);

  // Auto-logout functionality
  const [showLogoutWarning, setShowLogoutWarning] = useState(false);
  const [warningCountdown, setWarningCountdown] = useState(60);
  const logoutTimerRef = useRef(null);
  const warningTimerRef = useRef(null);
  const countdownIntervalRef = useRef(null);
  const lastActivityRef = useRef(Date.now());


  const API_URL = import.meta.env.VITE_API_URL;
  
  const AUTO_LOGOUT_TIME = 10 * 60 * 1000; // 10 minutes in milliseconds
  const WARNING_TIME = 60 * 1000; // Show warning 1 minute before logout

  // Configure axios to include auth token
  const getAuthHeaders = () => {
    const token = localStorage.getItem('adminToken');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const handleAutoLogout = useCallback(() => {
    // Clear all timers
    if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current);
    if (warningTimerRef.current) clearTimeout(warningTimerRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    
    // Clear stored activity time
    localStorage.removeItem('adminLastActivity');
    
    // Logout
    setIsAuthenticated(false);
    localStorage.removeItem('adminAuthenticated');
    setApplicants([]);
    setSelectedApplicant(null);
    setSearchTerm('');
    setShowLogoutWarning(false);
    
    alert('Your session has expired due to inactivity. Please log in again.');
  }, []);

  const hasPermission = (permission) => {
    if (!currentUser || !currentUser.permissions) return false;
    return currentUser.permissions.includes(permission) || currentUser.permissions.includes('*');
  };

  const clearAllTimers = () => {
    if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current);
    if (warningTimerRef.current) clearTimeout(warningTimerRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
  };

  // Reset activity timer
  const resetActivityTimer = useCallback(() => {
    if (!isAuthenticated) return;
    
    const now = Date.now();
    lastActivityRef.current = now;
    localStorage.setItem('adminLastActivity', now.toString());
    setShowLogoutWarning(false);
    
    // Clear existing timers
    clearAllTimers();

    // Set warning timer (9 minutes)
    warningTimerRef.current = setTimeout(() => {
      setShowLogoutWarning(true);
      setWarningCountdown(60);
      
      // Start countdown
      countdownIntervalRef.current = setInterval(() => {
        setWarningCountdown(prev => {
          if (prev <= 1) {
            handleAutoLogout();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }, AUTO_LOGOUT_TIME - WARNING_TIME);

    // Set auto-logout timer (10 minutes)
    logoutTimerRef.current = setTimeout(() => {
      handleAutoLogout();
    }, AUTO_LOGOUT_TIME);
  }, [isAuthenticated, handleAutoLogout, AUTO_LOGOUT_TIME, WARNING_TIME]);

  const extendSession = () => {
    resetActivityTimer();
  };

  useEffect(() => {
    // Check if already authenticated with new token system
    const token = localStorage.getItem('adminToken');
    if (token) {
      // Verify token with backend
      axios.get(`${API_URL}/auth/verify`, {
        headers: getAuthHeaders()
      })
      .then(response => {
        if (response.data.success) {
          setIsAuthenticated(true);
          setCurrentUser(response.data.user);
          fetchApplicants();
        } else {
          handleAutoLogout();
        }
      })
      .catch(err => {
        console.error('Token verification failed:', err);
        handleAutoLogout();
      });
    } else {
      // Check legacy authentication
      const legacyAuth = localStorage.getItem('adminAuthenticated');
      if (legacyAuth === 'true') {
        // Migrate to new system - show login form
        localStorage.removeItem('adminAuthenticated');
        localStorage.removeItem('adminLastActivity');
      }
      setLoading(false);
    }
  }, [handleAutoLogout, API_URL]);

  // Track user activity
  useEffect(() => {
    if (!isAuthenticated) return;

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    const activityHandler = () => {
      resetActivityTimer();
    };

    // Add event listeners
    events.forEach(event => {
      document.addEventListener(event, activityHandler, true);
    });

    // Initialize timer
    resetActivityTimer();

    // Cleanup
    return () => {
      events.forEach(event => {
        document.removeEventListener(event, activityHandler, true);
      });
      if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current);
      if (warningTimerRef.current) clearTimeout(warningTimerRef.current);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };
  }, [isAuthenticated, resetActivityTimer]);

  const handleDeleteApplicant = async (applicantId) => {
    if (!hasPermission('delete_applicants')) {
      alert('You do not have permission to delete applicants.');
      return;
    }
    
    if (!window.confirm('Are you sure you want to delete this applicant? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await axios.delete(`${API_URL}/admin/applicants/${applicantId}`, {
        headers: getAuthHeaders()
      });
      if (response.data.success) {
        setApplicants(applicants.filter(a => a.id !== applicantId));
        alert('Applicant deleted successfully!');
      } else {
        alert('Error deleting applicant: ' + response.data.message);
      }
    } catch (err) {
      console.error('Delete error:', err);
      if (err.response && err.response.status === 401) {
        handleAutoLogout();
      } else if (err.response && err.response.status === 403) {
        alert('You do not have permission to delete applicants.');
      } else if (err.response && err.response.data && err.response.data.message) {
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
      const response = await axios.post(`${API_URL}/auth/login`, {
        username: loginForm.username,
        password: loginForm.password
      });
      
      if (response.data.success) {
        setIsAuthenticated(true);
        setCurrentUser(response.data.user);
        
        // Store JWT token
        localStorage.setItem('adminToken', response.data.token);
        
        // Clear legacy storage
        localStorage.removeItem('adminAuthenticated');
        localStorage.removeItem('adminLastActivity');
        
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
    setCurrentUser(null);
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminAuthenticated');
    localStorage.removeItem('adminLastActivity');
    clearAllTimers();
    setShowLogoutWarning(false);
  };

  const fetchApplicants = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/admin/applicants`, {
        headers: getAuthHeaders()
      });
      
      if (response.data && response.data.applicants) {
        setApplicants(response.data.applicants);
      }
    } catch (err) {
      console.error('Error fetching applicants:', err);
      if (err.response && err.response.status === 401) {
        handleAutoLogout();
      } else if (err.response && err.response.status === 403) {
        setError('You do not have permission to view applicants.');
      } else {
        setError('Error loading applicants data');
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredApplicants = applicants.filter(applicant => {
    // Updated to handle new comprehensive applicant format
    const firstName = applicant.applicant_info?.firstName || '';
    const lastName = applicant.applicant_info?.lastName || '';
    const fullName = `${lastName}, ${firstName}`.trim();
    const email = applicant.applicant_info?.email || '';
    const position = applicant.applicant_info?.positionApplied || '';
    const cellphone = applicant.applicant_info?.cellphoneNumber || '';
    
    const searchLower = searchTerm.toLowerCase();
    
    const matchesSearch = 
      fullName.toLowerCase().includes(searchLower) ||
      firstName.toLowerCase().includes(searchLower) ||
      lastName.toLowerCase().includes(searchLower) ||
      email.toLowerCase().includes(searchLower) ||
      position.toLowerCase().includes(searchLower) ||
      cellphone.includes(searchTerm);
      
    return matchesSearch;
  });
  
  // Calculate total pages
  const totalPages = Math.ceil(filteredApplicants.length / itemsPerPage);
  
  // Get current page items
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredApplicants.slice(indexOfFirstItem, indexOfLastItem);
  
  // Page change handler
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };
  
  // Reset to first page when search term changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);





  const getCompletionStatus = (applicant) => {
    // New segmented format only
    const hasEvaluations = (
      (applicant.speech_eval && applicant.speech_eval.length > 0) ||
      (applicant.listening_test && applicant.listening_test.length > 0) ||
      (applicant.written_test && applicant.written_test.length > 0) ||
      (applicant.typing_test && applicant.typing_test.length > 0)
    );
    
    if (!hasEvaluations) return 'Not Started';
    if (applicant.completion_timestamp) return 'Completed';
    return 'In Progress';
  };

  const getStorageTypeLabel = (applicant) => {
    // Check applicant_status first (new, pending, approved, rejected)
    const applicantStatus = applicant.applicant_info?.applicant_status || applicant.applicant_status;
    
    if (applicantStatus === 'new') {
      return '🔵 New';
    } else if (applicantStatus === 'pending') {
      return '🟡 Pending';
    } else if (applicantStatus === 'approved') {
      return '🟢 Approved';
    } else if (applicantStatus === 'rejected') {
      return '🔴 Rejected';
    }
    
    // Fallback to storage type (temporary/permanent)
    return applicant.status === 'temporary' ? '🟠 (OLD FORMAT)' : '🟠 (OLD FORMAT)';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed': return '#10b981';
      case 'In Progress': return '#f59e0b';
      case 'Not Started': return '#6b7280';
      default: return '#6b7280';
    }
  };

  {/*
  const getTotalQuestions = (applicant) => {
    // New segmented format only
    let total = 0;
    total += (applicant.speech_eval?.length || 0);
    total += (applicant.listening_test?.length || 0);
    total += (applicant.written_test?.length || 0);
    total += (applicant.typing_test?.length || 0);
    return total;
  };
  */}
  const getTestScores = (applicant) => {
    // Get scores for each test type
    const speechScore = applicant.speech_eval && applicant.speech_eval.length > 0 
      ? applicant.speech_eval.reduce((sum, evalItem) => sum + (evalItem.evaluation?.score || 0), 0) / applicant.speech_eval.length
      : 0;
    
    const listeningScore = applicant.listening_test && applicant.listening_test.length > 0
      ? applicant.listening_test.reduce((sum, evalItem) => sum + (evalItem.accuracy_percentage || 0), 0) / applicant.listening_test.length
      : 0;
    
    // Fixed written test score calculation
    const writtenScore = applicant.written_test && applicant.written_test.length > 0
      ? applicant.written_test.reduce((sum, evalItem) => sum + (evalItem.score_percentage || 0), 0) / applicant.written_test.length
      : 0;
    
    const typingScore = applicant.typing_test && applicant.typing_test.length > 0
      ? applicant.typing_test.reduce((sum, evalItem) => sum + (evalItem.words_per_minute || 0), 0) / applicant.typing_test.length
      : 0;
    
    // Calculate personality score: categories passed / total categories
    let personalityPassed = 0;
    let personalityTotal = 0;
    if (applicant.personality_test && applicant.personality_test.length > 0) {
      const personalityData = applicant.personality_test[0]; // Get first personality test result
      if (personalityData && personalityData.category_analysis) {
        const categories = Object.keys(personalityData.category_analysis);
        personalityTotal = categories.length;
        personalityPassed = categories.filter(cat => 
          personalityData.category_analysis[cat].passed === true
        ).length;
      }
    }
    
    // Calculate merged score: (Speech + Listening) / 2
    // Note: listeningScore is in percentage (0-100), so divide by 10 to get 0-10 scale
    const listeningScoreNormalized = parseFloat(listeningScore) / 10;
    const mergedScore = (parseFloat(speechScore) + listeningScoreNormalized) / 2;
    const passFail = mergedScore >= 7.0 ? 'PASS' : 'FAIL';
    
    return {
      speech: speechScore.toFixed(1),
      listening: listeningScore.toFixed(1),
      written: writtenScore.toFixed(1),
      typing: typingScore.toFixed(1),
      personality: `${personalityPassed}/${personalityTotal}`,
      merged: mergedScore.toFixed(1),
      passFail: passFail
    };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
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
          <h1>Admin Dashboard</h1>
          <p>Manage and review applicant evaluations</p>
        </div>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </div>

      <div className="admin-tabs">
      <div className="stat-card">
              <h3>Total Applicants:</h3>
              <span className="stat-number">{applicants.length}</span>
            </div>
        <button 
          className={`tab-button ${activeTab === 'applicants' ? 'active' : ''}`}
          onClick={() => setActiveTab('applicants')}
        >
          Applicants
        </button>
        {currentUser?.role === 'super_admin' && (
          <>
            <button 
              className={`tab-button ${activeTab === 'questions' ? 'active' : ''}`}
              onClick={() => setActiveTab('questions')}
            >
              Speech Evaluation Questions
            </button>
            <button 
              className={`tab-button ${activeTab === 'listening-questions' ? 'active' : ''}`}
              onClick={() => setActiveTab('listening-questions')}
            >
              Listening Test Questions
            </button>
          </>
        )}
                  {hasPermission('view_users') && (
            <button 
              className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              User Management
            </button>
          )}
      </div>

      {activeTab === 'applicants' && (
        <>
          <div className="admin-stats">

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
            
            <div className="view-toggle-section">
              <button 
                className={`view-toggle-button ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                title="Grid View"
              >
                📊 Grid
              </button>
              <button 
                className={`view-toggle-button ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
                title="List View"
              >
                📋 List
              </button>
            </div>
            
            <button onClick={fetchApplicants} className="refresh-button">
              Refresh
            </button>
          </div>

          <div className={viewMode === 'grid' ? 'applicants-grid' : 'applicants-list'}>
            {filteredApplicants.length === 0 ? (
              <div className="no-applicants">
                <p>No applicants found matching your criteria.</p>
              </div>
            ) : viewMode === 'grid' ? (
              // Grid View
              currentItems.map((applicant, index) => {
                // Handle new comprehensive applicant format
                const firstName = applicant.applicant_info?.firstName || '';
                const lastName = applicant.applicant_info?.lastName || '';
                const fullName = lastName && firstName ? `${lastName}, ${firstName}` : 'Unknown';
                
                return (
                  <div key={`${applicant.id}_${index}`} className="applicant-card">
                    <div className="applicant-header">
                      <h3>{fullName}</h3>
                      <div className="status-badges">
                        <span 
                          className="status-badge"
                          style={{ backgroundColor: getStatusColor(getCompletionStatus(applicant)) }}
                        >
                          {getCompletionStatus(applicant)}
                        </span>
                        <span className="storage-type-badge">
                          {getStorageTypeLabel(applicant)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="applicant-info">
                      <p><strong>Email:</strong> {applicant.applicant_info?.email || 'N/A'}</p>
                      <p><strong>Position Applied:</strong> {applicant.applicant_info?.positionApplied || 'N/A'}</p>
                      <p><strong>Cell Phone:</strong> {applicant.applicant_info?.cellphoneNumber || applicant.applicant_info?.landlineNumber || 'N/A'}</p>
                      <p><strong>Gender:</strong> {applicant.applicant_info?.gender || 'N/A'}</p>
                      <p><strong>Applied:</strong> {formatDate(applicant.application_timestamp)}</p>
                      {applicant.completion_timestamp && (
                        <p><strong>Completed:</strong> {formatDate(applicant.completion_timestamp)}</p>
                      )}
                    </div>

                    <div className="applicant-stats">
                      
                      <div className="stat-item">
                        <span>Speech Score:</span>
                        <span>{getTestScores(applicant).speech}/10</span>
                      </div>
                      <div className="stat-item">
                        <span>Listening Score:</span>
                        <span>{(parseFloat(getTestScores(applicant).listening) / 10).toFixed(1)}/10</span>
                      </div>
                      <div className="stat-item">
                        <span>Written Score:</span>
                        <span>{getTestScores(applicant).written}%</span>
                      </div>
                      <div className="stat-item">
                        <span>Typing Score (WPM):</span>
                        <span>{getTestScores(applicant).typing}</span>
                      </div>
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
            ) : (
              // List View
              <div className="applicants-list-container">
                <div className="list-header">
                  <div className="list-header-item applied">Applied</div>
                  <div className="list-header-item name">Name</div>
                  {/* <div className="list-header-item email">Email / Gender</div> */}
                  <div className="list-header-item position">Position</div>
                  <div className="list-header-item status">Status</div>
                  <div className="list-header-item scores">Test Scores</div>
                  <div className="list-header-item actions">Actions</div>
                </div>
                {currentItems.map((applicant, index) => {
                  const firstName = applicant.applicant_info?.firstName || '';
                  const lastName = applicant.applicant_info?.lastName || '';
                  const fullName = lastName && firstName ? `${lastName}, ${firstName}` : 'Unknown';
                  const testScores = getTestScores(applicant);
                  
                  return (
                    <div key={`${applicant.id}_${index}`} className="applicant-list-item">
                      <div className="list-item-content applied">
                        <div className="applied-date">{formatDate(applicant.application_timestamp)}</div>
                        {applicant.completion_timestamp && (
                          <div className="completed-date">{formatDate(applicant.completion_timestamp)}</div>
                        )}
                      </div>
                      
                      <div className="list-item-content name">
                        <div className="applicant-name">{fullName}</div>
                        <div className="applicant-phone">{applicant.applicant_info?.cellphoneNumber || applicant.applicant_info?.landlineNumber || 'N/A'}</div>
                      </div>
                      
                      {/* <div className="list-item-content email">
                        <div className="applicant-email">{applicant.applicant_info?.email || 'N/A'}</div>
                        <div className="applicant-gender"><span className="gender-label">Gender:</span> {applicant.applicant_info?.gender || 'N/A'}</div>
                      </div> */}
                      
                      <div className="list-item-content position">
                        <div className="applicant-position">{applicant.applicant_info?.positionApplied || 'N/A'}</div>
                        
                      </div>
                      
                      <div className="list-item-content status">
                        <span 
                          className="status-badge list-status"
                          style={{ backgroundColor: getStatusColor(getCompletionStatus(applicant)) }}
                        >
                          {getCompletionStatus(applicant)}
                        </span>
                        <span className="storage-type-badge list-storage">
                          {getStorageTypeLabel(applicant)}
                        </span>
                      </div>
                      
                      <div className="list-item-content scores">
                        <div className="scores-grid-container">
                          <div className="score-row">
                            <span className="score-label">Speech:</span>
                            <span className="score-value">{testScores.speech}/10</span>
                          </div>
                          <div className="score-row">
                            <span className="score-label">Personality:</span>
                            <span className="score-value">{testScores.personality}</span>
                          </div>
                          <div className="score-row">
                            <span className="score-label">Listen:</span>
                            <span className="score-value">{(parseFloat(testScores.listening) / 10).toFixed(1)}/10</span>
                          </div>
                          <div className="score-row">
                            <span className="score-label">Written:</span>
                            <span className="score-value">{testScores.written}%</span>
                          </div>
                          
                          <div className="score-row">
                            <span className="score-label">Score:</span>
                            <span 
                              className="score-value"
                              style={{ color: parseFloat(testScores.merged) >= 7.0 ? '#10b981' : '#ef4444' }}
                            >
                              {testScores.merged}/10 ({testScores.passFail})
                            </span>
                          </div>
                          <div className="score-row">
                            <span className="score-label">Typing:</span>
                            <span className="score-value">{testScores.typing} WPM</span>
                          </div>
                          
                         {/*} <div className="score-row">
                            <span className="score-label">Placeholder2:</span>
                            <span className="score-value">101</span>
                          </div>
                          
                          
                          <div className="score-row">
                            <span className="score-label">Placeholder3:</span>
                            <span className="score-value">101</span>
                          </div>
                          */}
                          
                        </div>
                      </div>
                      
                      <div className="list-item-content actions">
                        <button
                          onClick={() => setSelectedApplicant(applicant)}
                          className="list-action-button details-button"
                          title="View Details"
                        >
                          Details
                        </button>
                        <button
                          onClick={() => handleDeleteApplicant(applicant.id)}
                          className="list-action-button delete-button"
                          title="Delete Applicant"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          
          {/* Pagination Controls */}
          {filteredApplicants.length > 0 && (
            <div className="pagination-controls">
              <button 
                onClick={() => handlePageChange(1)} 
                disabled={currentPage === 1}
                className="pagination-button first-page-button"
                title="First Page"
              >
                <span className="pagination-icon">&laquo;</span>
              </button>
              
              <button 
                onClick={() => handlePageChange(currentPage - 1)} 
                disabled={currentPage === 1}
                className="pagination-button prev-page-button"
                title="Previous Page"
              >
                <span className="pagination-icon">&lsaquo;</span>
              </button>
              
              <div className="pagination-info">
                Page {currentPage} of {totalPages}
              </div>
              
              <button 
                onClick={() => handlePageChange(currentPage + 1)} 
                disabled={currentPage === totalPages}
                className="pagination-button next-page-button"
                title="Next Page"
              >
                <span className="pagination-icon">&rsaquo;</span>
              </button>
              
              <button 
                onClick={() => handlePageChange(totalPages)} 
                disabled={currentPage === totalPages}
                className="pagination-button last-page-button"
                title="Last Page"
              >
                <span className="pagination-icon">&raquo;</span>
              </button>
              
              <select 
                value={itemsPerPage} 
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="items-per-page-select"
                title="Items Per Page"
              >
                <option value={6}>6 per page</option>
                <option value={12}>12 per page</option>
                <option value={24}>24 per page</option>
                <option value={48}>48 per page</option>
              </select>
            </div>
          )}
        </>
      )}

              {activeTab === 'questions' && (
          <AdminQuestions getAuthHeaders={getAuthHeaders} />
        )}

        {activeTab === 'listening-questions' && (
          <AdminListeningQuestions getAuthHeaders={getAuthHeaders} />
        )}

              {activeTab === 'users' && (
          <UserManagement 
            currentUser={currentUser}
            getAuthHeaders={getAuthHeaders}
          />
        )}

      {/* Modal for detailed view */}
      {selectedApplicant && (
        <AdminDetailsModal 
          applicant={selectedApplicant}
          onClose={() => setSelectedApplicant(null)}
          getAuthHeaders={getAuthHeaders}
          currentUser={currentUser}
        />
      )}

      {/* Auto-logout warning modal */}
      {showLogoutWarning && (
        <div className="logout-warning-overlay">
          <div className="logout-warning-modal">
            <div className="warning-header">
              <h3>⚠️ Session Expiring</h3>
            </div>
            <div className="warning-content">
              <p>Your session will expire in <strong>{warningCountdown}</strong> seconds due to inactivity.</p>
              <p>Click "Stay Logged In" to extend your session.</p>
            </div>
            <div className="warning-actions">
              <button onClick={extendSession} className="extend-session-button">
                Stay Logged In
              </button>
              <button onClick={handleAutoLogout} className="logout-now-button">
                Logout Now
              </button>
            </div>
          </div>
        </div>
      )}

        {/* Modal for editing questions */}
        {/* This block is removed as per the edit hint */}
      </div>
    );
  };

export default Admin;
