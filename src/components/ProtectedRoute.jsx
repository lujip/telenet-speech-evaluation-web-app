import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../contexts/SessionContext.jsx';

const ProtectedRoute = ({ children }) => {
  const { checkEvaluationAccess } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    if (!checkEvaluationAccess()) {
      navigate('/');
    }
  }, [checkEvaluationAccess, navigate]);

  return children;
};

export default ProtectedRoute; 