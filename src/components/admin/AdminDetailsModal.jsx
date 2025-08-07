import React, { useState } from 'react';
import './AdminDetailsModal.css';

const AdminDetailsModal = ({ applicant, onClose }) => {
  const [activeTab, setActiveTab] = useState('speech-evaluation');

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (!applicant) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{applicant.applicant_info?.fullName} - Detailed Evaluation</h2>
          <button 
            onClick={onClose}
            className="close-button"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="applicant-details">
            <h3>Applicant Information</h3>
            <div className="details-grid">
              <div><strong>Full Name:</strong> {applicant.applicant_info?.fullName}</div>
              <div><strong>Email:</strong> {applicant.applicant_info?.email}</div>
              <div><strong>Role:</strong> {applicant.applicant_info?.role}</div>
              <div><strong>Phone:</strong> {applicant.applicant_info?.phone}</div>
              <div><strong>Experience:</strong> {applicant.applicant_info?.experience}</div>
              <div><strong>Current Company:</strong> {applicant.applicant_info?.currentCompany}</div>
              <div><strong>Application Date:</strong> {formatDate(applicant.application_timestamp)}</div>
              {applicant.completion_timestamp && (
                <div><strong>Completion Date:</strong> {formatDate(applicant.completion_timestamp)}</div>
              )}
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="modal-tabs">
            <button 
              className={`tab-button ${activeTab === 'speech-evaluation' ? 'active' : ''}`}
              onClick={() => setActiveTab('speech-evaluation')}
            >
              🎤 Speech Evaluation Result
            </button>
            <button 
              className={`tab-button ${activeTab === 'placeholder-1' ? 'active' : ''}`}
              onClick={() => setActiveTab('placeholder-1')}
            >
              📋 Personality Test Result
            </button>
            <button 
              className={`tab-button ${activeTab === 'placeholder-2' ? 'active' : ''}`}
              onClick={() => setActiveTab('placeholder-2')}
            >
              📋 IQ Test Result
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'speech-evaluation' && (
              <div className="evaluations-section">
                <h3>Evaluations ({applicant.evaluations?.length || 0})</h3>
                {applicant.evaluations && applicant.evaluations.length > 0 ? (
                  applicant.evaluations.map((evaluation, index) => (
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
                              <source src={`http://localhost:5000/recordings/${evaluation.audio_path}`} type="audio/wav" />
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

                        <div className="audio-metrics">
                          <h5>Audio Metrics:</h5>
                          <div className="metrics-grid">
                            <span>Duration: {evaluation.audio_metrics?.duration?.toFixed(2)}s</span>
                            <span>Avg Pitch: {evaluation.audio_metrics?.avg_pitch_hz?.toFixed(1)}Hz</span>
                            <span>WPM: {evaluation.audio_metrics?.estimated_wpm?.toFixed(0)}</span>
                          </div>
                        </div>

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

            {activeTab === 'placeholder-1' && (
              <div className="placeholder-content">
                <h3>Listen Test (Not implemented)</h3>
                <p>This is a placeholder tab. Content will be added here in the future.</p>
              </div>
            )}

            {activeTab === 'placeholder-2' && (
              <div className="placeholder-content">
                <h3>Typing Test (Not implemented)</h3>
                <p>This is a placeholder tab. Content will be added here in the future.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDetailsModal;