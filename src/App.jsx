
import { useState, useRef } from 'react';
import './App.css';

function App() {
  const [showDropdown, setShowDropdown] = useState(false);
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [listening, setListening] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const recognitionRef = useRef(null);

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

      // Determine the correct endpoint based on file type
      let endpoint = 'http://localhost:8000/upload';
      if (file.type === 'application/pdf') {
        endpoint = 'http://localhost:8000/upload_pdf/';
      } else if (file.type.startsWith('image/')) {
        endpoint = 'http://localhost:8000/upload_image/';
      }

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
    
    setResponse('🔄 Processing your question... Please wait');
    
    try {
      const requestBody = {
        question: question.trim(),
        uploaded_files: uploadedFiles.map(f => f.id) // Include uploaded files context
      };

      const response = await fetch('http://localhost:8000/ask_question/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        setResponse(data.answer || 'No answer received');
      } else {
        setResponse(`Server error: ${response.status}`);
      }
    } catch (error) {
      setResponse(`Connection error: ${error.message}`);
    }
  };

  return (
  <div style={{ minHeight: '100vh', width: '100vw', background: 'radial-gradient(circle at 10% 10%, #f6f8fc 0%, #fff 100%)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter, Arial, Helvetica, sans-serif', paddingTop: '40px', position: 'relative' }}>
      {/* Login top right */}
      <a href="/login" style={{ position: 'absolute', top: 40, right: 48, textDecoration: 'none', zIndex: 10 }}>
        <span style={{ fontSize: '1rem', color: '#7B61FF', fontWeight: 500, letterSpacing: '0.01em', background: 'transparent', fontFamily: 'Inter, Arial, Helvetica, sans-serif', display: 'inline-block', border: '2px solid #7B61FF', borderRadius: '16px', padding: '6px 18px' }}>
          Login
        </span>
      </a>
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
          Instant, Reliable Academic Help
        </span>
      </div>
      {/* Main heading */}
      <h1 style={{ fontWeight: 700, fontSize: '4rem', color: '#181c2a', textAlign: 'center', marginBottom: '32px', letterSpacing: '-2px', lineHeight: 1.1 }}>
        Don't just cram. <span style={{ color: '#7c4afd' }}>Highpal it!</span>
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
      
      

      {/* Uploaded Files Display */}
      {uploadedFiles.length > 0 && (
        <div style={{
          width: '600px',
          maxWidth: '90vw',
          margin: '0 auto 24px',
          padding: '16px',
          background: '#f8f9ff',
          borderRadius: '16px',
          border: '1px solid #e0d7fa'
        }}>
          <h3 style={{ color: '#7c4afd', marginBottom: '12px', fontSize: '1rem' }}>📁 Uploaded Documents:</h3>
          {uploadedFiles.map((file, index) => (
            <div key={index} style={{
              padding: '8px 12px',
              background: '#fff',
              borderRadius: '8px',
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <span>📄</span>
              <span style={{ flex: 1, fontSize: '0.9rem' }}>{file.name}</span>
              <span style={{ fontSize: '0.8rem', color: '#666' }}>
                {(file.size / 1024).toFixed(1)} KB
              </span>
            </div>
          ))}
        </div>
      )}
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
    </div>
  );
}

export default App;
