import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';
import './CompletionPage.css';
import Header from '../header/Header.jsx';

const CompletionPage = () => {
  const navigate = useNavigate();
  const { clearSession } = useSession();

  const handleStartNew = () => {
    clearSession();
    navigate('/');
  };

  return (
    <div>
      <Header />
    <div className="main-content-vertical">
      <div className="box-container">
        <h1 className="completion-title">🎉 Evaluation Complete!</h1>
        <p className="completion-subtitle">Congratulations! You have successfully completed all three parts of the evaluation.</p>

        <div className="completion-summary">
          <h2>What You Completed:</h2>
          <div className="test-summary">
            <div className="test-item completed">
              <span className="test-icon">🎧</span>
              <div className="test-info">
                <h3>Listening Test</h3>
                <p>Repeated phrases accurately</p>
              </div>
            </div>
            
            <div className="test-item completed">
              <span className="test-icon">🗣️</span>
              <div className="test-info">
                <h3>Speech Evaluation</h3>
                <p>Answered interview questions</p>
              </div>
            </div>
            
            <div className="test-item completed">
              <span className="test-icon">⌨️</span>
              <div className="test-info">
                <h3>Typing Test</h3>
                <p>Demonstrated typing skills</p>
              </div>
            </div>

            <div className="test-item completed">
              <span className="test-icon">📝</span>
              <div className="test-info">
                <h3>Written Test</h3>
                <p>Completed knowledge assessment</p>
              </div>
            </div>
          </div>
        </div>

        <div className="completion-actions">
          <button onClick={handleStartNew} className="action-button primary">
            🆕 Start New Application
          </button>
        </div>

        <div className="completion-footer">
          <p>Your evaluation results have been saved and will be reviewed by our team.</p>
          <p>Thank you for your time and effort!</p>
        </div>
      </div>
    </div>
    </div>
  );
};

export default CompletionPage; 