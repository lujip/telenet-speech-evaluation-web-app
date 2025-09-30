import React from 'react';
import GenericWrittenTest from '../common/GenericWrittenTest.jsx';

const API_URL = import.meta.env.VITE_API_URL;

const PersonalityTest = ({ onComplete, onNext }) => {
  console.log("PersonalityTest component mounted");

  return (
    <GenericWrittenTest
      testType="personality"
      title="Personality Assessment"
      icon="🧠"
      instructions={[
        "This assessment contains questions about your work preferences and personality traits",
        "There are no right or wrong answers - answer honestly based on your natural preferences",
        "Each question offers multiple choice options - select the one that best describes you",
        "You can navigate between questions and change your answers before submitting",
        "Try to answer all questions for the most accurate assessment"
      ]}
      timerMinutes={15}
      fetchQuestionsUrl={`${API_URL}/personality/questions`}
      submitAnswersUrl={`${API_URL}/personality/submit`}
      maxQuestions={null} // Show all questions
      showQuestionNavigation={true}
      showTimer={true}
      onComplete={onComplete}
      onNext={onNext}
      containerClass="personality-test-wrapper"
      primaryColor="#667eea"
    />
  );
};

export default PersonalityTest;

