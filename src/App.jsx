import { useState, useRef, useEffect } from 'react';
import './App.css';
import RevisionMode from './components/RevisionMode';

function App() {
  const [currentView, setCurrentView] = useState('landing'); // 'landing', 'chat', 'revision'
  const [chatMode, setChatMode] = useState('pal'); // 'pal' or 'book'
  const [showDropdown, setShowDropdown] = useState(false);
  const [questionPal, setQuestionPal] = useState('');
  const [questionBook, setQuestionBook] = useState('');
  const [response, setResponse] = useState('');
  const [listening, setListening] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [user, setUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [conversationHistoryPal, setConversationHistoryPal] = useState([]);
  const [conversationHistoryBook, setConversationHistoryBook] = useState([]);
  const [showConversation, setShowConversation] = useState(false);
  const [sampleMode, setSampleMode] = useState(true);
  const [conversationFlow, setConversationFlow] = useState('idle');
  const [transcribedText, setTranscribedText] = useState('');
  const [continuousMode, setContinuousMode] = useState(false);
  const [autoListenTimeout, setAutoListenTimeout] = useState(null);
  const recognitionRef = useRef(null);

  // Load existing documents from MongoDB on app start
  const loadExistingDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8003/list_documents/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.documents && Array.isArray(data.documents)) {
          const formattedFiles = data.documents.map(doc => ({
            id: doc.document_id || doc.id,
            name: doc.filename || doc.name || 'Unknown Document',
            url: doc.url || '#',
            type: doc.type || 'pdf',
            status: 'uploaded'
          }));
          setUploadedFiles(formattedFiles);
        }
      }
    } catch (error) {
      console.error('Error loading existing documents:', error);
    }
  };

  useEffect(() => {
    loadExistingDocuments();
  }, []);

  // Mic functionality
  const handleMicClick = () => {
    if (!listening) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (chatMode === 'pal') {
          setQuestionPal(transcript);
        } else {
          setQuestionBook(transcript);
        }
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

  // Connect to backend server for Pal mode
  const handleAskPal = async () => {
    if (!questionPal.trim()) return;
    
    const questionText = questionPal.trim();
    const isFirstMessage = conversationHistoryPal.length === 0;
    
    const newEntry = {
      id: Date.now(),
      question: questionText,
      answer: '🔄 Processing your question... Please wait',
      timestamp: new Date().toISOString(),
      user: user?.name || 'Anonymous'
    };
    
    setConversationHistoryPal(prev => [...prev, newEntry]);
    
    try {
      const requestBody = {
        question: questionText,
        uploaded_files: [],
        is_first_message: isFirstMessage
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
        
        setConversationHistoryPal(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { ...entry, answer: answerText }
              : entry
          )
        );
      } else {
        const errorMessage = 'Sorry, I encountered an error. Please try again.';
        setConversationHistoryPal(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { ...entry, answer: errorMessage }
              : entry
          )
        );
      }
    } catch (error) {
      const errorMessage = 'Sorry, I\'m having trouble connecting. Please check your internet connection and try again.';
      setConversationHistoryPal(prev => 
        prev.map(entry => 
          entry.id === newEntry.id 
            ? { ...entry, answer: errorMessage }
            : entry
        )
      );
    } finally {
      setQuestionPal('');
    }
  };

  // Connect to backend server for Book mode
  const handleAskBook = async () => {
    if (!questionBook.trim()) return;
    
    const questionText = questionBook.trim();
    const isFirstMessage = conversationHistoryBook.length === 0;
    
    const newEntry = {
      id: Date.now(),
      question: questionText,
      answer: '🔄 Processing your question... Please wait',
      timestamp: new Date().toISOString(),
      user: user?.name || 'Anonymous'
    };
    
    setConversationHistoryBook(prev => [...prev, newEntry]);
    
    try {
      const requestBody = {
        question: questionText,
        uploaded_files: uploadedFiles.map(f => f.id),
        is_first_message: isFirstMessage
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
        
        setConversationHistoryBook(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { ...entry, answer: answerText }
              : entry
          )
        );
      } else {
        const errorMessage = 'Sorry, I encountered an error. Please try again.';
        setConversationHistoryBook(prev => 
          prev.map(entry => 
            entry.id === newEntry.id 
              ? { ...entry, answer: errorMessage }
              : entry
          )
        );
      }
    } catch (error) {
      const errorMessage = 'Sorry, I\'m having trouble connecting. Please check your internet connection and try again.';
      setConversationHistoryBook(prev => 
        prev.map(entry => 
          entry.id === newEntry.id 
            ? { ...entry, answer: errorMessage }
            : entry
        )
      );
    } finally {
      setQuestionBook('');
    }
  };

  // File upload handler
  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setUploading(true);

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('http://localhost:8003/upload_pdf/', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          const newFile = {
            id: data.document_id || Date.now(),
            name: file.name,
            url: data.url || URL.createObjectURL(file),
            type: file.type.includes('pdf') ? 'pdf' : 'image',
            status: 'uploaded'
          };
          setUploadedFiles(prev => [...prev, newFile]);
        }
      } catch (error) {
        console.error('Upload error:', error);
      }
    }

    setUploading(false);
    event.target.value = '';
  };

  // Revision Mode Component
  if (currentView === 'revision') {
    return <RevisionMode onBack={() => setCurrentView('chat')} uploadedFiles={uploadedFiles} />;
  }

  // Landing Page Component
  if (currentView === 'landing') {
    return (
      <div className="landing-page">
        <div className="header">
          <span className="logo">HighPal</span>
        </div>

        <div className="main-content">
          <div className="welcome-section">
            <h1 className="main-title">
              Don't just cram. <span className="highlight">HighPal it!</span>
            </h1>
            <p className="subtitle">Find your way, Pal has the map!</p>
          </div>

          <div className="columns-container">
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

  // Chat Interface - now uses separate histories and shows upload for book mode first
  return (
    <div style={{ minHeight: '100vh', width: '100vw', background: 'radial-gradient(circle at 10% 10%, #f6f8fc 0%, #fff 100%)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter, Arial, Helvetica, sans-serif', paddingTop: '40px', position: 'relative' }}>
      
      {/* Back arrow */}
      <button 
        onClick={() => setCurrentView('landing')}
        style={{
          position: 'absolute',
          top: '90px',
          left: '48px',
          background: '#5B3FFF',
          border: 'none',
          color: 'white',
          fontSize: '20px',
          cursor: 'pointer',
          zIndex: 10,
          padding: '4px',
          borderRadius: '50%',
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(91, 63, 255, 0.3)'
        }}
      >
        ←
      </button>

      {/* HighPal Logo */}
      <div style={{ position: 'absolute', top: '32px', left: '50%', transform: 'translateX(-50%)', zIndex: 10 }}>
        <span style={{ fontSize: '2rem', fontWeight: 800, color: '#181c2a', fontFamily: 'Inter, Arial, Helvetica, sans-serif' }}>
          HighPal
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

      {/* Content based on mode and upload status */}
      {chatMode === 'book' && uploadedFiles.length === 0 ? (
        /* Upload Section for Book Mode */
        <div style={{ textAlign: 'center', maxWidth: '600px', padding: '40px' }}>
          <div style={{ fontSize: '4rem', marginBottom: '24px' }}>📚</div>
          <h2 style={{ fontSize: '2rem', color: '#181c2a', marginBottom: '16px' }}>Upload Your Study Materials</h2>
          <p style={{ fontSize: '1.2rem', color: '#666', marginBottom: '32px' }}>
            Upload PDFs, documents, or images and I'll help you understand them better!
          </p>
          
          <label htmlFor="file-upload" style={{
            display: 'inline-block',
            background: 'linear-gradient(135deg, #7c4afd, #a084fa)',
            color: 'white',
            padding: '16px 32px',
            borderRadius: '16px',
            cursor: 'pointer',
            fontSize: '1.1rem',
            fontWeight: '600',
            border: 'none',
            boxShadow: '0 4px 16px rgba(124, 74, 253, 0.3)',
            transition: 'all 0.3s ease'
          }}>
            📄 Choose Files to Upload
          </label>
          <input 
            id="file-upload"
            type="file" 
            accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif,.bmp,.webp" 
            style={{ display: 'none' }} 
            onChange={handleFileUpload}
            disabled={uploading}
            multiple
          />
          
          {uploading && (
            <div style={{ marginTop: '24px', color: '#7c4afd' }}>
              <div>🔄 Uploading your files...</div>
            </div>
          )}
        </div>
      ) : (
        /* Chat Interface */
        <div style={{ width: '100%', maxWidth: '800px' }}>
          {/* Show uploaded files for book mode */}
          {chatMode === 'book' && uploadedFiles.length > 0 && (
            <div style={{ marginBottom: '24px', padding: '16px', background: '#f8f9fa', borderRadius: '12px' }}>
              <h3 style={{ color: '#7c4afd', marginBottom: '12px' }}>📚 Your Documents:</h3>
              {uploadedFiles.map(file => (
                <div key={file.id} style={{ padding: '8px', margin: '4px 0', background: 'white', borderRadius: '8px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{file.name}</span>
                  <span style={{ color: 'green' }}>✅ Ready</span>
                </div>
              ))}
            </div>
          )}

          {/* Conversation History */}
          <div style={{ marginBottom: '24px', maxHeight: '400px', overflowY: 'auto' }}>
            {(chatMode === 'pal' ? conversationHistoryPal : conversationHistoryBook).length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                {chatMode === 'pal' ? (
                  <div>
                    <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🎓</div>
                    <h3>Hi! I'm Pal, your study buddy</h3>
                    <p>Ask me anything about your studies!</p>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📖</div>
                    <h3>Ready to explore your documents!</h3>
                    <p>Ask questions about your uploaded materials below.</p>
                  </div>
                )}
              </div>
            ) : (
              <div>
                {(chatMode === 'pal' ? conversationHistoryPal : conversationHistoryBook).map((entry, index) => (
                  <div key={index} style={{ marginBottom: '16px' }}>
                    <div style={{ padding: '12px', background: '#f0f0f0', borderRadius: '12px', marginBottom: '8px' }}>
                      🤔 {entry.question}
                    </div>
                    <div style={{ padding: '12px', background: '#7c4afd', color: 'white', borderRadius: '12px' }}>
                      {entry.answer}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input Form */}
          <form onSubmit={e => { 
            e.preventDefault(); 
            if (chatMode === 'pal') {
              handleAskPal();
            } else {
              handleAskBook();
            }
          }} style={{ display: 'flex', gap: '12px', padding: '16px', background: 'white', borderRadius: '16px', boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }}>
            
            {/* File upload for book mode */}
            {chatMode === 'book' && (
              <label htmlFor="file-upload-chat" style={{ cursor: 'pointer', padding: '12px', background: '#f8f9fa', borderRadius: '8px' }}>
                📎
                <input 
                  id="file-upload-chat"
                  type="file" 
                  accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif,.bmp,.webp" 
                  style={{ display: 'none' }} 
                  onChange={handleFileUpload}
                  disabled={uploading}
                  multiple
                />
              </label>
            )}

            <input
              type="text"
              value={chatMode === 'pal' ? questionPal : questionBook}
              onChange={e => chatMode === 'pal' ? setQuestionPal(e.target.value) : setQuestionBook(e.target.value)}
              placeholder={chatMode === 'pal' ? "Ask me anything..." : (uploadedFiles.length === 0 ? "Upload documents first..." : "Ask about your documents...")}
              style={{
                flex: 1,
                padding: '12px 16px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1rem'
              }}
              disabled={chatMode === 'book' && uploadedFiles.length === 0}
            />
            
            <button 
              type="submit" 
              disabled={chatMode === 'book' && uploadedFiles.length === 0}
              style={{
                padding: '12px 24px',
                background: '#7c4afd',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '1rem',
                opacity: (chatMode === 'book' && uploadedFiles.length === 0) ? 0.5 : 1
              }}
            >
              Send
            </button>
          </form>
          
          {/* Disclaimer */}
          <div style={{ 
            textAlign: 'center', 
            marginTop: '16px', 
            fontSize: '0.85rem', 
            color: '#666',
            fontStyle: 'italic'
          }}>
            Highpal can also make mistakes.
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
