import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AdminQuestions.css';

const API_URL = import.meta.env.VITE_API_URL;

const AdminListeningQuestions = ({ getAuthHeaders }) => {
  const [questions, setQuestions] = useState([]);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [newQuestion, setNewQuestion] = useState({
    text: '',
    active: true
  });

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/listening-test-questions`, {
        headers: getAuthHeaders()
      });
      setQuestions(response.data.questions || []);
    } catch (err) {
      console.error('Error fetching listening test questions:', err);
    }
  };

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_URL}/admin/listening-test-questions`, {
        text: newQuestion.text,
        active: newQuestion.active
      }, {
        headers: getAuthHeaders()
      });
      
      if (response.data.success) {
        setNewQuestion({ 
          text: '', 
          active: true 
        });
        fetchQuestions();
      }
    } catch (err) {
      console.error('Error adding listening test question:', err);
    }
  };

  const handleUpdateQuestion = async (questionId, updatedData) => {
    try {
      const response = await axios.put(`${API_URL}/admin/listening-test-questions/${questionId}`, updatedData, {
        headers: getAuthHeaders()
      });
      if (response.data.success) {
        setEditingQuestion(null);
        fetchQuestions();
      }
    } catch (err) {
      console.error('Error updating listening test question:', err);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
      return;
    }
    
    try {
      await axios.delete(`${API_URL}/admin/listening-test-questions/${questionId}`, {
        headers: getAuthHeaders()
      });
      setQuestions(questions.filter(q => q.id !== questionId));
      alert('Question deleted successfully!');
    } catch (err) {
      alert('Error deleting question: ' + err.message);
    }
  };

  const handleToggleActive = async (questionId, currentActive) => {
    try {
      await axios.put(`${API_URL}/admin/listening-test-questions/${questionId}`, {
        active: !currentActive
      }, {
        headers: getAuthHeaders()
      });
      fetchQuestions();
    } catch (err) {
      console.error('Error toggling question status:', err);
    }
  };

  const handleReloadQuestions = async () => {
    try {
      const response = await axios.post(`${API_URL}/admin/listening-test-questions/reload`, {}, {
        headers: getAuthHeaders()
      });
      if (response.data.success) {
        fetchQuestions();
      }
    } catch (err) {
      console.error('Error reloading listening test questions:', err);
    }
  };

  return (
    <div className="questions-management">
      <div className="questions-header">
        <h2>Listening Test Question Management</h2>
        <p className="description">Manage phrases that applicants will hear and repeat during listening tests.</p>
        <button onClick={handleReloadQuestions} className="refresh-button">
          🔄 Reload Questions
        </button>
      </div>

      <div className="add-question-section">
        <h3>Add New Listening Test Phrase</h3>
        <form onSubmit={handleAddQuestion} className="add-question-form">
          <div className="form-group">
            <label htmlFor="question-text">Phrase Text:</label>
            <textarea
              id="question-text"
              value={newQuestion.text}
              onChange={(e) => setNewQuestion({...newQuestion, text: e.target.value})}
              placeholder="Enter the phrase that applicants will hear and repeat..."
              required
              rows={3}
            />
          </div>
          
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={newQuestion.active}
                onChange={(e) => setNewQuestion({...newQuestion, active: e.target.checked})}
              />
              Active (include in evaluations)
            </label>
          </div>
          
          <button type="submit" className="add-question-button">
            ➕ Add Listening Test Phrase
          </button>
        </form>
      </div>

      <div className="questions-list">
        <h3>Current Listening Test Phrases ({questions.length})</h3>
        {questions.length === 0 ? (
          <p>No listening test phrases found.</p>
        ) : (
          questions.map((question) => (
            <div key={question.id} className="question-card">
              <div className="question-header">
                <h4>Phrase {question.id}</h4>
                <div className="question-status">
                  <span className={`status-badge ${question.active ? 'active' : 'inactive'}`}>
                    {question.active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              
              <div className="question-content">
                <p><strong>Phrase:</strong> {question.text}</p>
              </div>
              
              <div className="question-actions">
                <button
                  onClick={() => handleToggleActive(question.id, question.active)}
                  className={`toggle-button ${question.active ? 'deactivate' : 'activate'}`}
                >
                  {question.active ? '🔄 Deactivate' : '✅ Activate'}
                </button>
                <button
                  onClick={() => setEditingQuestion(question)}
                  className="edit-button"
                >
                  ✏️ Edit
                </button>
                <button
                  onClick={() => handleDeleteQuestion(question.id)}
                  className="delete-button"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modal for editing questions */}
      {editingQuestion && (
        <div className="questions-management">
          <div className="modal-overlay" onClick={() => setEditingQuestion(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Edit Listening Test Phrase {editingQuestion.id}</h2>
                <button 
                  onClick={() => setEditingQuestion(null)}
                  className="close-button"
                >
                  ✕
                </button>
              </div>

              <div className="modal-body">
                <form onSubmit={(e) => {
                  e.preventDefault();
                  handleUpdateQuestion(editingQuestion.id, {
                    text: editingQuestion.text,
                    active: editingQuestion.active
                  });
                }}>
                  <div className="form-group">
                    <label htmlFor="edit-question-text">Phrase Text:</label>
                    <textarea
                      id="edit-question-text"
                      value={editingQuestion.text}
                      onChange={(e) => setEditingQuestion({...editingQuestion, text: e.target.value})}
                      required
                      rows={3}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={editingQuestion.active}
                        onChange={(e) => setEditingQuestion({...editingQuestion, active: e.target.checked})}
                      />
                      Active (include in evaluations)
                    </label>
                  </div>
                  
                  <div className="modal-actions">
                    <button type="button" onClick={() => setEditingQuestion(null)} className="cancel-button">
                      Cancel
                    </button>
                    <button type="submit" className="save-button">
                      Save Changes
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminListeningQuestions; 