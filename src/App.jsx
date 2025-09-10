
import { useState, useRef, useEffect } from 'react';
import './App.css';
import RevisionMode from './components/RevisionMode';

function App() {
  const [currentView, setCurrentView] = useState('landing'); // 'landing', 'chat', 'revision'
  const [chatMode, setChatMode] = useState('pal'); // 'pal' or 'book'
  const [showDropdown, setShowDropdown] = useState(false);
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [listening, setListening] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [user, setUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [showConversation, setShowConversation] = useState(false);
  const [sampleMode, setSampleMode] = useState(true); // Pal demo mode
  const [conversationFlow, setConversationFlow] = useState('idle');
  const [transcribedText, setTranscribedText] = useState('');
  const [continuousMode, setContinuousMode] = useState(false);
  const [autoListenTimeout, setAutoListenTimeout] = useState(null);
  const recognitionRef = useRef(null);

  // Load existing documents from MongoDB on app start
  const loadExistingDocuments = async () => {
    try {
      console.log('Loading existing documents from MongoDB...');
      const response = await fetch('http://localhost:8003/documents');
      
      if (response.ok) {
        const data = await response.json();
        console.log('Loaded documents:', data);
        
        if (data.documents && Array.isArray(data.documents)) {
          const formattedFiles = data.documents.map(doc => ({
            name: doc.filename || 'Unknown Document',
            size: doc.file_size || 0,
            type: doc.file_type || 'application/pdf',
            id: doc.id,
            processed: true,
            extractedText: doc.content_preview || ''
          }));
          
          setUploadedFiles(formattedFiles);
          console.log(`✅ Loaded ${formattedFiles.length} existing documents`);
        }
      } else {
        console.warn('Failed to load documents:', response.status);
      }
    } catch (error) {
      console.error('Error loading existing documents:', error);
    }
  };

  // Load documents on app start
  useEffect(() => {
    loadExistingDocuments();
    // Check for existing login session
    const savedUser = localStorage.getItem('highpal_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    // Load conversation history
    const savedHistory = localStorage.getItem('highpal_conversations');
    if (savedHistory) {
      setConversationHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Save conversation history whenever it changes
  useEffect(() => {
    localStorage.setItem('highpal_conversations', JSON.stringify(conversationHistory));
  }, [conversationHistory]);

  // Login functions
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginLoading(true);
    
    try {
      // For now, implement a simple demo login
      // In production, this would call your authentication API
      if (loginForm.email && loginForm.password) {
        const userData = {
          id: Date.now(),
          email: loginForm.email,
          name: loginForm.email.split('@')[0],
          loginTime: new Date().toISOString()
        };
        
        setUser(userData);
        localStorage.setItem('highpal_user', JSON.stringify(userData));
        setShowLoginModal(false);
        setLoginForm({ email: '', password: '' });
        
        alert(`✅ Welcome ${userData.name}! You're now logged in.`);
      } else {
        alert('Please enter both email and password');
      }
    } catch (error) {
      alert('❌ Login failed: ' + error.message);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('highpal_user');
    alert('👋 You have been logged out successfully!');
  };

  const openLoginModal = (e) => {
    e.preventDefault();
    setShowLoginModal(true);
  };

  // Speech-to-text
  const handleMicClick = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser.');
      return;
    }
    if (!listening) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event) => {
        setQuestion(event.results[0][0].transcript);
        setListening(false);
      };
      recognition.onend = () => setListening(false);
      recognitionRef.current = recognition;
      recognition.start();
      setListening(true);
    } else {
      recognitionRef.current && recognitionRef.current.stop();
      setListening(false);
    }
  };

  // Text-to-speech
  const handleSpeakerClick = () => {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-speech not supported in this browser.');
      return;
    }
    const utter = new window.SpeechSynthesisUtterance(response);
    window.speechSynthesis.speak(utter);
  };

  // Pal Voice Assistant System
  const palSampleResponses = {
    greeting: [
      "Hello! I'm Pal, your AI academic assistant. How can I help you today?",
      "Hi there! Pal here, ready to help with your academic questions!",
      "Hey! I'm Pal. What would you like to learn about today?"
    ],
    uploadPrompt: [
      "Great! I see you want to upload a document. I can help you analyze PDFs, Word docs, and text files.",
      "Perfect! Upload your academic materials and I'll help you understand them better.",
      "Excellent! I'm ready to process your documents and answer questions about them."
    ],
    searchHelp: [
      "I can help you search through your uploaded documents. What topic are you interested in?",
      "Let me help you find information in your materials. What are you looking for?",
      "I'm here to help you discover insights from your documents. What's your question?"
    ],
    encouragement: [
      "That's a great question! Let me search through your materials.",
      "Interesting topic! I'll look through your documents for relevant information.",
      "Good thinking! Let me find the best information for you."
    ],
    noDocuments: [
      "I notice you haven't uploaded any documents yet. Would you like to upload some academic materials first?",
      "To give you the best answers, I'd recommend uploading some documents. Shall we start there?",
      "I'm ready to help, but I'll need some documents to work with. Want to upload some files?"
    ]
  };

  const speakAsPal = (text) => {
    if (!('speechSynthesis' in window)) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new window.SpeechSynthesisUtterance(text);
    
    // Pal's voice settings - friendly and clear
    utterance.rate = 0.9;
    utterance.pitch = 1.1;
    utterance.volume = 0.8;
    
    // Try to use a pleasant voice
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.name.includes('Female') || 
      voice.name.includes('Samantha') ||
      voice.name.includes('Karen') ||
      voice.name.includes('Zira')
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }
    
    window.speechSynthesis.speak(utterance);
  };

  const getPalResponse = (userInput, context = {}) => {
    const input = userInput.toLowerCase();
    
    // Greeting patterns
    if (input.includes('hello') || input.includes('hi') || input.includes('hey') || input === '') {
      return palSampleResponses.greeting[Math.floor(Math.random() * palSampleResponses.greeting.length)];
    }
    
    // Upload-related queries
    if (input.includes('upload') || input.includes('file') || input.includes('document')) {
      return palSampleResponses.uploadPrompt[Math.floor(Math.random() * palSampleResponses.uploadPrompt.length)];
    }
    
    // Search-related queries
    if (input.includes('search') || input.includes('find') || input.includes('look for')) {
      if (uploadedFiles.length === 0) {
        return palSampleResponses.noDocuments[Math.floor(Math.random() * palSampleResponses.noDocuments.length)];
      }
      return palSampleResponses.searchHelp[Math.floor(Math.random() * palSampleResponses.searchHelp.length)];
    }
    
    // Default response with encouragement
    if (uploadedFiles.length === 0) {
      return palSampleResponses.noDocuments[Math.floor(Math.random() * palSampleResponses.noDocuments.length)];
    }
    
    return palSampleResponses.encouragement[Math.floor(Math.random() * palSampleResponses.encouragement.length)];
  };

  const startPalConversation = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser.');
      return;
    }
    
    setConversationFlow('active');
    
    // Pal introduction
    const introduction = "Hi! I'm Pal, your AI academic assistant. I'm here to help you with your studies. You can ask me about your uploaded documents, or I can help you get started. What would you like to do?";
    
    // Add to conversation history
    const palEntry = {
      id: Date.now(),
      speaker: 'Pal',
      message: introduction,
      timestamp: new Date().toISOString(),
      type: 'assistant'
    };
    
    setConversationHistory(prev => [...prev, palEntry]);
    speakAsPal(introduction);
    
    // Start listening after introduction
    setTimeout(() => {
      startListeningForPal();
    }, 3000);
  };

  const startListeningForPal = () => {
    if (!('webkitSpeechRecognition' in window)) return;
    
    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;
    
    recognition.onstart = () => {
      setListening(true);
      setTranscribedText('Listening...');
    };
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setTranscribedText(transcript);
      
      // Add user message to conversation
      const userEntry = {
        id: Date.now(),
        speaker: user?.name || 'You',
        message: transcript,
        timestamp: new Date().toISOString(),
        type: 'user'
      };
      
      setConversationHistory(prev => [...prev, userEntry]);
      
      // Generate and speak Pal's response
      const palResponse = getPalResponse(transcript);
      
      const palEntry = {
        id: Date.now() + 1,
        speaker: 'Pal',
        message: palResponse,
        timestamp: new Date().toISOString(),
        type: 'assistant'
      };
      
      setConversationHistory(prev => [...prev, palEntry]);
      
      // Speak the response
      setTimeout(() => {
        speakAsPal(palResponse);
      }, 500);
      
      // Continue listening after response
      setTimeout(() => {
        if (conversationFlow === 'active') {
          startListeningForPal();
        }
      }, palResponse.length * 80 + 2000); // Estimate speech time + pause
    };
    
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setTranscribedText('Error: ' + event.error);
      setListening(false);
    };
    
    recognition.onend = () => {
      setListening(false);
      setTranscribedText('');
    };
    
    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopPalConversation = () => {
    setConversationFlow('idle');
    setListening(false);
    setTranscribedText('');
    
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    // Cancel any ongoing speech
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    
    // Add goodbye message
    const goodbyeMessage = "Goodbye! Feel free to start another conversation anytime. I'm always here to help with your academic needs!";
    
    const palEntry = {
      id: Date.now(),
      speaker: 'Pal',
      message: goodbyeMessage,
      timestamp: new Date().toISOString(),
      type: 'assistant'
    };
    
    setConversationHistory(prev => [...prev, palEntry]);
    speakAsPal(goodbyeMessage);
  };

  // File upload handler
  const handleFileUpload = async (event) => {
    console.log('File upload event triggered');
    console.log('Event target:', event.target);
    console.log('Files:', event.target.files);
    console.log('Files length:', event.target.files ? event.target.files.length : 0);
    
    if (!event.target.files || event.target.files.length === 0) {
      console.log('No files selected or files array is empty');
      return;
    }
    
    const file = event.target.files[0];
    console.log('Selected file:', {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified
    });

    if (!file) {
      console.log('File is null or undefined');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      console.log('FormData created, sending request...');

      // Use the generic upload endpoint for all file types
      let endpoint = 'http://localhost:8003/upload';

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      });

      console.log('Upload response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('Upload successful:', result);
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          size: file.size,
          type: file.type,
          id: result.file_id || result.doc_id || Date.now(),
          processed: true,
          extractedText: result.text || result.extracted_text || ''
        }]);
        alert(`✅ File "${file.name}" uploaded successfully!`);
      } else {
        const error = await response.text();
        console.error('Upload failed:', error);
        alert(`❌ Upload failed: ${error}`);
      }
    } catch (error) {
      console.error('Connection error:', error);
      alert(`❌ Connection error: ${error.message}`);
    } finally {
      setUploading(false);
      // Reset the input value so the same file can be uploaded again
      event.target.value = '';
    }
  };

  // Connect to backend server
  const handleAsk = async () => {
    if (!question.trim()) return;
    
    const questionText = question.trim();
    
    // Create new conversation entry
    const newEntry = {
      id: Date.now(),
      question: questionText,
      answer: '🔄 Processing your question... Please wait',
      timestamp: new Date().toISOString(),
      user: user?.name || 'Anonymous'
    };
    
    // Add to conversation history immediately
    setConversationHistory(prev => [...prev, newEntry]);
    
    setResponse('🔄 Processing your question... Please wait');
    
    try {
      const requestBody = {
        question: questionText,
        uploaded_files: uploadedFiles.map(f => f.id) // Include uploaded files context
      };

      const response = await fetch('http://localhost:8003/ask_question/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        const answerText = data.answer || 'No answer received';
        
        setResponse(answerText);
        
        // Update conversation history with real answer
        setConversationHistory(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { ...entry, answer: answerText }
              : entry
          )
        );
      } else {
        const errorMessage = `Server error: ${response.status}`;
        setResponse(errorMessage);
        
        // Update conversation history with error
        setConversationHistory(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { ...entry, answer: errorMessage }
              : entry
          )
        );
      }
    } catch (error) {
      const errorMessage = `Connection error: ${error.message}`;
      setResponse(errorMessage);
      
      // Update conversation history with error
      setConversationHistory(prev => 
        prev.map(entry => 
          entry.id === newEntry.id 
            ? { ...entry, answer: errorMessage }
            : entry
        )
      );
    } finally {
      // Clear the question input after processing
      setQuestion('');
    }
  };

  // Helper function to format timestamps
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Clear conversation history
  const clearConversationHistory = () => {
    if (window.confirm('Are you sure you want to clear all conversation history?')) {
      setConversationHistory([]);
      setShowConversation(false);
    }
  };

  // Conversation History Component
  const ConversationHistory = ({ history, onClear }) => {
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history]);

    return (
      <div className="conversation-panel">
        <div className="conversation-header">
          <h3>💬 Conversation History</h3>
          <div className="conversation-controls">
            <button onClick={onClear} className="clear-btn" title="Clear History">
              🗑️ Clear
            </button>
            <button 
              onClick={() => setShowConversation(false)} 
              className="close-btn"
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>
        
        <div className="conversation-messages">
          {history.length === 0 ? (
            <div className="no-conversations">
              <p>💭 No conversations yet!</p>
              <p>Start asking questions to see your chat history here.</p>
            </div>
          ) : (
            history.map((entry) => (
              <div key={entry.id} className="conversation-entry">
                <div className="message user-message">
                  <div className="message-content">🤔 {entry.question}</div>
                  <div className="message-time">{formatTime(entry.timestamp)}</div>
                </div>
                <div className="message ai-message">
                  <div className="message-content">
                    🤖 {entry.answer}
                  </div>
                  <div className="message-time">{formatTime(entry.timestamp)}</div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
    );
  };

  // Landing Page Component
  if (currentView === 'landing') {
    return (
      <div className="landing-page">
        {/* HighPal Logo - Top Left */}
        <div className="header">
          <span className="logo">HighPal</span>
        </div>

        {/* Main Content - Two Columns */}
        <div className="main-content">
          <div className="welcome-section">
            <h1 className="main-title">
              Don't just cram. <span className="highlight">HighPal it!</span>
            </h1>
            <p className="subtitle">Find your way, Pal has the map!</p>
          </div>

          <div className="columns-container">
            {/* Learn with Pal Column */}
            <div 
              className="learning-column learn-with-pal-column"
              onClick={() => {
                setChatMode('pal');
                setCurrentView('chat');
              }}
            >
              <div className="column-icon">🎓</div>
              <h2 className="column-title">Learn with Pal</h2>
              <p className="column-description">
                Speak your question, hear your solution!
              </p>
              <button className="cta-button">Start Learning →</button>
            </div>

            {/* Learn from My Book Column */}
            <div 
              className="learning-column my-book-column"
              onClick={() => {
                setChatMode('book');
                setCurrentView('chat');
              }}
            >
              <div className="column-icon">📚</div>
              <h2 className="column-title">Learn from My Book</h2>
              <p className="column-description">
                From textbooks to clarity—Pal helps.
              </p>
              <button className="cta-button">Upload & Learn →</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
  <div style={{ minHeight: '100vh', width: '100vw', background: 'radial-gradient(circle at 10% 10%, #f6f8fc 0%, #fff 100%)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter, Arial, Helvetica, sans-serif', paddingTop: '40px', position: 'relative' }}>
      
      {/* Back arrow - centered below Highpal logo */}
      <button 
        onClick={() => setCurrentView('landing')}
        style={{
          position: 'absolute',
          top: '90px',
          left: '48px',
          transform: 'translateX(50%)',
          background: '#5B3FFF',
          border: 'none',
          color: 'white',
          fontSize: '20px',
          cursor: 'pointer',
          zIndex: 10,
          transition: 'all 0.3s ease',
          padding: '4px',
          borderRadius: '50%',
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(91, 63, 255, 0.3)'
        }}
        onMouseEnter={(e) => {
          e.target.style.background = '#7c4afd';
          e.target.style.transform = 'translateX(50%) scale(1.1)';
          e.target.style.boxShadow = '0 4px 12px rgba(91, 63, 255, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = '#5B3FFF';
          e.target.style.transform = 'translateX(50%) scale(1)';
          e.target.style.boxShadow = '0 2px 8px rgba(91, 63, 255, 0.3)';
        }}
        title="Back to Home"
      >
        ←
      </button>

      {/* Login/User section top right */}
      <div style={{ position: 'absolute', top: 40, right: 48, zIndex: 10 }}>
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ 
              fontSize: '0.9rem', 
              color: '#5B3FFF', 
              fontWeight: 500,
              fontFamily: 'Inter, Arial, Helvetica, sans-serif'
            }}>
              👋 Hi, {user.name}!
            </span>
            <button
              onClick={handleLogout}
              style={{
                fontSize: '0.9rem',
                color: '#7B61FF',
                fontWeight: 500,
                letterSpacing: '0.01em',
                background: 'transparent',
                fontFamily: 'Inter, Arial, Helvetica, sans-serif',
                border: '2px solid #7B61FF',
                borderRadius: '16px',
                padding: '6px 18px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={e => {
                e.target.style.background = '#7B61FF';
                e.target.style.color = '#fff';
              }}
              onMouseLeave={e => {
                e.target.style.background = 'transparent';
                e.target.style.color = '#7B61FF';
              }}
            >
              Logout
            </button>
          </div>
        ) : (
          <button
            onClick={openLoginModal}
            style={{
              fontSize: '1rem',
              color: '#7B61FF',
              fontWeight: 500,
              letterSpacing: '0.01em',
              background: 'transparent',
              fontFamily: 'Inter, Arial, Helvetica, sans-serif',
              border: '2px solid #7B61FF',
              borderRadius: '16px',
              padding: '6px 18px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={e => {
              e.target.style.background = '#7B61FF';
              e.target.style.color = '#fff';
            }}
            onMouseLeave={e => {
              e.target.style.background = 'transparent';
              e.target.style.color = '#7B61FF';
            }}
          >
            Login
          </button>
        )}
      </div>
      {/* Company name top left */}
      <a href="/" style={{ position: 'absolute', top: 32, left: 48, textDecoration: 'none', zIndex: 10 }}>
        <span style={{ fontSize: '2.5rem', color: '#5B3FFF', fontWeight: 700, letterSpacing: '-1px', background: 'transparent', borderRadius: '0', boxShadow: 'none', padding: '0', border: 'none', fontFamily: 'Inter, Arial, Helvetica, sans-serif', display: 'inline-block', lineHeight: 1 }}>
          Highpal
        </span>
      </a>
      {/* Top badge */}
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'center' }}>
  <span style={{ background: '#fff', borderRadius: '24px', boxShadow: '0 2px 12px rgba(80,80,180,0.08)', padding: '10px 32px', fontSize: '1.1rem', color: '#5b5b8a', fontWeight: 500, letterSpacing: '0.01em', border: '3px solid #7B61FF', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24"><path d="M12 2v2m0 16v2m8-10h2M2 12H4m15.07-7.07l-1.41 1.41M6.34 17.66l-1.41 1.41M17.66 17.66l-1.41-1.41M6.34 6.34L4.93 4.93" stroke="#7c7cf0" strokeWidth="2" strokeLinecap="round"/></svg>
          {chatMode === 'pal' ? 'Got doubts? Let\'s untangle them together!' : 'Upload your documents and start learning!'}
        </span>
      </div>
      {/* Main heading */}
      <h1 style={{ fontWeight: 700, fontSize: '4rem', color: '#181c2a', textAlign: 'center', marginBottom: '32px', letterSpacing: '-2px', lineHeight: 1.1 }}>
        {chatMode === 'pal' ? (
          <>Have a question? <span style={{ color: '#7c4afd' }}>Pal is here.</span></>
        ) : (
          <>Let's explore your <span style={{ color: '#7c4afd' }}>study materials!</span></>
        )}
      </h1>
      {/* Mic icon */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '32px' }}>
        <button
          onClick={handleMicClick}
          style={{
            background: '#f6f4ff',
            border: '2px solid #e0d7fa',
            outline: 'none',
            cursor: 'pointer',
            borderRadius: '50%',
            boxShadow: '0 8px 32px rgba(124,74,253,0.10)',
            width: '140px',
            height: '140px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s',
            marginBottom: '16px',
          }}
          title={listening ? 'Listening...' : 'Click to speak'}
        >
          {/* Modern mic SVG icon */}
          <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="36" cy="36" r="34" fill="#ede7fa" stroke="#a084fa" strokeWidth="2" />
            <rect x="28" y="18" width="16" height="28" rx="8" fill="#7c4afd" />
            <rect x="32" y="46" width="8" height="8" rx="4" fill="#7c4afd" />
            <path d="M24 46c0 6.627 5.373 12 12 12s12-5.373 12-12" stroke="#a084fa" strokeWidth="2.5" strokeLinecap="round" />
            <rect x="34" y="54" width="4" height="8" rx="2" fill="#a084fa" />
          </svg>
        </button>
        <span style={{ fontSize: '1.2rem', color: '#4b4b6b', marginTop: '8px', fontWeight: 500 }}>
          {listening ? 'Listening...' : 'Speak when ready!'}
        </span>
      </div>
      
      {/* Pal Voice Assistant Controls */}
      <div style={{ 
        margin: '24px 0', 
        padding: '20px', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
        borderRadius: '20px', 
        boxShadow: '0 8px 32px rgba(124,74,253,0.20)',
        width: '500px',
        maxWidth: '90vw',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px'
      }}>
        <div style={{ color: '#fff', textAlign: 'center' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '1.5rem', fontWeight: 600 }}>
            🤖 Meet Pal - Your AI Assistant
          </h3>
          <p style={{ margin: 0, fontSize: '1rem', opacity: 0.9 }}>
            {sampleMode ? 'Voice conversation demo mode' : 'Connected to full AI system'}
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {conversationFlow === 'idle' ? (
            <button
              onClick={startPalConversation}
              style={{
                background: '#fff',
                color: '#667eea',
                border: 'none',
                borderRadius: '25px',
                padding: '12px 24px',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}
              onMouseEnter={e => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={e => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
              }}
            >
              🎤 Start Conversation with Pal
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
              <button
                onClick={stopPalConversation}
                style={{
                  background: '#ff4757',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '25px',
                  padding: '12px 24px',
                  fontSize: '1rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}
                onMouseEnter={e => {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.15)';
                }}
                onMouseLeave={e => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                }}
              >
                🛑 Stop Conversation
              </button>
              
              <div style={{
                background: 'rgba(255,255,255,0.2)',
                borderRadius: '15px',
                padding: '8px 16px',
                color: '#fff',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                {listening ? (
                  <>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      background: '#00ff00',
                      borderRadius: '50%',
                      animation: 'pulse 1s infinite'
                    }}></div>
                    Listening...
                  </>
                ) : (
                  <>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      background: '#ffa500',
                      borderRadius: '50%'
                    }}></div>
                    {transcribedText || 'Processing...'}
                  </>
                )}
              </div>
            </div>
          )}
        </div>
        
        <div style={{
          fontSize: '0.85rem',
          color: 'rgba(255,255,255,0.8)',
          textAlign: 'center',
          fontStyle: 'italic'
        }}>
          {conversationFlow === 'active' ? 
            "Pal is listening and ready to help with your academic questions!" :
            "Start a natural voice conversation with Pal about your studies"
          }
        </div>
      </div>

      {/* Input bar */}
      <form onSubmit={e => { e.preventDefault(); handleAsk(); }} style={{ width: '600px', maxWidth: '90vw', margin: '0 auto', display: 'flex', alignItems: 'center', background: '#fff', borderRadius: '32px', boxShadow: '0 8px 32px rgba(124,74,253,0.10)', padding: '8px 16px', border: '1px solid #f0f0f0' }}>
        <div style={{ display: 'flex', flex: 1, border: '3px solid #fff', borderRadius: '32px', background: '#fff', boxShadow: '0 8px 32px rgba(124,74,253,0.10)', padding: '4px 8px', position: 'relative' }}>
          <label htmlFor="file-upload" style={{ display: 'flex', alignItems: 'center', marginRight: '10px', cursor: 'pointer' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: uploading ? '#ccc' : '#f6f4ff',
                border: '2px solid #e0d7fa',
                color: uploading ? '#666' : '#7B61FF',
                fontSize: '1.6rem',
                fontWeight: 700,
                boxShadow: '0 2px 8px rgba(123,97,255,0.10)',
                transition: 'background 0.2s',
                position: 'relative',
              }}
              onClick={e => { 
                e.preventDefault(); 
                if (!uploading) {
                  setShowDropdown(v => !v); 
                }
              }}
            >
              {uploading ? '⏳' : '+'}
              {showDropdown && !uploading && (
                <div style={{
                  position: 'absolute',
                  top: '40px',
                  left: 0,
                  minWidth: '120px',
                  background: '#fff',
                  border: '1.5px solid #7B61FF',
                  borderRadius: '12px',
                  boxShadow: '0 2px 12px rgba(123,97,255,0.10)',
                  zIndex: 100,
                  padding: '8px 0',
                  textAlign: 'left',
                }}>
                  <div
                    style={{
                      padding: '8px 18px',
                      color: '#7B61FF',
                      fontWeight: 500,
                      fontSize: '1rem',
                      cursor: 'pointer',
                      borderRadius: '8px',
                      transition: 'background 0.2s',
                    }}
                    onMouseEnter={e => e.target.style.background = '#f8f4ff'}
                    onMouseLeave={e => e.target.style.background = 'transparent'}
                    onClick={e => {
                      e.stopPropagation();
                      setShowDropdown(false);
                      const fileInput = document.getElementById('file-upload');
                      fileInput.accept = '.pdf';
                      fileInput.click();
                    }}
                  >
                    📄 PDF
                  </div>
                  <div
                    style={{
                      padding: '8px 18px',
                      color: '#7B61FF',
                      fontWeight: 500,
                      fontSize: '1rem',
                      cursor: 'pointer',
                      borderRadius: '8px',
                      transition: 'background 0.2s',
                    }}
                    onMouseEnter={e => e.target.style.background = '#f8f4ff'}
                    onMouseLeave={e => e.target.style.background = 'transparent'}
                    onClick={e => {
                      e.stopPropagation();
                      setShowDropdown(false);
                      const fileInput = document.getElementById('file-upload');
                      fileInput.accept = '.png,.jpg,.jpeg,.gif,.bmp,.webp';
                      fileInput.click();
                    }}
                  >
                    🖼️ Image
                  </div>
                </div>
              )}
            </span>
            <input 
              id="file-upload" 
              type="file" 
              accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif,.bmp,.webp" 
              style={{ display: 'none' }} 
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
          
          {/* Revision Mode Button */}
          {chatMode === 'book' && uploadedFiles.length > 0 && (
            <button
              onClick={() => setCurrentView('revision')}
              style={{
                background: 'linear-gradient(135deg, #ff6b6b, #ff5722)',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                padding: '12px 16px',
                fontSize: '0.9rem',
                fontWeight: '600',
                cursor: 'pointer',
                marginLeft: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 2px 8px rgba(255, 107, 107, 0.3)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={e => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 4px 12px rgba(255, 107, 107, 0.4)';
              }}
              onMouseLeave={e => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 2px 8px rgba(255, 107, 107, 0.3)';
              }}
              title="Start revision quiz based on your uploaded documents"
            >
              📝 Quiz Me
            </button>
          )}
          
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Quick Question? Quick Answer!"
            style={{
              flex: 1,
              fontSize: '1rem',
              padding: '18px 20px',
              border: 'none',
              borderRadius: '32px',
              outline: 'none',
              fontFamily: 'Inter, Arial, Helvetica, sans-serif',
              color: '#222',
              background: 'transparent',
              fontWeight: 400,
            }}
          />
          <button
            type="submit"
            style={{
              fontSize: '1.2rem',
              fontWeight: 600,
              padding: '0 32px',
              background: 'linear-gradient(90deg, #a084fa 0%, #7c4afd 100%)',
              color: '#fff',
              border: 'none',
              borderRadius: '24px',
              cursor: 'pointer',
              fontFamily: 'Inter, Arial, Helvetica, sans-serif',
              boxShadow: '0 2px 8px rgba(123,97,255,0.20)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginLeft: '12px',
              transition: 'background 0.2s',
            }}
          >
            <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><path d="M2 12l20-8-8 20-2.5-7.5L2 12z" stroke="#fff" strokeWidth="2" strokeLinejoin="round"/></svg>
            Get Answer
          </button>
        </div>
      </form>
      
      {/* Response area */}
      {response && (
        <div style={{
          width: '600px',
          maxWidth: '90vw',
          margin: '24px auto 0',
          padding: '24px',
          background: '#fff',
          borderRadius: '16px',
          boxShadow: '0 8px 32px rgba(124,74,253,0.10)',
          border: '1px solid #f0f0f0'
        }}>
          <h3 style={{ 
            color: '#7c4afd', 
            marginBottom: '16px', 
            fontSize: '1.2rem',
            fontWeight: 600 
          }}>
            Answer:
          </h3>
          <p style={{ 
            color: '#333', 
            lineHeight: 1.6,
            fontSize: '1rem',
            margin: 0 
          }}>
            {response}
          </p>
          {response && !response.startsWith('🔄') && !response.startsWith('Connection') && !response.startsWith('Server') && (
            <button
              onClick={handleSpeakerClick}
              style={{
                marginTop: '16px',
                padding: '8px 16px',
                background: '#f6f4ff',
                border: '2px solid #e0d7fa',
                borderRadius: '20px',
                color: '#7c4afd',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
              title="Listen to response"
            >
              🔊 Listen
            </button>
          )}
        </div>
      )}
      
      {/* Conversation Toggle Button */}
      <button 
        onClick={() => setShowConversation(!showConversation)}
        className={`conversation-btn ${conversationHistory.length > 0 ? 'has-history' : ''}`}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          background: conversationHistory.length > 0 
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
            : '#6c757d',
          color: 'white',
          border: 'none',
          borderRadius: '25px',
          padding: '12px 20px',
          fontSize: '0.9rem',
          fontWeight: '500',
          cursor: 'pointer',
          boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
          zIndex: 999,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          transition: 'all 0.3s ease',
          animation: conversationHistory.length > 0 ? 'pulse 2s infinite' : 'none'
        }}
        title="View conversation history"
      >
        💬 Chat History ({conversationHistory.length})
      </button>

      {/* Conversation Panel */}
      {showConversation && (
        <ConversationHistory 
          history={conversationHistory}
          onClear={clearConversationHistory}
        />
      )}

      {/* Login Modal */}
      {showLoginModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: '#fff',
            borderRadius: '20px',
            padding: '40px',
            width: '400px',
            maxWidth: '90vw',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
            position: 'relative'
          }}>
            {/* Close button */}
            <button
              onClick={() => setShowLoginModal(false)}
              style={{
                position: 'absolute',
                top: '15px',
                right: '20px',
                background: 'transparent',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>

            {/* Modal header */}
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <h2 style={{
                color: '#5B3FFF',
                fontSize: '2rem',
                fontWeight: 700,
                margin: '0 0 10px 0',
                fontFamily: 'Inter, Arial, Helvetica, sans-serif'
              }}>
                Welcome to HighPal
              </h2>
              <p style={{
                color: '#666',
                fontSize: '1rem',
                margin: 0,
                fontFamily: 'Inter, Arial, Helvetica, sans-serif'
              }}>
                Sign in to save your documents and chat history
              </p>
            </div>

            {/* Login form */}
            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  color: '#333',
                  fontSize: '0.9rem',
                  fontWeight: 500,
                  marginBottom: '8px',
                  fontFamily: 'Inter, Arial, Helvetica, sans-serif'
                }}>
                  Email Address
                </label>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={e => setLoginForm({...loginForm, email: e.target.value})}
                  placeholder="Enter your email"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '2px solid #e0d7fa',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    fontFamily: 'Inter, Arial, Helvetica, sans-serif',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                    boxSizing: 'border-box'
                  }}
                  onFocus={e => e.target.style.borderColor = '#7B61FF'}
                  onBlur={e => e.target.style.borderColor = '#e0d7fa'}
                />
              </div>

              <div style={{ marginBottom: '30px' }}>
                <label style={{
                  display: 'block',
                  color: '#333',
                  fontSize: '0.9rem',
                  fontWeight: 500,
                  marginBottom: '8px',
                  fontFamily: 'Inter, Arial, Helvetica, sans-serif'
                }}>
                  Password
                </label>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={e => setLoginForm({...loginForm, password: e.target.value})}
                  placeholder="Enter your password"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '2px solid #e0d7fa',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    fontFamily: 'Inter, Arial, Helvetica, sans-serif',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                    boxSizing: 'border-box'
                  }}
                  onFocus={e => e.target.style.borderColor = '#7B61FF'}
                  onBlur={e => e.target.style.borderColor = '#e0d7fa'}
                />
              </div>

              <button
                type="submit"
                disabled={loginLoading}
                style={{
                  width: '100%',
                  padding: '14px 20px',
                  background: loginLoading ? '#ccc' : 'linear-gradient(90deg, #a084fa 0%, #7c4afd 100%)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '12px',
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  cursor: loginLoading ? 'not-allowed' : 'pointer',
                  fontFamily: 'Inter, Arial, Helvetica, sans-serif',
                  transition: 'all 0.2s'
                }}
              >
                {loginLoading ? '🔄 Signing in...' : '🚀 Sign In'}
              </button>
            </form>

            {/* Demo notice */}
            <div style={{
              marginTop: '20px',
              padding: '12px',
              background: '#f8f9ff',
              borderRadius: '8px',
              border: '1px solid #e0d7fa'
            }}>
              <p style={{
                fontSize: '0.85rem',
                color: '#666',
                margin: 0,
                textAlign: 'center',
                fontFamily: 'Inter, Arial, Helvetica, sans-serif'
              }}>
                💡 <strong>Demo Mode:</strong> Use any email and password to sign in
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
