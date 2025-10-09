import React from 'react';
import GenericWrittenTest from '../common/GenericWrittenTest.jsx';

const API_URL = import.meta.env.VITE_API_URL;

const WrittenTest = ({ onComplete, onNext }) => {
  console.log("WrittenTest component mounted");

  return (
    <GenericWrittenTest
      testType="written"
      title="Written Test"
      icon="📝"
      instructions={[
        "This test contains 20 randomly selected questions",
        "Answer all questions to the best of your ability",
        "Some questions are multiple choice, others require typed answers",
        "Read each question carefully before answering",
        "You can navigate between questions and change answers before submitting",
        "Make sure to answer all questions for the best evaluation"
      ]}
      timerMinutes={10}
      fetchQuestionsUrl={`${API_URL}/written/questions`}
      submitAnswersUrl={`${API_URL}/written/submit`}
      maxQuestions={null} // Show all questions (already randomized to 20 by backend)
      showQuestionNavigation={true}
      showTimer={true}
      onComplete={onComplete}
      onNext={onNext}
      containerClass="written-test-wrapper"
      primaryColor="#2F6798"
    />
  );
};

export default WrittenTest;