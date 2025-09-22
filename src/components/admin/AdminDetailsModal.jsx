import React, { useState, useEffect } from 'react';
import './AdminDetailsModal.css';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

const AdminDetailsModal = ({ applicant, onClose, getAuthHeaders, currentUser }) => {
  const [activeTab, setActiveTab] = useState('speech-evaluation');
  const [showExtendedDetails, setShowExtendedDetails] = useState(false);
  
  // Comments state
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [commentsError, setCommentsError] = useState('');

  // Load comments when modal opens or applicant changes
  useEffect(() => {
    if (applicant && applicant.id) {
      loadComments();
    }
  }, [applicant?.id]);

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
            <span className="storage-type-badge">
              {applicant.status === 'temporary' ? '🟡 Temporary' : '🟢 Permanent'}
            </span>
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
            
            {/* Dropdown Toggle Button */}
            <div className="details-toggle-container">
              <button 
                className={`details-toggle-button ${showExtendedDetails ? 'expanded' : ''}`}
                onClick={() => setShowExtendedDetails(!showExtendedDetails)}
              >
                {showExtendedDetails ? '▼ Show Less Details' : '▶ Show More Details'}
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
          </div>

          {/* Tab Navigation */}
          <div className="modal-tabs">
            <button 
              className={`tab-button ${activeTab === 'speech-evaluation' ? 'active' : ''}`}
              onClick={() => setActiveTab('speech-evaluation')}
            >
              🎤 Speech Evaluation ({getSpeechEvaluationsCount()})
            </button>
            <button 
              className={`tab-button ${activeTab === 'listening-test' ? 'active' : ''}`}
              onClick={() => setActiveTab('listening-test')}
            >
              📋 Listening Test ({getListeningTestEvaluationsCount()})
            </button>
            <button 
              className={`tab-button ${activeTab === 'written-test' ? 'active' : ''}`}
              onClick={() => setActiveTab('written-test')}
            >
              ✍️ Written Test ({getWrittenTestEvaluations().length})
            </button>
            <button 
              className={`tab-button ${activeTab === 'typing-test' ? 'active' : ''}`}
              onClick={() => setActiveTab('typing-test')}
            >
              ⌨️ Typing Test ({getTypingTestEvaluations().length})
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
                        <span className="score-badge">Accuracy: {listeningEval.accuracy_percentage}%</span>
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