import React, { useState, useEffect } from 'react';
import './RevisionMode.css';

const RevisionMode = ({ uploadedFiles, onBackToChat }) => {
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [revisionSession, setRevisionSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [startTime, setStartTime] = useState(null);

  const startRevisionSession = async () => {
    if (!selectedDocument) {
      alert('Please select a document first');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8003/book/revision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: selectedDocument.id,
          difficulty: 'adaptive',
          question_count: 10
        })
      });

      if (response.ok) {
        const sessionData = await response.json();
        setRevisionSession(sessionData);
        setCurrentQuestionIndex(0);
        setUserAnswers({});
        setStartTime(Date.now());
        setShowResults(false);
        setFeedback(null);
      } else {
        alert('Failed to start revision session');
      }
    } catch (error) {
      console.error('Error starting revision:', error);
      alert('Error starting revision session');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerChange = (questionId, answer) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < revisionSession.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      submitRevision();
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const submitRevision = async () => {
    setIsLoading(true);
    try {
      const answers = revisionSession.questions.map(q => ({
        question_id: q.id,
        user_answer: userAnswers[q.id] || '',
        time_taken: Math.floor((Date.now() - startTime) / 1000)
      }));

      const response = await fetch('http://localhost:8003/book/revision/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          revision_session_id: revisionSession.revision_session_id,
          answers: answers
        })
      });

      if (response.ok) {
        const feedbackData = await response.json();
        setFeedback(feedbackData);
        setShowResults(true);
      } else {
        alert('Failed to submit revision');
      }
    } catch (error) {
      console.error('Error submitting revision:', error);
      alert('Error submitting revision');
    } finally {
      setIsLoading(false);
    }
  };

  const currentQuestion = revisionSession?.questions[currentQuestionIndex];
  const progress = revisionSession ? ((currentQuestionIndex + 1) / revisionSession.questions.length) * 100 : 0;

  if (showResults && feedback) {
    return (
      <div className="revision-container">
        <div className="revision-header">
          <button onClick={onBackToChat} className="back-button">
            ← Back to Chat
          </button>
          <h2>📊 Revision Results</h2>
        </div>

        <div className="results-container">
          <div className="score-summary">
            <h3>Your Score: {feedback.score} ({feedback.percentage}%)</h3>
            <div className={`score-badge ${feedback.percentage >= 80 ? 'excellent' : feedback.percentage >= 60 ? 'good' : 'needs-improvement'}`}>
              {feedback.percentage >= 80 ? '🎉 Excellent!' : feedback.percentage >= 60 ? '👍 Good Job!' : '📚 Keep Studying!'}
            </div>
          </div>

          <div className="feedback-section">
            <h4>Overall Feedback</h4>
            <p>{feedback.overall_feedback}</p>
          </div>

          <div className="strengths-section">
            <h4>✅ Your Strengths</h4>
            <ul>
              {feedback.strengths.map((strength, index) => (
                <li key={index}>{strength}</li>
              ))}
            </ul>
          </div>

          <div className="improvement-section">
            <h4>🎯 Areas for Improvement</h4>
            <ul>
              {feedback.areas_for_improvement.map((area, index) => (
                <li key={index}>{area}</li>
              ))}
            </ul>
          </div>

          <div className="next-steps-section">
            <h4>📋 Next Steps</h4>
            <ul>
              {feedback.next_steps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ul>
          </div>

          <div className="action-buttons">
            <button onClick={() => setShowResults(false)} className="try-again-button">
              🔄 Try Another Revision
            </button>
            <button onClick={onBackToChat} className="back-to-chat-button">
              💬 Back to Chat
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (revisionSession && !showResults) {
    return (
      <div className="revision-container">
        <div className="revision-header">
          <button onClick={() => setRevisionSession(null)} className="back-button">
            ← Back to Setup
          </button>
          <h2>📝 Revision Session</h2>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <span className="progress-text">
            Question {currentQuestionIndex + 1} of {revisionSession.questions.length}
          </span>
        </div>

        <div className="question-container">
          <div className="question-header">
            <span className="question-type">{currentQuestion?.type?.replace('_', ' ').toUpperCase()}</span>
            <span className="difficulty">Difficulty: {currentQuestion?.difficulty}</span>
          </div>

          <h3 className="question-text">{currentQuestion?.question}</h3>

          <div className="answer-section">
            {currentQuestion?.type === 'multiple_choice' && (
              <div className="multiple-choice">
                {currentQuestion.options?.map((option, index) => (
                  <label key={index} className="option-label">
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      value={option}
                      checked={userAnswers[currentQuestion.id] === option}
                      onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                    />
                    <span className="option-text">{option}</span>
                  </label>
                ))}
              </div>
            )}

            {currentQuestion?.type === 'true_false' && (
              <div className="true-false">
                <label className="option-label">
                  <input
                    type="radio"
                    name={`question-${currentQuestion.id}`}
                    value="true"
                    checked={userAnswers[currentQuestion.id] === 'true'}
                    onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                  />
                  <span className="option-text">True</span>
                </label>
                <label className="option-label">
                  <input
                    type="radio"
                    name={`question-${currentQuestion.id}`}
                    value="false"
                    checked={userAnswers[currentQuestion.id] === 'false'}
                    onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                  />
                  <span className="option-text">False</span>
                </label>
              </div>
            )}

            {currentQuestion?.type === 'open_ended' && (
              <textarea
                className="open-ended-answer"
                placeholder="Type your answer here..."
                value={userAnswers[currentQuestion.id] || ''}
                onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                rows={4}
              />
            )}
          </div>

          {currentQuestion?.explanation && (
            <div className="question-explanation">
              <strong>Hint:</strong> {currentQuestion.explanation}
            </div>
          )}

          <div className="navigation-buttons">
            <button 
              onClick={previousQuestion} 
              disabled={currentQuestionIndex === 0}
              className="nav-button prev-button"
            >
              ← Previous
            </button>
            
            <button 
              onClick={nextQuestion}
              disabled={!userAnswers[currentQuestion?.id]}
              className="nav-button next-button"
            >
              {currentQuestionIndex === revisionSession.questions.length - 1 ? 'Submit' : 'Next →'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="revision-container">
      <div className="revision-header">
        <button onClick={onBackToChat} className="back-button">
          ← Back to Chat
        </button>
        <h2>📚 Revision Mode</h2>
      </div>

      <div className="revision-setup">
        <div className="setup-section">
          <h3>Select Document for Revision</h3>
          <p>Choose one of your uploaded documents to create a quiz and test your understanding.</p>
          
          {uploadedFiles.length === 0 ? (
            <div className="no-documents">
              <p>No documents uploaded yet. Please upload a document first to use revision mode.</p>
            </div>
          ) : (
            <div className="document-list">
              {uploadedFiles.map((file, index) => (
                <div 
                  key={index} 
                  className={`document-item ${selectedDocument?.id === file.id ? 'selected' : ''}`}
                  onClick={() => setSelectedDocument(file)}
                >
                  <div className="document-info">
                    <span className="document-name">📄 {file.name}</span>
                    <span className="document-size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  {selectedDocument?.id === file.id && (
                    <span className="selected-indicator">✅</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedDocument && (
          <div className="revision-options">
            <h4>Revision Settings</h4>
            <div className="option-group">
              <label>Difficulty Level:</label>
              <select defaultValue="adaptive">
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
                <option value="adaptive">Adaptive</option>
              </select>
            </div>
            <div className="option-group">
              <label>Number of Questions:</label>
              <select defaultValue="10">
                <option value="5">5 Questions</option>
                <option value="10">10 Questions</option>
                <option value="15">15 Questions</option>
                <option value="20">20 Questions</option>
              </select>
            </div>
          </div>
        )}

        <div className="start-button-container">
          <button 
            onClick={startRevisionSession}
            disabled={!selectedDocument || isLoading}
            className="start-revision-button"
          >
            {isLoading ? 'Creating Quiz...' : '🚀 Start Revision Quiz'}
          </button>
        </div>

        <div className="revision-info">
          <h4>How Revision Mode Works:</h4>
          <ul>
            <li>🎯 AI generates questions based on your uploaded document</li>
            <li>📝 Mix of multiple choice, true/false, and open-ended questions</li>
            <li>⏱️ Take your time - no rush, focus on understanding</li>
            <li>📊 Get detailed feedback and suggestions for improvement</li>
            <li>🔄 Retake anytime to track your progress</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RevisionMode;
