import React, { useState } from 'react'
import './ApplicantForm.css'
import Header from '../header/Header.jsx';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext.jsx';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

const ApplicantForm = () => {
  const navigate = useNavigate();
  const { startNewSession } = useSession();

  const [formData, setFormData] = useState({
    positionApplied: '',
    positionType: '',
    
    // Personal Information
    lastName: '',
    firstName: '',
    dateOfBirth: '',
    gender: '',
    civilStatus: '',
    email: '',
    tin: '',
    sss: '',
    philhealth: '',
    hdmf: '',
    landlineNumber: '',
    cellphoneNumber: '',
    mothersMaidenName: '',
    mothersOccupation: '',
    fathersName: '',
    fathersOccupation: '',
    cityAddress: '',
    provincialAddress: '',

    // Educational Attainment
    highSchoolFinish: '',
    highSchoolName: '',
    highSchoolYears: '',
    
    collegeFinish: '',
    collegeName: '',
    collegeYears: '',
    
    vocationalFinish: '',
    vocationalName: '',
    vocationalYears: '',
    
    mastersFinish: '',
    mastersName: '',
    mastersYears: '',

    // Work History
    workHistory: [{
      companyName: '',
      dateOfTenure: '',
      reasonsForLeaving: '',
      salary: ''
    }]
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

  const handleWorkHistoryChange = (index, field, value) => {
    const updatedWorkHistory = [...formData.workHistory];
    updatedWorkHistory[index][field] = value;
    setFormData(prev => ({
      ...prev,
      workHistory: updatedWorkHistory
    }));
  };

  const addWorkHistory = () => {
    setFormData(prev => ({
      ...prev,
      workHistory: [...prev.workHistory, {
        companyName: '',
        dateOfTenure: '',
        reasonsForLeaving: '',
        salary: ''
      }]
    }));
  };

  const removeWorkHistory = (index) => {
    if (formData.workHistory.length > 1) {
      const updatedWorkHistory = formData.workHistory.filter((_, i) => i !== index);
      setFormData(prev => ({
        ...prev,
        workHistory: updatedWorkHistory
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    // Required fields validation
    if (!formData.positionApplied.trim()) {
      newErrors.positionApplied = 'Position applied is required';
    }
    
    if (!formData.positionType) {
      newErrors.positionType = 'Position type is required';
    }
    
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }
    
    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.dateOfBirth) {
      newErrors.dateOfBirth = 'Date of birth is required';
    }
    
    if (!formData.gender) {
      newErrors.gender = 'Gender is required';
    }
    
    if (!formData.civilStatus) {
      newErrors.civilStatus = 'Civil status is required';
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
        applicant: {
          ...formData,
          applicant_status: 'new'  // Hidden status field for newly created applicants
        }
      };
      
      try {
        await axios.post(`${API_URL}/store_applicant`, applicantData);
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
    navigate('/tech-test');
  };

  const resetForm = () => {
    setFormData({
      positionApplied: '',
      positionType: '',
      lastName: '',
      firstName: '',
      dateOfBirth: '',
      gender: '',
      civilStatus: '',
      email: '',
      tin: '',
      sss: '',
      philhealth: '',
      hdmf: '',
      landlineNumber: '',
      cellphoneNumber: '',
      mothersMaidenName: '',
      mothersOccupation: '',
      fathersName: '',
      fathersOccupation: '',
      cityAddress: '',
      provincialAddress: '',
      highSchoolFinish: '',
      highSchoolName: '',
      highSchoolYears: '',
      collegeFinish: '',
      collegeName: '',
      collegeYears: '',
      vocationalFinish: '',
      vocationalName: '',
      vocationalYears: '',
      mastersFinish: '',
      mastersName: '',
      mastersYears: '',
      workHistory: [{
        companyName: '',
        dateOfTenure: '',
        reasonsForLeaving: '',
        salary: ''
      }]
    });
    setErrors({});
    setIsSubmitted(false);
  };

  // Check if form is complete (all required fields filled)
  const isFormComplete = () => {
    return formData.positionApplied.trim() && 
           formData.positionType &&
           formData.lastName.trim() && 
           formData.firstName.trim() && 
           formData.email.trim() && 
           formData.dateOfBirth &&
           formData.gender &&
           formData.civilStatus &&
           /\S+@\S+\.\S+/.test(formData.email);
  };

  if (isSubmitted) {
    return (
      <>
        <Header />
        <div className="box-container">
          <div className="success-container">
            <h2>Application Submitted Successfully!</h2>
            <p>Thank you, {formData.firstName} {formData.lastName}! Your application has been received.</p>
            <div className="applicant-summary">
              <h3>Application Summary:</h3>
              <p><strong>Name:</strong> {formData.lastName}, {formData.firstName}</p>
              <p><strong>Email:</strong> {formData.email}</p>
              <p><strong>Position Applied:</strong> {formData.positionApplied}</p>
              <p><strong>Position Type:</strong> {formData.positionType}</p>
              {formData.cellphoneNumber && <p><strong>Phone:</strong> {formData.cellphoneNumber}</p>}
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
            Please provide your complete details before starting the evaluation process.
          </p>
          
          <form onSubmit={handleSubmit} className="applicant-form">
            {/* Position Applied */}
            <div className="form-section">
              <h3>Position Applied</h3>
              
              <div className="form-group">
                <label htmlFor="positionApplied">Position Applied *</label>
                <input
                  type="text"
                  id="positionApplied"
                  name="positionApplied"
                  value={formData.positionApplied}
                  onChange={handleInputChange}
                  className={errors.positionApplied ? 'error' : ''}
                  placeholder="Enter position you're applying for"
                />
                {errors.positionApplied && <span className="error-message">{errors.positionApplied}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="positionType">Position Type *</label>
                <select
                  id="positionType"
                  name="positionType"
                  value={formData.positionType}
                  onChange={handleInputChange}
                  className={errors.positionType ? 'error' : ''}
                >
                  <option value="">Select position type</option>
                  <option value="voice">Voice</option>
                  <option value="non-voice">Non-Voice</option>
                </select>
                {errors.positionType && <span className="error-message">{errors.positionType}</span>}
              </div>
            </div>

            {/* Personal Information */}
            <div className="form-section">
              <h3>Personal Information</h3>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="lastName">Last Name *</label>
                  <input
                    type="text"
                    id="lastName"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    className={errors.lastName ? 'error' : ''}
                    placeholder="Enter your last name"
                  />
                  {errors.lastName && <span className="error-message">{errors.lastName}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="firstName">First Name *</label>
                  <input
                    type="text"
                    id="firstName"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    className={errors.firstName ? 'error' : ''}
                    placeholder="Enter your first name"
                  />
                  {errors.firstName && <span className="error-message">{errors.firstName}</span>}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="dateOfBirth">Date of Birth *</label>
                  <input
                    type="date"
                    id="dateOfBirth"
                    name="dateOfBirth"
                    value={formData.dateOfBirth}
                    onChange={handleInputChange}
                    className={errors.dateOfBirth ? 'error' : ''}
                  />
                  {errors.dateOfBirth && <span className="error-message">{errors.dateOfBirth}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="gender">Gender *</label>
                  <select
                    id="gender"
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className={errors.gender ? 'error' : ''}
                  >
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                  {errors.gender && <span className="error-message">{errors.gender}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="civilStatus">Civil Status *</label>
                  <select
                    id="civilStatus"
                    name="civilStatus"
                    value={formData.civilStatus}
                    onChange={handleInputChange}
                    className={errors.civilStatus ? 'error' : ''}
                  >
                    <option value="">Select civil status</option>
                    <option value="Single">Single</option>
                    <option value="Married">Married</option>
                    <option value="Divorced">Divorced</option>
                    <option value="Widowed">Widowed</option>
                  </select>
                  {errors.civilStatus && <span className="error-message">{errors.civilStatus}</span>}
                </div>
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

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="tin">TIN</label>
                  <input
                    type="text"
                    id="tin"
                    name="tin"
                    value={formData.tin}
                    onChange={handleInputChange}
                    placeholder="Enter your TIN"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="sss">SSS</label>
                  <input
                    type="text"
                    id="sss"
                    name="sss"
                    value={formData.sss}
                    onChange={handleInputChange}
                    placeholder="Enter your SSS number"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="philhealth">Philhealth</label>
                  <input
                    type="text"
                    id="philhealth"
                    name="philhealth"
                    value={formData.philhealth}
                    onChange={handleInputChange}
                    placeholder="Enter your Philhealth number"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="hdmf">HDMF (Pag-ibig)</label>
                  <input
                    type="text"
                    id="hdmf"
                    name="hdmf"
                    value={formData.hdmf}
                    onChange={handleInputChange}
                    placeholder="Enter your HDMF number"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="landlineNumber">Landline Number</label>
                  <input
                    type="tel"
                    id="landlineNumber"
                    name="landlineNumber"
                    value={formData.landlineNumber}
                    onChange={handleInputChange}
                    placeholder="Enter your landline number"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="cellphoneNumber">Cell Phone Number</label>
                  <input
                    type="tel"
                    id="cellphoneNumber"
                    name="cellphoneNumber"
                    value={formData.cellphoneNumber}
                    onChange={handleInputChange}
                    placeholder="Enter your cell phone number"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="mothersMaidenName">Mother's Maiden Name</label>
                  <input
                    type="text"
                    id="mothersMaidenName"
                    name="mothersMaidenName"
                    value={formData.mothersMaidenName}
                    onChange={handleInputChange}
                    placeholder="Enter your mother's maiden name"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="mothersOccupation">Mother's Occupation</label>
                  <input
                    type="text"
                    id="mothersOccupation"
                    name="mothersOccupation"
                    value={formData.mothersOccupation}
                    onChange={handleInputChange}
                    placeholder="Enter your mother's occupation"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="fathersName">Father's Name</label>
                  <input
                    type="text"
                    id="fathersName"
                    name="fathersName"
                    value={formData.fathersName}
                    onChange={handleInputChange}
                    placeholder="Enter your father's name"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="fathersOccupation">Father's Occupation</label>
                  <input
                    type="text"
                    id="fathersOccupation"
                    name="fathersOccupation"
                    value={formData.fathersOccupation}
                    onChange={handleInputChange}
                    placeholder="Enter your father's occupation"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="cityAddress">City Address</label>
                <textarea
                  id="cityAddress"
                  name="cityAddress"
                  value={formData.cityAddress}
                  onChange={handleInputChange}
                  placeholder="Enter your city address"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label htmlFor="provincialAddress">Provincial Address</label>
                <textarea
                  id="provincialAddress"
                  name="provincialAddress"
                  value={formData.provincialAddress}
                  onChange={handleInputChange}
                  placeholder="Enter your provincial address"
                  rows="3"
                />
              </div>
            </div>

            {/* Educational Attainment */}
            <div className="form-section">
              <h3>Educational Attainment</h3>
              
              {/* High School */}
              <div className="education-subsection">
                <h4>High School</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="highSchoolFinish">Finished High School</label>
                    <select
                      id="highSchoolFinish"
                      name="highSchoolFinish"
                      value={formData.highSchoolFinish}
                      onChange={handleInputChange}
                    >
                      <option value="">Please select</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="highSchoolName">Name of School</label>
                    <input
                      type="text"
                      id="highSchoolName"
                      name="highSchoolName"
                      value={formData.highSchoolName}
                      onChange={handleInputChange}
                      placeholder="Enter school name"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="highSchoolYears">Years Attended</label>
                    <input
                      type="text"
                      id="highSchoolYears"
                      name="highSchoolYears"
                      value={formData.highSchoolYears}
                      onChange={handleInputChange}
                      placeholder="e.g., 2015-2019"
                    />
                  </div>
                </div>
              </div>

              {/* College/University */}
              <div className="education-subsection">
                <h4>College/University</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="collegeFinish">Finished College/University</label>
                    <select
                      id="collegeFinish"
                      name="collegeFinish"
                      value={formData.collegeFinish}
                      onChange={handleInputChange}
                    >
                      <option value="">Please select</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="collegeName">Name of School</label>
                    <input
                      type="text"
                      id="collegeName"
                      name="collegeName"
                      value={formData.collegeName}
                      onChange={handleInputChange}
                      placeholder="Enter school name"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="collegeYears">Years Attended</label>
                    <input
                      type="text"
                      id="collegeYears"
                      name="collegeYears"
                      value={formData.collegeYears}
                      onChange={handleInputChange}
                      placeholder="e.g., 2019-2023"
                    />
                  </div>
                </div>
              </div>

              {/* Vocational */}
              <div className="education-subsection">
                <h4>Vocational</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="vocationalFinish">Finished Vocational</label>
                    <select
                      id="vocationalFinish"
                      name="vocationalFinish"
                      value={formData.vocationalFinish}
                      onChange={handleInputChange}
                    >
                      <option value="">Please select</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="vocationalName">Name of School</label>
                    <input
                      type="text"
                      id="vocationalName"
                      name="vocationalName"
                      value={formData.vocationalName}
                      onChange={handleInputChange}
                      placeholder="Enter school name"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="vocationalYears">Years Attended</label>
                    <input
                      type="text"
                      id="vocationalYears"
                      name="vocationalYears"
                      value={formData.vocationalYears}
                      onChange={handleInputChange}
                      placeholder="e.g., 2020-2022"
                    />
                  </div>
                </div>
              </div>

              {/* Master's */}
              <div className="education-subsection">
                <h4>Master's Degree</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="mastersFinish">Finished Master's</label>
                    <select
                      id="mastersFinish"
                      name="mastersFinish"
                      value={formData.mastersFinish}
                      onChange={handleInputChange}
                    >
                      <option value="">Please select</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="mastersName">Name of School</label>
                    <input
                      type="text"
                      id="mastersName"
                      name="mastersName"
                      value={formData.mastersName}
                      onChange={handleInputChange}
                      placeholder="Enter school name"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="mastersYears">Years Attended</label>
                    <input
                      type="text"
                      id="mastersYears"
                      name="mastersYears"
                      value={formData.mastersYears}
                      onChange={handleInputChange}
                      placeholder="e.g., 2023-2025"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Work History */}
            <div className="form-section">
              <h3>Work History</h3>
              
              {formData.workHistory.map((work, index) => (
                <div key={index} className="work-history-item">
                  <div className="work-history-header">
                    <h4>Company {index + 1}</h4>
                    {formData.workHistory.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeWorkHistory(index)}
                        className="btn btn-remove"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor={`companyName-${index}`}>Company Name</label>
                      <input
                        type="text"
                        id={`companyName-${index}`}
                        value={work.companyName}
                        onChange={(e) => handleWorkHistoryChange(index, 'companyName', e.target.value)}
                        placeholder="Enter company name"
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor={`dateOfTenure-${index}`}>Date of Tenure</label>
                      <input
                        type="text"
                        id={`dateOfTenure-${index}`}
                        value={work.dateOfTenure}
                        onChange={(e) => handleWorkHistoryChange(index, 'dateOfTenure', e.target.value)}
                        placeholder="e.g., Jan 2020 - Dec 2022"
                      />
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor={`reasonsForLeaving-${index}`}>Reasons for Leaving</label>
                      <input
                        type="text"
                        id={`reasonsForLeaving-${index}`}
                        value={work.reasonsForLeaving}
                        onChange={(e) => handleWorkHistoryChange(index, 'reasonsForLeaving', e.target.value)}
                        placeholder="Enter reasons for leaving"
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor={`salary-${index}`}>Salary</label>
                      <input
                        type="text"
                        id={`salary-${index}`}
                        value={work.salary}
                        onChange={(e) => handleWorkHistoryChange(index, 'salary', e.target.value)}
                        placeholder="Enter salary"
                      />
                    </div>
                  </div>
                </div>
              ))}

              <button
                type="button"
                onClick={addWorkHistory}
                className="btn btn-add-company"
              >
                Add Another Company
              </button>
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