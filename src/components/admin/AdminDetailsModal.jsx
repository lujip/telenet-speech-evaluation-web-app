import React, { useState, useEffect } from 'react';
import './AdminDetailsModal.css';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

const AdminDetailsModal = ({ applicant, onClose, getAuthHeaders, currentUser }) => {
  const [activeTab, setActiveTab] = useState('speech-evaluation');
  const [showExtendedDetails, setShowExtendedDetails] = useState(false);
  const [showResume, setShowResume] = useState(false);
  
  // Comments state
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [commentsError, setCommentsError] = useState('');
  
  // Status state
  const [applicantStatus, setApplicantStatus] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  // Resume state
  const [currentResume, setCurrentResume] = useState(null);
  const [allResumes, setAllResumes] = useState([]);
  const [isUploadingResume, setIsUploadingResume] = useState(false);
  const [resumeUploadError, setResumeUploadError] = useState('');
  const [resumeUrl, setResumeUrl] = useState(null);

  // Load comments and resumes when modal opens or applicant changes
  useEffect(() => {
    if (applicant && applicant.id) {
      loadComments();
      loadApplicantResumes();
    }
  }, [applicant?.id]);

  // Initialize applicant status
  useEffect(() => {
    if (applicant) {
      const currentStatus = applicant.applicant_info?.applicant_status || applicant.applicant_status || 'permanent';
      setApplicantStatus(currentStatus);
    }
  }, [applicant]);

  const loadComments = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/applicants/${applicant.id}/comments`, {
        headers: getAuthHeaders()
      });
      setComments(response.data.comments || []);
      setCommentsError('');
    } catch (error) {
      console.error('Error loading comments:', error);
      if (error.response && error.response.status === 401) {
        setCommentsError('Authentication required. Please log in again.');
      } else if (error.response && error.response.status === 403) {
        setCommentsError('You do not have permission to view comments.');
      } else if (getCompletionStatus(applicant) === 'In Progress') {
        setCommentsError('Comments are not allowed for applicants who are still in progress.');
      } else {
        setCommentsError('Failed to load comments');
      }
    }
    
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;
    
    setIsSubmittingComment(true);
    setCommentsError('');
    
    try {
      // Get evaluator name from current user
      const evaluatorName = currentUser?.full_name || currentUser?.username || 'Unknown User';
      
      const response = await axios.post(`${API_URL}/admin/applicants/${applicant.id}/comments`, {
        comment: newComment.trim(),
        evaluator: evaluatorName
      }, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setNewComment('');
        loadComments(); // Reload comments to get the latest list
      } else {
        setCommentsError(response.data.message || 'Failed to submit comment');
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
      if (error.response && error.response.status === 401) {
        setCommentsError('Authentication required. Please log in again.');
      } else if (error.response && error.response.status === 403) {
        setCommentsError('You do not have permission to add comments.');
      } else {
        setCommentsError('Failed to submit comment');
      }
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const deleteComment = async (commentId) => {
    if (!window.confirm('Are you sure you want to delete this comment?')) return;
    
    try {
      const response = await axios.delete(`${API_URL}/admin/applicants/${applicant.id}/comments/${commentId}`, {
        headers: getAuthHeaders()
      });
      if (response.data.success) {
        loadComments(); // Reload comments
      } else {
        setCommentsError(response.data.message || 'Failed to delete comment');
      }
    } catch (error) {
      console.error('Error deleting comment:', error);
      if (error.response && error.response.status === 401) {
        setCommentsError('Authentication required. Please log in again.');
      } else if (error.response && error.response.status === 403) {
        setCommentsError('You do not have permission to delete comments.');
      } else {
        setCommentsError('Failed to delete comment');
      }
    }
  };

  const handleStatusChange = async (newStatus) => {
    setIsUpdatingStatus(true);
    try {
      const response = await axios.put(`${API_URL}/admin/applicants/${applicant.id}/status`, {
        status: newStatus
      }, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setApplicantStatus(newStatus);
        // Optionally notify parent component to refresh data
        alert('Status updated successfully!');
      } else {
        alert('Failed to update status: ' + response.data.message);
      }
    } catch (error) {
      console.error('Error updating status:', error);
      if (error.response && error.response.status === 401) {
        alert('Authentication required. Please log in again.');
      } else if (error.response && error.response.status === 403) {
        alert('You do not have permission to update applicant status.');
      } else {
        alert('Failed to update status');
      }
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const loadApplicantResumes = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/admin/applicants/${applicant.id}/resumes`,
        { headers: getAuthHeaders() }
      );

      if (response.data.success && response.data.resumes.length > 0) {
        setAllResumes(response.data.resumes);
        const firstResume = response.data.resumes[0];
        setCurrentResume(firstResume);
        await loadResumeBlob(firstResume.path);
      } else {
        setAllResumes([]);
        setCurrentResume(null);
        setResumeUrl(null);
      }
    } catch (error) {
      console.error('Error loading resumes:', error);
      setAllResumes([]);
      setCurrentResume(null);
      setResumeUrl(null);
    }
  };

  const loadResumeBlob = async (resumePath) => {
    try {
      const response = await axios.get(
        `${API_URL}/resume/${resumePath}`,
        {
          headers: getAuthHeaders(),
          responseType: 'blob'
        }
      );
      const url = window.URL.createObjectURL(response.data);
      setResumeUrl(url);
    } catch (error) {
      console.error('Error loading resume blob:', error);
      setResumeUrl(null);
    }
  };

  const handleResumeUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const allowedTypes = ['application/pdf', 'application/msword', 
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
      setResumeUploadError('Invalid file type. Please upload PDF or Word document.');
      return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setResumeUploadError('File size exceeds 10 MB limit.');
      return;
    }

    setIsUploadingResume(true);
    setResumeUploadError('');
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API_URL}/admin/applicants/${applicant.id}/resume`,
        formData,
        {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      if (response.data.success) {
        setResumeUploadError('');
        await loadApplicantResumes();
        alert('Resume uploaded successfully!');
      } else {
        setResumeUploadError(response.data.message || 'Upload failed');
      }
    } catch (error) {
      console.error('Resume upload error:', error);
      setResumeUploadError(error.response?.data?.message || 'Failed to upload resume');
    } finally {
      setIsUploadingResume(false);
      event.target.value = '';
    }
  };

  const handleDeleteResume = async (filename) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) {
      return;
    }

    try {
      const response = await axios.delete(
        `${API_URL}/admin/applicants/${applicant.id}/resume/${filename}`,
        { headers: getAuthHeaders() }
      );

      if (response.data.success) {
        await loadApplicantResumes();
      } else {
        setResumeUploadError(response.data.message || 'Failed to delete resume');
      }
    } catch (error) {
      console.error('Error deleting resume:', error);
      setResumeUploadError('Failed to delete resume');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  // Get speech evaluations
  const getSpeechEvaluations = () => {
    if (!applicant) return [];
    return applicant.speech_eval || [];
  };

  const getSpeechEvaluationsCount = () => {
    return getSpeechEvaluations().length;
  };

  // Filter typing test evaluations
  const getTypingTestEvaluations = () => {
    if (!applicant) return [];
    return applicant.typing_test || [];
  };

  // Get listening test evaluations
  const getListeningTestEvaluations = () => {
    if (!applicant) return [];
      return applicant.listening_test || [];
  };

  const getListeningTestEvaluationsCount = () => {
    return getListeningTestEvaluations().length;
  };

  // Get written test evaluations
  const getWrittenTestEvaluations = () => {
    if (!applicant) return [];
    return applicant.written_test || [];
  };

  // Get personality test evaluations
  const getPersonalityTestEvaluations = () => {
    if (!applicant) return [];
    return applicant.personality_test || [];
  };

  const getPersonalityTestEvaluationsCount = () => {
    return getPersonalityTestEvaluations().length;
  };

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

  if (!applicant) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{applicant.applicant_info?.lastName}, {applicant.applicant_info?.firstName} - Detailed Evaluation</h2>
          <div className="modal-header-badges">
            <select 
              className="status-dropdown"
              value={applicantStatus}
              onChange={(e) => handleStatusChange(e.target.value)}
              disabled={isUpdatingStatus}
            >
              <option value="new">🔵 New</option>
              <option value="pending">🟡 Pending</option>
              <option value="approved">🟢 Approved</option>
              <option value="rejected">🔴 Rejected</option>
            </select>
          </div>
          <button 
            onClick={onClose}
            className="close-button"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="applicant-details">
            <div className="details-header">
              <h3>Applicant Information</h3>
            </div>
            
            <div className="details-grid">
              <div><strong>Name:</strong> {applicant.applicant_info?.lastName}, {applicant.applicant_info?.firstName}</div>
              <div><strong>Position Applied:</strong> {applicant.applicant_info?.positionApplied}</div>
              <div><strong>Email:</strong> {applicant.applicant_info?.email}</div>
              <div><strong>Date of Birth:</strong> {applicant.applicant_info?.dateOfBirth}</div>
              <div><strong>Gender:</strong> {applicant.applicant_info?.gender}</div>
              <div><strong>Civil Status:</strong> {applicant.applicant_info?.civilStatus}</div>
              <div><strong>Cell Phone:</strong> {applicant.applicant_info?.cellphoneNumber}</div>
              <div><strong>Landline:</strong> {applicant.applicant_info?.landlineNumber}</div>
              <div><strong>Application Date:</strong> {formatDate(applicant.application_timestamp)}</div>
              {applicant.completion_timestamp && (
                <div><strong>Completion Date:</strong> {formatDate(applicant.completion_timestamp)}</div>
              )}
            </div>
            
            {/* Dropdown Toggle Buttons */}
            <div className="details-toggle-container">
              <button 
                className={`details-toggle-button ${showExtendedDetails ? 'expanded' : ''}`}
                onClick={() => setShowExtendedDetails(!showExtendedDetails)}
              >
                {showExtendedDetails ? '▼ Show Less Details' : '▶ Show More Details'}
              </button>
              <button 
                className={`details-toggle-button ${showResume ? 'expanded' : ''}`}
                onClick={() => setShowResume(!showResume)}
              >
                {showResume ? '▼ Hide Resume' : '▶ Show Resume'}
              </button>
            </div>
            
            {/* Extended Details Section */}
            {showExtendedDetails && (
              <div className="extended-details">
                <h4>Personal Information</h4>
                <div className="extended-details-grid">
                  <div><strong>TIN:</strong> {applicant.applicant_info?.tin || 'N/A'}</div>
                  <div><strong>SSS:</strong> {applicant.applicant_info?.sss || 'N/A'}</div>
                  <div><strong>Philhealth:</strong> {applicant.applicant_info?.philhealth || 'N/A'}</div>
                  <div><strong>HDMF (Pag-ibig):</strong> {applicant.applicant_info?.hdmf || 'N/A'}</div>
                  <div><strong>Mother's Maiden Name:</strong> {applicant.applicant_info?.mothersMaidenName || 'N/A'}</div>
                  <div><strong>Mother's Occupation:</strong> {applicant.applicant_info?.mothersOccupation || 'N/A'}</div>
                  <div><strong>Father's Name:</strong> {applicant.applicant_info?.fathersName || 'N/A'}</div>
                  <div><strong>Father's Occupation:</strong> {applicant.applicant_info?.fathersOccupation || 'N/A'}</div>
                </div>
                
                <h4>Addresses</h4>
                <div className="extended-details-grid">
                  <div><strong>City Address:</strong> {applicant.applicant_info?.cityAddress || 'N/A'}</div>
                  <div><strong>Provincial Address:</strong> {applicant.applicant_info?.provincialAddress || 'N/A'}</div>
                </div>

                <h4>Educational Attainment</h4>
                <div className="education-details">
                  <div className="education-section">
                    <h5>High School</h5>
                    <p><strong>Finished:</strong> {applicant.applicant_info?.highSchoolFinish === 'yes' ? 'Yes' : applicant.applicant_info?.highSchoolFinish === 'no' ? 'No' : 'N/A'}</p>
                    <p><strong>School:</strong> {applicant.applicant_info?.highSchoolName || 'N/A'}</p>
                    <p><strong>Years:</strong> {applicant.applicant_info?.highSchoolYears || 'N/A'}</p>
                  </div>
                  
                  <div className="education-section">
                    <h5>College/University</h5>
                    <p><strong>Finished:</strong> {applicant.applicant_info?.collegeFinish === 'yes' ? 'Yes' : applicant.applicant_info?.collegeFinish === 'no' ? 'No' : 'N/A'}</p>
                    <p><strong>School:</strong> {applicant.applicant_info?.collegeName || 'N/A'}</p>
                    <p><strong>Years:</strong> {applicant.applicant_info?.collegeYears || 'N/A'}</p>
                  </div>
                  
                  <div className="education-section">
                    <h5>Vocational</h5>
                    <p><strong>Finished:</strong> {applicant.applicant_info?.vocationalFinish === 'yes' ? 'Yes' : applicant.applicant_info?.vocationalFinish === 'no' ? 'No' : 'N/A'}</p>
                    <p><strong>School:</strong> {applicant.applicant_info?.vocationalName || 'N/A'}</p>
                    <p><strong>Years:</strong> {applicant.applicant_info?.vocationalYears || 'N/A'}</p>
                  </div>
                  
                  <div className="education-section">
                    <h5>Master's Degree</h5>
                    <p><strong>Finished:</strong> {applicant.applicant_info?.mastersFinish === 'yes' ? 'Yes' : applicant.applicant_info?.mastersFinish === 'no' ? 'No' : 'N/A'}</p>
                    <p><strong>School:</strong> {applicant.applicant_info?.mastersName || 'N/A'}</p>
                    <p><strong>Years:</strong> {applicant.applicant_info?.mastersYears || 'N/A'}</p>
                  </div>
                </div>

                <h4>Work History</h4>
                <div className="work-history-details">
                  {applicant.applicant_info?.workHistory && applicant.applicant_info.workHistory.length > 0 ? (
                    applicant.applicant_info.workHistory.map((work, index) => (
                      <div key={index} className="work-entry">
                        <h5>Company {index + 1}</h5>
                        <p><strong>Company Name:</strong> {work.companyName || 'N/A'}</p>
                        <p><strong>Date of Tenure:</strong> {work.dateOfTenure || 'N/A'}</p>
                        <p><strong>Reasons for Leaving:</strong> {work.reasonsForLeaving || 'N/A'}</p>
                        <p><strong>Salary:</strong> {work.salary || 'N/A'}</p>
                      </div>
                    ))
                  ) : (
                    <p>No work history available</p>
                  )}
                </div>
              </div>
            )}

            {/* Resume Section */}
            {showResume && (
              <div className="resume-section">
                <h3>Resume</h3>
                
                {/* Upload Section */}
                <div className="resume-upload-section">
                  <input
                    type="file"
                    id="resumeInput"
                    accept=".pdf,.doc,.docx"
                    onChange={handleResumeUpload}
                    disabled={isUploadingResume}
                    style={{ display: 'none' }}
                  />
                  <button
                    className="upload-button"
                    onClick={() => document.getElementById('resumeInput').click()}
                    disabled={isUploadingResume}
                  >
                    {isUploadingResume ? '⏳ Uploading...' : '📤 Upload Resume'}
                  </button>
                  {resumeUploadError && (
                    <div className="upload-error-message">{resumeUploadError}</div>
                  )}
                </div>

                {/* Resume Viewer */}
                {currentResume ? (
                  <div className="resume-viewer-section">
                    <div className="resume-info">
                      <p><strong>Current Resume:</strong> {currentResume.filename}</p>
                      <p><strong>Uploaded:</strong> {formatDate(currentResume.uploaded_at)}</p>
                    </div>
                    {resumeUrl ? (
                      <div className="resume-viewer">
                        <iframe
                          src={resumeUrl}
                          type="application/pdf"
                          width="100%"
                          height="700"
                          title="Applicant Resume"
                        />
                      </div>
                    ) : (
                      <div style={{ padding: '20px', textAlign: 'center', color: '#718096' }}>
                        Loading resume...
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="no-resume-message">
                    <p>No resume uploaded yet. Click "Upload Resume" to add one.</p>
                  </div>
                )}

                {/* Resume History */}
                {allResumes.length > 0 && (
                  <div className="resume-history">
                    <h4>Resume History</h4>
                    <div className="resume-list">
                      {allResumes.map((resume) => (
                        <div key={resume.filename} className="resume-item">
                          <div className="resume-item-info">
                            <span className="resume-filename">{resume.filename}</span>
                            <span className="resume-date">{formatDate(resume.uploaded_at)}</span>
                            <span className="resume-size">({(resume.size / 1024).toFixed(2)} KB)</span>
                          </div>
                          <div className="resume-item-actions">
                            {resume.filename !== currentResume?.filename && (
                              <button
                                className="view-button"
                                onClick={async () => {
                                  setCurrentResume(resume);
                                  await loadResumeBlob(resume.path);
                                }}
                              >
                                View
                              </button>
                            )}
                            <button
                              className="delete-button"
                              onClick={() => handleDeleteResume(resume.filename)}
                              title="Delete this resume"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Tab Navigation */}
          <div className="modal-tabs">
            <button 
              className={`tab-button ${activeTab === 'speech-evaluation' ? 'active' : ''}`}
              onClick={() => setActiveTab('speech-evaluation')}
            >
              Speech Evaluation ({getSpeechEvaluationsCount()})
            </button>
            <button 
              className={`tab-button ${activeTab === 'listening-test' ? 'active' : ''}`}
              onClick={() => setActiveTab('listening-test')}
            >
              Listening Test ({getListeningTestEvaluationsCount()})
            </button>
            <button 
              className={`tab-button ${activeTab === 'written-test' ? 'active' : ''}`}
              onClick={() => setActiveTab('written-test')}
            >
              Written Test ({getWrittenTestEvaluations().length})
            </button>
            <button 
              className={`tab-button ${activeTab === 'typing-test' ? 'active' : ''}`}
              onClick={() => setActiveTab('typing-test')}
            >
              Typing Test ({getTypingTestEvaluations().length})
            </button>
            <button 
              className={`tab-button ${activeTab === 'personality-test' ? 'active' : ''}`}
              onClick={() => setActiveTab('personality-test')}
            >
              Personality Test ({getPersonalityTestEvaluationsCount()})
            </button>
            <button 
              className={`tab-button ${activeTab === 'comments' ? 'active' : ''}`}
              onClick={() => setActiveTab('comments')}
            >
              💬 Comments ({comments.length})
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'speech-evaluation' && (
              <div className="evaluations-section">
                <h3>Speech Evaluations ({getSpeechEvaluationsCount()})</h3>
                {getSpeechEvaluations().length > 0 ? (
                  getSpeechEvaluations().map((evaluation, index) => (
                    <div key={`eval_${applicant.id}_${index}`} className="evaluation-item">
                      <div className="evaluation-header">
                        <h4>Question {index + 1}</h4>
                        <span className="score-badge">Score: {evaluation.evaluation?.score || 0}/10</span>
                      </div>
                      
                      <div className="evaluation-content">
                        <p><strong>Question:</strong> {evaluation.question}</p>
                        <p><strong>Transcript:</strong> {evaluation.transcript || 'No transcript available'}</p>
                        
                        {evaluation.audio_path && (
                          <div className="audio-player-section">
                            <h5>Audio Recording:</h5>
                            <audio controls className="audio-player" onError={(e) => {
                              console.warn(`Audio file not found: ${evaluation.audio_path}`);
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'block';
                            }}>
                              <source src={`${API_URL}/recordings/${evaluation.audio_path}`} type="audio/wav" />
                              Your browser does not support the audio element.
                            </audio>
                            <div style={{display: 'none', color: '#ef4444', fontSize: '0.875rem', fontStyle: 'italic'}}>
                              Audio file not available
                            </div>
                            <small style={{color: '#6b7280', fontSize: '0.75rem', marginTop: '5px', display: 'block'}}>
                              File: {evaluation.audio_path}
                            </small>
                          </div>
                        )}
                      
                        <div className="category-scores">
                          <h5>Category Scores:</h5>
                          <div className="scores-grid">
                            {evaluation.evaluation?.category_scores && 
                              Object.entries(evaluation.evaluation.category_scores).map(([category, score]) => (
                                <div key={category} className="category-score">
                                  <span>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>
                                  <span className="score">{score}/10</span>
                                </div>
                              ))
                            }
                          </div>
                        </div>

                        <div className="feedback-section">
                          <h5>Feedback:</h5>
                          <p>{evaluation.comment || 'No feedback available'}</p>
                        </div>

                    {/*    <div className="audio-metrics">
                          <h5>Audio Metrics:</h5>
                          <div className="metrics-grid">
                            <span>Duration: {evaluation.audio_metrics?.duration?.toFixed(2)}s</span>
                            <span>Avg Pitch: {evaluation.audio_metrics?.avg_pitch_hz?.toFixed(1)}Hz</span>
                            <span>WPM: {evaluation.audio_metrics?.estimated_wpm?.toFixed(0)}</span>
                          </div>
                        </div> */}

                        <p className="timestamp">
                          <small>Recorded: {formatDate(evaluation.timestamp)}</small>
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>No evaluations available for this applicant.</p>
                )}
              </div>
            )}

            {activeTab === 'listening-test' && (
              <div className="evaluations-section">
                <h3>Listening Test Results ({getListeningTestEvaluationsCount()})</h3>
                {getListeningTestEvaluations().length > 0 ? (
                  getListeningTestEvaluations().map((listeningEval, index) => (
                    <div key={`listening_${applicant.id}_${index}`} className="evaluation-item">
                      <div className="evaluation-header">
                        <h4>Listening Test #{index + 1}</h4>
                        <span className="score-badge">Accuracy: {(listeningEval.accuracy_percentage / 10).toFixed(1)}/10</span>
                      </div>
                      
                      <div className="evaluation-content">
                        <p><strong>Question:</strong> {listeningEval.question_text || 'No question text available'}</p>
                        <p><strong>Transcript:</strong> {listeningEval.transcript || 'No transcript available'}</p>

                        {listeningEval.audio_path && (
                          <div className="audio-player-section">
                            <h5>Audio Recording:</h5>
                            <audio controls className="audio-player" onError={(e) => {
                              console.warn(`Audio file not found: ${listeningEval.audio_path}`);
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'block';
                            }}>
                              <source src={`${API_URL}/recordings/${listeningEval.audio_path}`} type="audio/wav" />
                              Your browser does not support the audio element.
                            </audio>
                            <div style={{display: 'none', color: '#ef4444', fontSize: '0.875rem', fontStyle: 'italic'}}>
                              Audio file not available
                            </div>
                            <small style={{color: '#6b7280', fontSize: '0.75rem', marginTop: '5px', display: 'block'}}>
                              File: {listeningEval.audio_path}
                            </small>
                          </div>
                        )}

                        <div className="feedback-section">
                          <h5>Result:</h5>
                          <p>{listeningEval.is_correct ? 'Correct' : 'Incorrect'}</p>
                        </div>

                        <p className="timestamp">
                          <small>Completed: {formatDate(listeningEval.timestamp)}</small>
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>No evaluations available for this applicant.</p>
                )}
              </div>
            )}

            {activeTab === 'written-test' && (
              <div className="evaluations-section">
                <h3>Written Test Results ({getWrittenTestEvaluations().length})</h3>
                {getWrittenTestEvaluations().length > 0 ? (
                  getWrittenTestEvaluations().map((writtenEval, index) => (
                    <div key={`written_${applicant.id}_${index}`} className="evaluation-item">
                      <div className="evaluation-header">
                        <h4>Written Test #{index + 1}</h4>
                        <span className="score-badge">Score: {writtenEval.score_percentage || 0}%</span>
                      </div>
                      
                      <div className="evaluation-content">
                        <div className="written-test-summary">
                          <h5>Test Summary:</h5>
                          <div className="written-stats-grid">
                            <div className="written-stat">
                              <span className="stat-label">Total Questions:</span>
                              <span className="stat-value">{writtenEval.total_questions || 0}</span>
                            </div>
                            <div className="written-stat">
                              <span className="stat-label">Correct Answers:</span>
                              <span className="stat-value">{writtenEval.correct_answers || 0}</span>
                            </div>
                            <div className="written-stat">
                              <span className="stat-label">Score:</span>
                              <span className="stat-value">{writtenEval.score_percentage || 0}%</span>
                            </div>
                            <div className="written-stat">
                              <span className="stat-label">Completion Time:</span>
                              <span className="stat-value">{writtenEval.completion_time || 0}s</span>
                            </div>
                          </div>
                        </div>

                        {writtenEval.question_results && writtenEval.question_results.length > 0 && (
                          <div className="question-breakdown">
                            <h5>Question Breakdown:</h5>
                            <div className="questions-list">
                              {writtenEval.question_results.map((result, qIndex) => (
                                <div key={qIndex} className={`question-result-item ${result.is_correct ? 'correct' : 'incorrect'}`}>
                                  <div className="question-result-header">
                                    <span className="question-number">Q{qIndex + 1}</span>
                                    <span className={`result-indicator ${result.is_correct ? 'correct' : 'incorrect'}`}>
                                      {result.is_correct ? '✓' : '✗'}
                                    </span>
                                  </div>
                                  <div className="question-result-content">
                                    <p className="question-text">{result.question}</p>
                                    <div className="answer-details">
                                      <p><strong>Answer:</strong> {result.submitted_answer_display || `Option ${(result.submitted_answer || result.submitted_answer_index) + 1}`}</p>
                                      {!result.is_correct && (
                                        <p><strong>Correct Answer:</strong> {result.correct_answer_display || `Option ${(result.correct_answer || result.correct_answer_index) + 1}`}</p>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <p className="timestamp">
                          <small>Completed: {formatDate(writtenEval.timestamp)}</small>
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-written-results">
                    <p>No written test results available for this applicant.</p>
                    <p className="written-note">
                      <small>
                        Note: Written test results will appear here once the applicant completes the written test.
                      </small>
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'typing-test' && (
              <div className="typing-test-section">
                <h3>Typing Test Results ({getTypingTestEvaluations().length})</h3>
                {getTypingTestEvaluations().length > 0 ? (
                  getTypingTestEvaluations().map((typingEval, index) => (
                    <div key={`typing_${applicant.id}_${index}`} className="typing-evaluation-item">
                      <div className="typing-evaluation-header">
                        <h4>Typing Test #{index + 1}</h4>
                        <span className="wpm-badge">WPM: {typingEval.words_per_minute}</span>
                      </div>
                      
                      <div className="typing-evaluation-content">
                        <div className="typing-stats-grid">
                          <div className="typing-stat">
                            <span className="stat-label">Words Per Minute:</span>
                            <span className="stat-value">{typingEval.words_per_minute}</span>
                          </div>
                          <div className="typing-stat">
                            <span className="stat-label">Accuracy:</span>
                            <span className="stat-value">{typingEval.accuracy_percentage}%</span>
                            </div>
                          <div className="typing-stat">
                            <span className="stat-label">Words Typed:</span>
                            <span className="stat-value">{typingEval.typed_words}</span>
                          </div>
                          <div className="typing-stat">
                            <span className="stat-label">Time Taken:</span>
                            <span className="stat-value">{typingEval.time_taken_seconds}s</span>
                          </div>
                        </div>

                        <div className="typed-text-section">
                          <h5>Typed Text:</h5>
                          <div className="typed-text-display">
                            {typingEval.typed_text || 'No text available'}
                          </div>
                        </div>

                        <div className="test-info">
                          <h5>Test Information:</h5>
                          <div className="test-info-grid">
                            <span><strong>Test ID:</strong> {typingEval.test_id}</span>
                            <span><strong>Type:</strong> {typingEval.type}</span>
                          </div>
                        </div>

                        <p className="timestamp">
                          <small>Completed: {formatDate(typingEval.timestamp)}</small>
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-typing-results">
                    <p>No typing test results available for this applicant.</p>
                    <p className="typing-note">
                      <small>
                        Note: Typing test results will appear here once the applicant completes the typing test.
                      </small>
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'personality-test' && (
              <div className="evaluations-section">
                <h3>Personality Test Results ({getPersonalityTestEvaluationsCount()})</h3>
                {getPersonalityTestEvaluations().length > 0 ? (
                  getPersonalityTestEvaluations().map((personalityEval, index) => (
                    <div key={`personality_${applicant.id}_${index}`} className="evaluation-item">
                      <div className="evaluation-header">
                        <h4>Personality Test #{index + 1}</h4>
                        <span className="score-badge">Questions: {personalityEval.total_questions || 0}</span>
                      </div>
                      
                      <div className="evaluation-content">
                        <div className="personality-test-summary">
                          <h5>Test Summary:</h5>
                          <div className="written-stats-grid">
                            <div className="written-stat">
                              <span className="stat-label">Total Questions:</span>
                              <span className="stat-value">{personalityEval.total_questions || 0}</span>
                            </div>
                            <div className="written-stat">
                              <span className="stat-label">Completion Time:</span>
                              <span className="stat-value">{personalityEval.completion_time || 0}s</span>
                            </div>
                            <div className="written-stat">
                              <span className="stat-label">Categories Passed:</span>
                              <span className="stat-value">
                                {personalityEval.category_analysis ? 
                                  Object.values(personalityEval.category_analysis).filter(cat => cat.passed).length : 0
                                }/5
                              </span>
                            </div>
                            <div className="written-stat">
                              <span className="stat-label">Overall Performance:</span>
                              <span className="stat-value">
                                {personalityEval.category_analysis ? 
                                  Math.round(Object.values(personalityEval.category_analysis).reduce((sum, cat) => sum + (cat.percentage || 0), 0) / 5) : 0
                                }%
                              </span>
                            </div>
                          </div>
                          
                          <div className="category-scores-summary">
                            <h6>Category Scores Overview:</h6>
                            <div className="category-scores-list">
                              {personalityEval.category_analysis ? (
                                Object.entries(personalityEval.category_analysis).map(([category, data]) => (
                                  <div key={category} className="category-score-item">
                                    <span className="category-label">
                                      {category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                    </span>
                                    <span className={`category-score-value ${data.passed ? 'passed' : 'failed'}`}>
                                      {data.score || 0}/10 ({data.percentage || 0}%)
                                      {data.passed ? ' ✅' : ' ❌'}
                                    </span>
                                  </div>
                                ))
                              ) : personalityEval.trait_analysis ? (
                                <div className="legacy-data-notice">
                                  <p style={{color: '#6b7280', fontStyle: 'italic'}}>
                                    Legacy personality data detected. Please retake the personality test with the updated format.
                                  </p>
                                </div>
                              ) : (
                                <div className="no-data-notice">
                                  <p style={{color: '#6b7280', fontStyle: 'italic'}}>
                                    No category analysis data available.
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>




                        {personalityEval.question_results && personalityEval.question_results.length > 0 && (
                          <div className="question-breakdown">
                            <h5>Question Responses:</h5>
                            <div className="personality-questions-list">
                              {personalityEval.question_results.map((result, qIndex) => (
                                <div key={qIndex} className="personality-question-item">
                                  <div className="personality-question-header">
                                    <span className="question-number">Q{qIndex + 1}</span>
                                    <span className="question-category">{result.category || 'General'}</span>
                                  </div>
                                  <div className="personality-question-content">
                                    <p className="question-text">{result.question}</p>
                                    <div className="answer-details">
                                      <p><strong>Response:</strong> {result.selected_option || 'No response'}</p>
                                      <p><strong>Correct Answer:</strong> {result.correct_answer || 'Unknown'}</p>
                                      <p><strong>Result:</strong> 
                                        <span className={`result-status ${result.is_correct ? 'correct' : 'incorrect'}`}>
                                          {result.is_correct ? ' ✅ Correct' : ' ❌ Incorrect'}
                                        </span>
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <p className="timestamp">
                          <small>Completed: {formatDate(personalityEval.timestamp)}</small>
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-personality-results">
                    <p>No personality test results available for this applicant.</p>
                    <p className="personality-note">
                      <small>
                        Note: Personality test results will appear here once the applicant completes the personality assessment.
                      </small>
                    </p>
                  </div>
                )}
              </div>
            )}

                         {activeTab === 'comments' && (
               <div className="comments-section">
                 <h3>Comments ({comments.length})</h3>
                 {commentsError && <p style={{ color: 'red' }}>{commentsError}</p>}
                 <div className="comment-list">
                   {comments.length > 0 ? (
                     comments.map((comment) => {
                       // Check if current user can delete this comment
                       const canDelete = 
                         (comment.user_id && comment.user_id === currentUser?.id) || // Own comment
                         (currentUser?.permissions?.includes('delete_comments')) || // Has permission
                         (currentUser?.permissions?.includes('*')); // Super admin
                       
                       return (
                         <div key={comment.id} className="comment-item">
                           <div className="comment-header">
                             <div className="comment-author">
                               <strong>{comment.evaluator}</strong>
                               {comment.user_role && (
                                 <span className={`role-badge role-${comment.user_role}`}>
                                   {comment.user_role.replace('_', ' ')}
                                 </span>
                               )}
                             </div>
                             <div className="comment-meta">
                               <span className="comment-timestamp">{formatDate(comment.timestamp)}</span>
                               {canDelete && (
                                 <button 
                                   onClick={() => deleteComment(comment.id)}
                                   className="delete-comment-button"
                                   title="Delete Comment"
                                 >
                                   🗑️
                                 </button>
                               )}
                             </div>
                           </div>
                           <p className="comment-text">{comment.comment}</p>
                         </div>
                       );
                     })
                   ) : (
                     <div className="no-comments">
                       <p>No comments yet. Be the first to add a comment!</p>
                     </div>
                   )}
                 </div>
                               <div className="add-comment-section">
                 <div className="comment-form-header">
                   <strong>Add Comment as: {currentUser?.full_name || currentUser?.username}</strong>
                   {currentUser?.role && (
                     <span className={`role-badge role-${currentUser.role}`}>
                       {currentUser.role.replace('_', ' ')}
                     </span>
                   )}
                 </div>
                 <textarea
                   placeholder="Add a new comment..."
                   value={newComment}
                   onChange={(e) => setNewComment(e.target.value)}
                   rows="3"
                   cols="50"
                 />
                 <button onClick={submitComment} disabled={isSubmittingComment || !newComment.trim()}>
                   {isSubmittingComment ? 'Submitting...' : 'Submit Comment'}
                 </button>
               </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDetailsModal;