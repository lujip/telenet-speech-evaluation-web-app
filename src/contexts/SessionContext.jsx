import React, { createContext, useContext, useState, useEffect } from 'react';

const SessionContext = createContext();

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

export const SessionProvider = ({ children }) => {
  const [applicantInfo, setApplicantInfo] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isEvaluationStarted, setIsEvaluationStarted] = useState(false);

  // Initialize session from localStorage on mount
  useEffect(() => {
    const storedApplicant = localStorage.getItem('currentApplicant');
    const storedSessionId = localStorage.getItem('applicantSessionId');
    
    if (storedApplicant && storedSessionId) {
      try {
        const applicantData = JSON.parse(storedApplicant);
        setApplicantInfo(applicantData.applicant);
        setSessionId(storedSessionId);
      } catch (error) {
        console.error('Error parsing stored applicant data:', error);
        clearSession();
      }
    }
  }, []);

  const startNewSession = (applicantData) => {
    // Generate new session ID with more uniqueness
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15);
    const newSessionId = `${timestamp}_${random}`;
    
    // Store in localStorage
    const sessionData = {
      sessionId: newSessionId,
      timestamp: new Date().toISOString(),
      applicant: applicantData
    };
    
    localStorage.setItem('currentApplicant', JSON.stringify(sessionData));
    localStorage.setItem('applicantSessionId', newSessionId);
    
    // Update state
    setApplicantInfo(applicantData);
    setSessionId(newSessionId);
    setIsEvaluationStarted(false);
    
    return newSessionId;
  };

  const clearSession = () => {
    // Clear localStorage
    localStorage.removeItem('currentApplicant');
    localStorage.removeItem('applicantSessionId');
    
    // Clear state
    setApplicantInfo(null);
    setSessionId(null);
    setIsEvaluationStarted(false);
  };

  const startEvaluation = () => {
    if (!applicantInfo || !sessionId) {
      throw new Error('Cannot start evaluation without applicant info and session ID');
    }
    setIsEvaluationStarted(true);
  };

  const checkEvaluationAccess = () => {
    return !!(applicantInfo && sessionId);
  };

  const value = {
    applicantInfo,
    sessionId,
    isEvaluationStarted,
    startNewSession,
    clearSession,
    startEvaluation,
    checkEvaluationAccess
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}; 