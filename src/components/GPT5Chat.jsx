import React, { useState, useEffect, useRef } from 'react';
import './GPT5Chat.css';

const GPT5Chat = ({ user, uploadedFiles = [] }) => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [modelInfo, setModelInfo] = useState(null);
  const chatEndRef = useRef(null);

  // Load conversation history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('highpal_gpt4o_conversations');
    if (savedHistory) {
      setConversationHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Save conversation history whenever it changes
  useEffect(() => {
    localStorage.setItem('highpal_gpt4o_conversations', JSON.stringify(conversationHistory));
  }, [conversationHistory]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationHistory, response]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) return;
    
    setLoading(true);
    setResponse('🤖 HighPal is thinking with GPT-4o... Please wait');
    
    // Create new conversation entry
    const newEntry = {
      id: Date.now(),
      question: question,
      answer: '🤖 Processing with GPT-4o...',
      timestamp: new Date().toISOString(),
      user: user?.name || 'Anonymous',
      model: 'gpt-4o'
    };
    
    // Add to conversation history immediately
    setConversationHistory(prev => [...prev, newEntry]);
    
    try {
      const requestBody = {
        question: question,
        uploaded_files: uploadedFiles.map(f => f.id)
      };

      const response = await fetch('http://localhost:8003/gpt4o-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        const answerText = data.answer || 'No answer received from GPT-4o';
        
        setResponse(answerText);
        setModelInfo({
          model: data.model,
          tokens: data.tokens_used,
          timestamp: data.timestamp
        });
        
        // Update conversation history with real answer
        setConversationHistory(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { 
                  ...entry, 
                  answer: answerText,
                  tokens: data.tokens_used,
                  model: data.model
                }
              : entry
          )
        );
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || `GPT-4o service error: ${response.status}`;
        setResponse(`❌ ${errorMessage}`);
        
        // Update conversation history with error
        setConversationHistory(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { ...entry, answer: `❌ ${errorMessage}` }
              : entry
          )
        );
      }
    } catch (error) {
      const errorMessage = `Connection error: ${error.message}`;
      setResponse(`❌ ${errorMessage}`);
      
      // Update conversation history with error
      setConversationHistory(prev => 
        prev.map(entry => 
          entry.id === newEntry.id 
            ? { ...entry, answer: `❌ ${errorMessage}` }
            : entry
        )
      );
    } finally {
      setLoading(false);
      setQuestion('');
    }
  };

  const clearHistory = () => {
    setConversationHistory([]);
    setResponse('');
    localStorage.removeItem('highpal_gpt4o_conversations');
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="gpt5-chat">
      <div className="chat-header">
        <h2>🚀 HighPal GPT-4o Enhanced Chat</h2>
        <div className="chat-controls">
          <button 
            onClick={() => setShowHistory(!showHistory)}
            className="history-toggle"
          >
            {showHistory ? 'Hide History' : 'Show History'} ({conversationHistory.length})
          </button>
          {conversationHistory.length > 0 && (
            <button onClick={clearHistory} className="clear-history">
              Clear History
            </button>
          )}
        </div>
      </div>

      {/* Conversation History */}
      {showHistory && (
        <div className="conversation-history">
          <h3>📚 Conversation History</h3>
          {conversationHistory.length === 0 ? (
            <p className="no-history">No conversations yet. Start chatting with HighPal!</p>
          ) : (
            <div className="history-list">
              {conversationHistory.map((conv) => (
                <div key={conv.id} className="conversation-item">
                  <div className="conversation-meta">
                    <span className="user">👤 {conv.user}</span>
                    <span className="time">{formatTime(conv.timestamp)}</span>
                    <span className="model">🤖 {conv.model}</span>
                    {conv.tokens && <span className="tokens">⚡ {conv.tokens} tokens</span>}
                  </div>
                  <div className="question">
                    <strong>Q:</strong> {conv.question}
                  </div>
                  <div className="answer">
                    <strong>A:</strong> {conv.answer}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>
      )}

      {/* Current Response */}
      {response && (
        <div className="current-response">
          <h3>🎓 HighPal's Response</h3>
          <div className="response-content">
            {response}
          </div>
          {modelInfo && (
            <div className="model-info">
              <span>Powered by {modelInfo.model}</span>
              {modelInfo.tokens && <span> • {modelInfo.tokens} tokens used</span>}
              <span> • {formatTime(modelInfo.timestamp)}</span>
            </div>
          )}
        </div>
      )}

      {/* Chat Input */}
      <form onSubmit={handleSubmit} className="chat-form">
        <div className="input-group">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask HighPal anything about your studies, exams, or academic topics..."
            className="question-input"
            rows={3}
            disabled={loading}
          />
          <button 
            type="submit" 
            disabled={loading || !question.trim()}
            className="submit-button"
          >
            {loading ? '🤖 Thinking...' : '🚀 Ask GPT-4o'}
          </button>
        </div>
        
        {uploadedFiles.length > 0 && (
          <div className="context-info">
            📄 Using context from {uploadedFiles.length} uploaded document(s)
          </div>
        )}
      </form>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h4>💡 Quick Study Help</h4>
        <div className="action-buttons">
          <button 
            onClick={() => setQuestion("Explain this concept in simple terms")}
            className="quick-action"
          >
            📖 Explain Concept
          </button>
          <button 
            onClick={() => setQuestion("Give me practice problems on this topic")}
            className="quick-action"
          >
            📝 Practice Problems
          </button>
          <button 
            onClick={() => setQuestion("What are the key formulas I should remember?")}
            className="quick-action"
          >
            📐 Key Formulas
          </button>
          <button 
            onClick={() => setQuestion("How can I study this topic efficiently?")}
            className="quick-action"
          >
            ⏰ Study Tips
          </button>
        </div>
      </div>

      {/* Features Info */}
      <div className="features-info">
        <h4>🌟 GPT-4o Enhanced Features</h4>
        <ul>
          <li>🧠 Advanced reasoning for complex academic problems</li>
          <li>🎯 Personalized explanations based on your learning style</li>
          <li>💪 Confidence building and motivational responses</li>
          <li>📊 Exam strategies and study planning assistance</li>
          <li>🔄 Adaptive difficulty based on your understanding</li>
        </ul>
      </div>
    </div>
  );
};

export default GPT5Chat;
