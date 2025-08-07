import React from 'react';
import './App.css';
import Header from './components/header/Header.jsx';
import EvaluationPage from './components/evaluationpage/EvaluationPage.jsx';

const App = () => {
  return (
    <div>
      <Header/>
      <EvaluationPage />
    </div>
  );
};

export default App;