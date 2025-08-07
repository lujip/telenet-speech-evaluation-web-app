import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AdminQuestions.css';

const AdminQuestions = () => {
  const [questions, setQuestions] = useState([]);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [newQuestion, setNewQuestion] = useState({
    text: '',
    keywords: '',
    active: true
  });

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await axios.get('http://localhost:5000/admin/questions');
      setQuestions(response.data.questions || []);
    } catch (err) {
      console.error('Error fetching questions:', err);
    }
  };

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    try {
      const keywordsArray = newQuestion.keywords.split(',').map(k => k.trim()).filter(k => k);
      
      const response = await axios.post('http://localhost:5000/admin/questions', {
        text: newQuestion.text,
        keywords: keywordsArray,
        active: newQuestion.active
      });
      
      if (response.data.success) {
        setNewQuestion({ text: '', keywords: '', active: true });
        fetchQuestions();
      }
    } catch (err) {
      console.error('Error adding question:', err);
    }
  };

  const handleUpdateQuestion = async (questionId, updatedData) => {
    try {
      const response = await axios.put(`http://localhost:5000/admin/questions/${questionId}`, updatedData);
      if (response.data.success) {
        setEditingQuestion(null);
        fetchQuestions();
      }
    } catch (err) {
      console.error('Error updating question:', err);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    try {
      await axios.delete(`http://localhost:5000/admin/questions/${questionId}`);
      setQuestions(questions.filter(q => q.id !== questionId));
      alert('Question deleted successfully!');
    } catch (err) {
      alert('Error deleting question: ' + err.message);
    }
  };

  const handleReloadQuestions = async () => {
    try {
      const response = await axios.post('http://localhost:5000/admin/questions/reload');
      if (response.data.success) {
        fetchQuestions();
      }
    } catch (err) {
      console.error('Error reloading questions:', err);
    }
  };

  return (
    <div className="questions-management">
      <div className="questions-header">
        <h2>Question Management</h2>
        <button onClick={handleReloadQuestions} className="refresh-button">
          🔄 Reload Questions
        </button>
      </div>

      <div className="add-question-section">
        <h3>Add New Question</h3>
        <form onSubmit={handleAddQuestion} className="add-question-form">
          <div className="form-group">
            <label htmlFor="question-text">Question Text:</label>
            <textarea
              id="question-text"
              value={newQuestion.text}
              onChange={(e) => setNewQuestion({...newQuestion, text: e.target.value})}
              placeholder="Enter the question text..."
              required
              rows={3}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="question-keywords">Keywords (comma-separated):</label>
            <input
              type="text"
              id="question-keywords"
              value={newQuestion.keywords}
              onChange={(e) => setNewQuestion({...newQuestion, keywords: e.target.value})}
              placeholder="calm, empathy, listen, resolve, apologize"
              required
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
            ➕ Add Question
          </button>
        </form>
      </div>

      <div className="questions-list">
        <h3>Current Questions ({questions.length})</h3>
        {questions.length === 0 ? (
          <p>No questions found.</p>
        ) : (
          questions.map((question) => (
            <div key={question.id} className="question-card">
              <div className="question-header">
                <h4>Question {question.id}</h4>
                <div className="question-status">
                  <span className={`status-badge ${question.active ? 'active' : 'inactive'}`}>
                    {question.active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              
              <div className="question-content">
                <p><strong>Text:</strong> {question.text}</p>
                <p><strong>Keywords:</strong> {question.keywords.join(', ')}</p>
              </div>
              
              <div className="question-actions">
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
                <h2>Edit Question {editingQuestion.id}</h2>
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
                  // Handle keywords - if it's a string, split it; if it's already an array, use it
                  const keywordsArray = typeof editingQuestion.keywords === 'string' 
                    ? editingQuestion.keywords.split(',').map(k => k.trim()).filter(k => k)
                    : editingQuestion.keywords;
                  handleUpdateQuestion(editingQuestion.id, {
                    text: editingQuestion.text,
                    keywords: keywordsArray,
                    active: editingQuestion.active
                  });
                }}>
                  <div className="form-group">
                    <label htmlFor="edit-question-text">Question Text:</label>
                    <textarea
                      id="edit-question-text"
                      value={editingQuestion.text}
                      onChange={(e) => setEditingQuestion({...editingQuestion, text: e.target.value})}
                      required
                      rows={3}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="edit-question-keywords">Keywords (comma-separated):</label>
                    <input
                      type="text"
                      id="edit-question-keywords"
                      value={Array.isArray(editingQuestion.keywords) ? editingQuestion.keywords.join(', ') : editingQuestion.keywords}
                      onChange={(e) => setEditingQuestion({...editingQuestion, keywords: e.target.value})}
                      required
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

export default AdminQuestions;
