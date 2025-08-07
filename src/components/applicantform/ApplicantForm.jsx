import React, { useState } from 'react'
import './ApplicantForm.css'
import Header from '../header/Header.jsx';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';
import axios from 'axios';

const ApplicantForm = () => {
  const navigate = useNavigate();
  const { startNewSession } = useSession();

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    role: '',
    phone: '',
    experience: '',
    currentCompany: ''
  });

  const [errors, setErrors] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.role.trim()) {
      newErrors.role = 'Role applying for is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      setIsSubmitted(true);
      
      // Start new session with applicant data
      const sessionId = startNewSession(formData);
      
      // Send to backend for temporary storage
      const applicantData = {
        sessionId: sessionId,
        timestamp: new Date().toISOString(),
        applicant: formData
      };
      
      try {
        await axios.post('http://localhost:5000/store_applicant', applicantData);
        console.log('Applicant data sent to backend successfully');
      } catch (error) {
        console.error('Error sending applicant data to backend:', error);
        // Continue even if backend storage fails, as we have localStorage backup
      }
      
      // Log the data for debugging
      console.log('Applicant Data stored temporarily:', applicantData);
    }
  };

  const handleProceedToEvaluation = () => {
    navigate('/techtest');
  };

  const resetForm = () => {
    setFormData({
      fullName: '',
      email: '',
      role: '',
      phone: '',
      experience: '',
      currentCompany: ''
    });
    setErrors({});
    setIsSubmitted(false);
  };

  // Check if form is complete (all required fields filled)
  const isFormComplete = () => {
    return formData.fullName.trim() && 
           formData.email.trim() && 
           formData.role.trim() &&
           /\S+@\S+\.\S+/.test(formData.email);
  };

  if (isSubmitted) {
    return (
      <>
        <Header />
        <div className="box-container">
          <div className="success-container">
            <h2>Application Submitted Successfully!</h2>
            <p>Thank you, {formData.fullName}! Your application has been received.</p>
            <div className="applicant-summary">
              <h3>Application Summary:</h3>
              <p><strong>Name:</strong> {formData.fullName}</p>
              <p><strong>Email:</strong> {formData.email}</p>
              <p><strong>Role:</strong> {formData.role}</p>
              {formData.phone && <p><strong>Phone:</strong> {formData.phone}</p>}
              {formData.currentCompany && <p><strong>Current Company:</strong> {formData.currentCompany}</p>}
            </div>
            <div className="action-buttons">
              <button onClick={handleProceedToEvaluation} className="btn btn-submit">
                Proceed to Evaluation
              </button>
              <button onClick={resetForm} className="btn btn-reset">
                Submit Another Application
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="box-container">
        <div className="form-container">
          <h2>Applicant Information Form</h2>
          <p className="form-description">
            Please provide your basic details before starting the evaluation process.
          </p>
          
          <form onSubmit={handleSubmit} className="applicant-form">
            <div className="form-section">
              <h3>Personal Information</h3>
              
              <div className="form-group">
                <label htmlFor="fullName">Full Name *</label>
                <input
                  type="text"
                  id="fullName"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  className={errors.fullName ? 'error' : ''}
                  placeholder="Enter your full name"
                />
                {errors.fullName && <span className="error-message">{errors.fullName}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="email">Email Address *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={errors.email ? 'error' : ''}
                  placeholder="Enter your email address"
                />
                {errors.email && <span className="error-message">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="phone">Phone Number</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  placeholder="Enter your phone number"
                />
              </div>
            </div>

            <div className="form-section">
              <h3>Professional Information</h3>
              
              <div className="form-group">
                <label htmlFor="role">Role Applying For *</label>
                <input
                  type="text"
                  id="role"
                  name="role"
                  value={formData.role}
                  onChange={handleInputChange}
                  className={errors.role ? 'error' : ''}
                  placeholder="e.g., Agent, UX Designer, etc."
                />
                {errors.role && <span className="error-message">{errors.role}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="currentCompany">Current Company</label>
                <input
                  type="text"
                  id="currentCompany"
                  name="currentCompany"
                  value={formData.currentCompany}
                  onChange={handleInputChange}
                  placeholder="Enter your current company"
                />
              </div>

              <div className="form-group">
                <label htmlFor="experience">Years of Experience</label>
                <select
                  id="experience"
                  name="experience"
                  value={formData.experience}
                  onChange={handleInputChange}
                >
                  <option value="">Select experience level</option>
                  <option value="0-1">0-1 years</option>
                  <option value="1-3">1-3 years</option>
                  <option value="3-5">3-5 years</option>
                  <option value="5-8">5-8 years</option>
                  <option value="8+">8+ years</option>
                </select>
              </div>

            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-submit"
                disabled={!isFormComplete()}
              >
                Submit Application
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};

export default ApplicantForm;