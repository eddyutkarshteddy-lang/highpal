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
  
  // Voice functionality state
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [voiceState, setVoiceState] = useState('idle'); // 'idle', 'listening', 'processing', 'speaking'
  const [audioRef, setAudioRef] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  
  // Continuous conversation state
  const [isConversationActive, setIsConversationActive] = useState(false);
  const [conversationTimeout, setConversationTimeout] = useState(null);
  const [turnCount, setTurnCount] = useState(0);
  const continuousRecognitionRef = useRef(null);
  const conversationActiveRef = useRef(false);
  const conversationPausedRef = useRef(false);
  
  // Voice overlay state
  const [showVoiceOverlay, setShowVoiceOverlay] = useState(false);
  const [isConversationPaused, setIsConversationPaused] = useState(false);
  const [inactivityTimeout, setInactivityTimeout] = useState(null);
  const [overlayAnimation, setOverlayAnimation] = useState('slide-up');
  const [lastRecognizedText, setLastRecognizedText] = useState('');
  const [lastProcessedText, setLastProcessedText] = useState('');

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

  // Azure Speech Service configuration from environment variables
  const azureSpeechConfig = {
    subscriptionKey: import.meta.env.VITE_AZURE_SPEECH_KEY,
    region: import.meta.env.VITE_AZURE_SPEECH_REGION || "centralindia",
    voiceName: import.meta.env.VITE_AZURE_SPEECH_VOICE || "en-US-EmmaMultilingualNeural",
    endpoint: `https://${import.meta.env.VITE_AZURE_SPEECH_REGION || "centralindia"}.tts.speech.microsoft.com/`
  };

  // Enhanced Mathematical expression post-processing
  const processMathematicalText = (text) => {
    let processedText = text.toLowerCase();
    
    // More comprehensive mathematical speech patterns and corrections
    const mathCorrections = {
      // Common misheard trigonometric functions
      'sign': 'sin',
      'sine': 'sin',
      'sin of': 'sin',
      'sign of': 'sin',
      'coastline': 'cos',
      'cosign': 'cos',
      'cosine': 'cos',
      'cos of': 'cos',
      'cause': 'cos',
      'course': 'cos',
      'tangent': 'tan',
      'tan of': 'tan',
      'cotangent': 'cot',
      'secant': 'sec',
      'cosecant': 'csc',
      
      // Powers and exponents
      'squared': '²',
      'cubed': '³',
      'to the power of 2': '²',
      'to the power of 3': '³',
      'power 2': '²',
      'power 3': '³',
      'power two': '²',
      'power three': '³',
      'raised to 2': '²',
      'raised to the power 2': '²',
      
      // Greek letters (common misheard)
      'theta': 'θ',
      'beta': 'β',
      'alpha': 'α',
      'gamma': 'γ',
      'delta': 'δ',
      'lambda': 'λ',
      'pi': 'π',
      'sigma': 'σ',
      'omega': 'ω',
      'phi': 'φ',
      'data': 'θ', // Common mishearing
      'theater': 'θ',
      'feta': 'θ',
      
      // Mathematical operators
      'plus': '+',
      'add': '+',
      'minus': '-',
      'subtract': '-',
      'times': '×',
      'multiply': '×',
      'divided by': '÷',
      'equals': '=',
      'equal to': '=',
      'not equal': '≠',
      'less than or equal': '≤',
      'greater than or equal': '≥',
      
      // Common mathematical terms that get misheard
      'derivative': 'derivative',
      'integral': 'integral',
      'limit': 'limit',
      'infinity': '∞',
      'root': '√',
      'square root': '√',
      
      // Question starters
      'what is': 'what is',
      'find': 'find',
      'calculate': 'calculate',
      'solve': 'solve',
      'evaluate': 'evaluate',
    };
    
    // Apply corrections with word boundaries
    Object.entries(mathCorrections).forEach(([wrong, correct]) => {
      const regex = new RegExp(`\\b${wrong.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
      processedText = processedText.replace(regex, correct);
    });
    
    // Handle specific mathematical expressions with more patterns
    processedText = processedText
      // Fix sin squared patterns
      .replace(/sin\s*\^?\s*2/gi, 'sin²')
      .replace(/sine\s*squared/gi, 'sin²')
      .replace(/sign\s*squared/gi, 'sin²')
      // Fix cos squared patterns  
      .replace(/cos\s*\^?\s*2/gi, 'cos²')
      .replace(/cosine\s*squared/gi, 'cos²')
      .replace(/cause\s*squared/gi, 'cos²')
      // Fix variable squares
      .replace(/\bx\s*\^?\s*2/gi, 'x²')
      .replace(/\by\s*\^?\s*2/gi, 'y²')
      .replace(/\bz\s*\^?\s*2/gi, 'z²')
      // Fix theta patterns
      .replace(/\bdata\b/gi, 'θ')
      .replace(/\bfeta\b/gi, 'θ')
      .replace(/\btheater\b/gi, 'θ')
      // Clean up spacing
      .replace(/\s+/g, ' ')
      .trim();
    
    return processedText;
  };

  // Continuous conversation helper functions
  const isEndCommand = (text) => {
    const endPhrases = [
      'bye', 'goodbye', 'exit', 'quit', 'stop', 'end conversation', 
      'that\'s all', 'thank you', 'thanks', 'end', 'finish'
    ];
    return endPhrases.some(phrase => text.toLowerCase().includes(phrase));
  };

  const startContinuousListening = () => {
    return new Promise((resolve, reject) => {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        reject(new Error('Speech recognition not supported'));
        return;
      }

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      // Optimize settings for much better accuracy
      recognition.continuous = true; // Allow longer speech
      recognition.interimResults = true; // Show results as user speaks
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 3; // Get multiple options

      let finalTranscript = '';
      let timeout = setTimeout(() => {
        recognition.stop();
        if (finalTranscript.trim()) {
          resolve(finalTranscript.trim());
        } else {
          reject(new Error('No speech detected'));
        }
      }, 20000); // 20 second timeout

      recognition.onresult = (event) => {
        let interimTranscript = '';
        
        // Process all results
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            console.log('🎤 FINAL SPEECH:', finalTranscript);
            
            // Clear timeout and resolve immediately when we get final result
            clearTimeout(timeout);
            
            // Apply mathematical text processing
            const processedTranscript = processMathematicalText(finalTranscript.trim());
            console.log('🧮 PROCESSED:', processedTranscript);
            
            // Store for debugging display
            setLastRecognizedText(finalTranscript.trim());
            setLastProcessedText(processedTranscript);
            
            recognition.stop();
            resolve(processedTranscript);
            return;
          } else {
            interimTranscript += transcript;
            console.log('🎤 INTERIM:', interimTranscript);
          }
        }
      };

      recognition.onerror = (event) => {
        clearTimeout(timeout);
        console.error('Speech recognition error:', event.error);
        
        // Try to restart recognition on certain errors
        if (event.error === 'no-speech' || event.error === 'audio-capture') {
          setTimeout(() => {
            console.log('Restarting speech recognition...');
            recognition.start();
          }, 1000);
        } else {
          reject(new Error(`Speech recognition error: ${event.error}`));
        }
      };

      recognition.onstart = () => {
        console.log('🎤 Speech recognition started - speak now!');
      };

      recognition.onend = () => {
        console.log('🎤 Speech recognition ended');
        clearTimeout(timeout);
      };

      continuousRecognitionRef.current = recognition;
      
      // Start recognition
      try {
        recognition.start();
      } catch (error) {
        reject(new Error(`Failed to start recognition: ${error.message}`));
      }
    });
  };

  const endConversation = () => {
    console.log('Ending conversation');
    setIsConversationActive(false);
    conversationActiveRef.current = false;
    conversationPausedRef.current = false;
    setVoiceState('idle');
    setTurnCount(0);
    setIsConversationPaused(false);
    setShowVoiceOverlay(false);
    
    // Stop any ongoing recognition
    if (continuousRecognitionRef.current) {
      continuousRecognitionRef.current.stop();
      continuousRecognitionRef.current = null;
    }
    
    // Clear any timeouts
    if (conversationTimeout) {
      clearTimeout(conversationTimeout);
      setConversationTimeout(null);
    }
    
    if (inactivityTimeout) {
      clearTimeout(inactivityTimeout);
      setInactivityTimeout(null);
    }
  };

  const pauseConversation = () => {
    console.log('Pausing conversation');
    setIsConversationPaused(true);
    conversationPausedRef.current = true;
    setVoiceState('idle');
    
    // Stop ongoing recognition
    if (continuousRecognitionRef.current) {
      continuousRecognitionRef.current.stop();
      continuousRecognitionRef.current = null;
    }
    
    // Clear inactivity timeout since we're pausing
    if (inactivityTimeout) {
      clearTimeout(inactivityTimeout);
      setInactivityTimeout(null);
    }
  };

  const resumeConversation = () => {
    console.log('Resuming conversation');
    setIsConversationPaused(false);
    conversationPausedRef.current = false;
    
    // Restart conversation loop
    setTimeout(() => {
      conversationLoop();
    }, 500);
  };

  const startInactivityTimer = () => {
    // Clear existing timer
    if (inactivityTimeout) {
      clearTimeout(inactivityTimeout);
    }
    
    // Set 5-minute (300000ms) timer
    const timer = setTimeout(() => {
      console.log('Auto-pausing due to inactivity');
      pauseConversation();
    }, 300000);
    
    setInactivityTimeout(timer);
  };

  // Play AI response using browser speech synthesis (fallback) or Azure Speech Service
  const playAIResponse = async (text) => {
    try {
      console.log('Playing AI response:', text);
      
      // Try Azure Speech Service first
      try {
        const response = await fetch(`${azureSpeechConfig.endpoint}cognitiveservices/v1`, {
          method: 'POST',
          headers: {
            'Ocp-Apim-Subscription-Key': azureSpeechConfig.subscriptionKey,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
          },
          body: `
            <speak version='1.0' xml:lang='en-US'>
              <voice xml:lang='en-US' xml:gender='Female' name='${azureSpeechConfig.voiceName}'>
                <prosody rate='0.9' pitch='medium'>
                  ${text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}
                </prosody>
              </voice>
            </speak>
          `
        });

        if (response.ok) {
          const audioBlob = await response.blob();
          const audioUrl = URL.createObjectURL(audioBlob);
          
          return new Promise((resolve, reject) => {
            const audio = new Audio(audioUrl);
            audio.onloadeddata = () => {
              console.log('Audio loaded, playing...');
              audio.play().then(() => {
                setCurrentAudio(audio);
              }).catch(reject);
            };
            audio.onended = () => {
              console.log('Audio playback finished');
              URL.revokeObjectURL(audioUrl);
              setCurrentAudio(null);
              resolve();
            };
            audio.onerror = (error) => {
              console.error('Audio playback error:', error);
              URL.revokeObjectURL(audioUrl);
              reject(error);
            };
          });
        } else {
          throw new Error(`Azure Speech Service error: ${response.status}`);
        }
      } catch (azureError) {
        console.warn('Azure Speech failed, using browser fallback:', azureError.message);
        
        // Fallback to browser speech synthesis
        return new Promise((resolve, reject) => {
          if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 1;
            
            // Try to use a female voice
            const voices = speechSynthesis.getVoices();
            const femaleVoice = voices.find(voice => 
              voice.name.toLowerCase().includes('female') || 
              voice.name.toLowerCase().includes('zira') ||
              voice.name.toLowerCase().includes('hazel') ||
              voice.gender === 'female'
            );
            if (femaleVoice) {
              utterance.voice = femaleVoice;
            }
            
            utterance.onend = () => {
              console.log('Browser speech finished');
              resolve();
            };
            utterance.onerror = (error) => {
              console.error('Browser speech error:', error);
              reject(error);
            };
            
            speechSynthesis.speak(utterance);
          } else {
            reject(new Error('Speech synthesis not supported'));
          }
        });
      }
    } catch (error) {
      console.error('Error playing AI response:', error);
      throw error;
    }
  };

  // Main voice conversation handler for continuous mode
  const handleVoiceConversation = async () => {
    console.log('Voice button clicked, current state:', voiceState, 'Active:', isConversationActive);
    
    if (isConversationActive) {
      // End the conversation with smooth overlay exit
      setOverlayAnimation('slide-down');
      await playAIResponse("Ending our conversation. Goodbye!");
      setTimeout(() => {
        endConversation();
      }, 300); // Wait for animation to complete
      return;
    }

    // Check microphone permissions
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop()); // Stop the stream immediately
    } catch (error) {
      console.error('Microphone access denied:', error);
      alert('Microphone access is required for voice conversation. Please:\n\n1. Click the microphone icon 🎤 in your browser address bar\n2. Select "Allow"\n3. Refresh the page and try again\n\nOr check your browser microphone settings.');
      return;
    }

    // Start continuous conversation with overlay
    setShowVoiceOverlay(true);
    setOverlayAnimation('slide-up');
    await startContinuousConversation();
  };

  const startContinuousConversation = async () => {
    console.log('Starting continuous conversation');
    setIsConversationActive(true);
    conversationActiveRef.current = true;
    conversationPausedRef.current = false;
    setTurnCount(0);
    
    // Welcome message
    setVoiceState('speaking');
    const welcomeMessage = "Hi! I'm Pal, your AI tutor. I'm ready for our conversation - what would you like to learn about today?";
    await playAIResponse(welcomeMessage);
    
    // Small delay to ensure state is updated, then start the conversation loop
    setTimeout(() => {
      conversationLoop();
    }, 500);
  };

  const conversationLoop = async () => {
    console.log('ConversationLoop started, conversationActiveRef:', conversationActiveRef.current);
    
    while (conversationActiveRef.current && !conversationPausedRef.current) {
      try {
        console.log('Starting new turn in conversation loop');
        
        // Double check if conversation was ended or paused
        if (!conversationActiveRef.current || conversationPausedRef.current) {
          console.log('Conversation was ended or paused, breaking loop');
          break;
        }
        
        setVoiceState('listening');
        console.log('Voice state set to listening, about to start listening...');
        
        // Start inactivity timer
        startInactivityTimer();
        
        // Listen for user input
        const userInput = await startContinuousListening();
        console.log('User said:', userInput);
        
        // Clear inactivity timer since user spoke
        if (inactivityTimeout) {
          clearTimeout(inactivityTimeout);
          setInactivityTimeout(null);
        }
        
        // Check if user wants to end conversation
        if (isEndCommand(userInput)) {
          setOverlayAnimation('slide-down');
          await playAIResponse("Goodbye! Thanks for our conversation. Feel free to chat with me anytime!");
          setTimeout(() => {
            endConversation();
          }, 300);
          return;
        }
        
        // Process the question
        setVoiceState('processing');
        const aiResponse = await getAIResponse(userInput);
        
        // Add follow-up prompt to continue conversation
        const responseWithPrompt = `${aiResponse}\n\nDo you have any other questions?`;
        
        // Speak the response
        setVoiceState('speaking');
        await playAIResponse(responseWithPrompt);
        
        // Increment turn count
        setTurnCount(prev => prev + 1);
        
        // Brief pause before next listen
        await new Promise(resolve => setTimeout(resolve, 2000));
        
      } catch (error) {
        console.log('Conversation error:', error.message);
        
        if (error.message === 'Speech timeout') {
          // Handle timeout gracefully - auto-pause instead of continuing
          console.log('Speech timeout - auto-pausing conversation');
          pauseConversation();
          break;
        } else {
          // Other errors - end conversation
          console.error('Ending conversation due to error:', error);
          endConversation();
          break;
        }
      }
    }
    console.log('ConversationLoop ended');
  };

  const getAIResponse = async (question) => {
    try {
      console.log('Sending to AI:', question);
      const response = await fetch('http://localhost:8003/ask_question/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: question,
          uploaded_files: [],
          is_first_message: conversationHistoryPal.length === 0
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      const aiResponse = data.answer || 'I apologize, but I couldn\'t process that question properly.';
      
      // Update conversation history
      const newEntry = { question: question, answer: aiResponse };
      setConversationHistoryPal(prev => [...prev, newEntry]);
      
      return aiResponse;
      
    } catch (error) {
      console.error('AI response error:', error);
      return 'I\'m having trouble processing that right now. Could you try asking in a different way?';
    }
  };

  // Enhanced Mic functionality with better accuracy
  const handleMicClick = () => {
    if (!listening) {
      const recognition = new window.webkitSpeechRecognition();
      
      // Enhanced settings for better speech recognition
      recognition.continuous = true; // Allow longer speech
      recognition.interimResults = true; // Show real-time results
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 3; // Multiple alternatives
      
      let finalTranscript = '';
      
      recognition.onresult = (event) => {
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            console.log('🎤 Mic Final:', finalTranscript);
            
            // Apply mathematical text processing
            const processedText = processMathematicalText(finalTranscript.trim());
            console.log('🧮 Mic Processed:', processedText);
            
            if (chatMode === 'pal') {
              setQuestionPal(processedText);
            } else {
              setQuestionBook(processedText);
            }
            setListening(false);
            recognition.stop();
          } else {
            interimTranscript += transcript;
            console.log('🎤 Mic Interim:', interimTranscript);
            
            // Show interim results in real-time
            if (chatMode === 'pal') {
              setQuestionPal(interimTranscript);
            } else {
              setQuestionBook(interimTranscript);
            }
          }
        }
      };
      
      recognition.onerror = (event) => {
        console.error('Mic recognition error:', event.error);
        setListening(false);
      };
      
      recognition.onend = () => {
        console.log('🎤 Mic recognition ended');
        setListening(false);
      };
      
      recognition.onstart = () => {
        console.log('🎤 Mic recognition started');
      };
      
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
        uploaded_files: []
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
        uploaded_files: uploadedFiles.map(f => f.id)
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

            {/* Voice Conversation Button */}
            <button 
              type="button"
              onClick={handleVoiceConversation}
              disabled={chatMode === 'book' && uploadedFiles.length === 0}
              style={{
                padding: '12px',
                background: isConversationActive && voiceState === 'idle' ? '#dc3545' :
                           voiceState === 'idle' ? '#28a745' : 
                           voiceState === 'listening' ? '#28a745' : 
                           voiceState === 'processing' ? '#ffc107' : '#17a2b8',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '1.2rem',
                minWidth: '48px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: (chatMode === 'book' && uploadedFiles.length === 0) ? 0.5 : 1,
                transition: 'all 0.3s ease'
              }}
              title={
                isConversationActive ? 'End voice conversation' :
                voiceState === 'idle' ? 'Start continuous voice conversation' :
                voiceState === 'listening' ? 'Listening... (conversation active)' :
                voiceState === 'processing' ? 'Processing...' :
                'Speaking...'
              }
            >
              {isConversationActive && voiceState === 'idle' && '🔴'}
              {!isConversationActive && voiceState === 'idle' && '🎤'}
              {voiceState === 'listening' && '🎤'}
              {voiceState === 'processing' && '⏳'}
              {voiceState === 'speaking' && '🔊'}
            </button>
          </form>
        </div>
      )}
      
      {/* Voice Conversation Overlay */}
      {showVoiceOverlay && (
        <div 
          className={`voice-overlay ${overlayAnimation}`}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            background: 'rgba(124, 74, 253, 0.15)',
            backdropFilter: 'blur(20px)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            gap: '32px'
          }}
        >
          {/* Voice Status Display */}
          <div style={{
            textAlign: 'center',
            color: '#181c2a',
            marginBottom: '40px'
          }}>
            <div style={{
              fontSize: '4rem',
              marginBottom: '16px'
            }}>
              {isConversationPaused ? '⏸️' :
               voiceState === 'listening' ? '🎤' :
               voiceState === 'processing' ? '⚡' :
               voiceState === 'speaking' ? '🔊' : '🎧'}
            </div>
            <h2 style={{
              fontSize: '2.5rem',
              fontWeight: '700',
              marginBottom: '8px'
            }}>
              {isConversationPaused ? 'Conversation Paused' :
               voiceState === 'listening' ? 'Listening...' :
               voiceState === 'processing' ? 'Thinking...' :
               voiceState === 'speaking' ? 'Speaking...' : 'Voice Mode Active'}
            </h2>
            <p style={{
              fontSize: '1.2rem',
              opacity: 0.8
            }}>
              {isConversationPaused ? 'Click RESUME to continue or END to finish' :
               voiceState === 'listening' ? 'Speak now, I\'m listening to your question' :
               voiceState === 'processing' ? 'Processing your question and preparing response' :
               voiceState === 'speaking' ? 'Listen to my response' : 'Ready for conversation'}
            </p>
            
            {/* Mathematical Recognition Feedback */}
            {(lastRecognizedText || lastProcessedText) && (
              <div style={{
                marginTop: '20px',
                padding: '16px',
                background: 'rgba(255,255,255,0.9)',
                borderRadius: '12px',
                fontSize: '0.9rem',
                maxWidth: '500px',
                margin: '20px auto 0'
              }}>
                {lastRecognizedText && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🎤 What I heard:</strong> 
                    <br />
                    <span style={{ 
                      fontFamily: 'monospace', 
                      background: '#f0f0f0', 
                      padding: '4px 8px', 
                      borderRadius: '4px',
                      display: 'inline-block',
                      marginTop: '4px'
                    }}>
                      {lastRecognizedText}
                    </span>
                  </div>
                )}
                {lastProcessedText && lastProcessedText !== lastRecognizedText && (
                  <div>
                    <strong>🧮 Mathematical correction:</strong>
                    <br />
                    <span style={{ 
                      fontFamily: 'monospace', 
                      color: '#7c4afd',
                      background: '#f8f5ff',
                      padding: '4px 8px', 
                      borderRadius: '4px',
                      display: 'inline-block',
                      marginTop: '4px'
                    }}>
                      {lastProcessedText}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Control Buttons */}
          <div style={{
            display: 'flex',
            gap: '24px',
            alignItems: 'center'
          }}>
            {/* PAUSE/RESUME Button */}
            <button
              onClick={isConversationPaused ? resumeConversation : pauseConversation}
              disabled={voiceState === 'processing' || voiceState === 'speaking'}
              style={{
                padding: '16px 32px',
                background: isConversationPaused ? '#28a745' : '#ffc107',
                color: 'white',
                border: 'none',
                borderRadius: '50px',
                fontSize: '1.2rem',
                fontWeight: '600',
                cursor: 'pointer',
                minWidth: '140px',
                boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
                transition: 'all 0.3s ease',
                opacity: (voiceState === 'processing' || voiceState === 'speaking') ? 0.6 : 1
              }}
            >
              {isConversationPaused ? '▶️ RESUME' : '⏸️ PAUSE'}
            </button>

            {/* END Button */}
            <button
              onClick={async () => {
                setOverlayAnimation('slide-down');
                await playAIResponse("Ending our conversation. Goodbye!");
                setTimeout(() => {
                  endConversation();
                }, 300);
              }}
              style={{
                padding: '16px 32px',
                background: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '50px',
                fontSize: '1.2rem',
                fontWeight: '600',
                cursor: 'pointer',
                minWidth: '140px',
                boxShadow: '0 4px 16px rgba(220, 53, 69, 0.3)',
                transition: 'all 0.3s ease'
              }}
            >
              🔴 END
            </button>
          </div>

          {/* Conversation Stats */}
          {turnCount > 0 && (
            <div style={{
              position: 'absolute',
              bottom: '40px',
              left: '50%',
              transform: 'translateX(-50%)',
              color: '#181c2a',
              fontSize: '1rem',
              opacity: 0.7,
              textAlign: 'center'
            }}>
              <p>Conversation turns: {turnCount}</p>
              <p style={{ fontSize: '0.9rem', marginTop: '4px' }}>
                Say "goodbye" or "end" to finish naturally
              </p>
            </div>
          )}
          
          {/* Enhanced Speech Tips */}
          {voiceState === 'listening' && (
            <div style={{
              position: 'absolute',
              bottom: '40px',
              right: '40px',
              background: 'rgba(255,255,255,0.95)',
              padding: '16px',
              borderRadius: '12px',
              fontSize: '0.85rem',
              maxWidth: '280px',
              color: '#181c2a',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
            }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#7c4afd' }}>🎤 Speech Tips:</h4>
              <p style={{ margin: '6px 0', lineHeight: '1.4' }}>
                <strong>📢 Speak clearly and slowly</strong>
              </p>
              <p style={{ margin: '6px 0', lineHeight: '1.4' }}>
                <strong>🧮 For math:</strong> "sine squared theta plus cosine squared theta"
              </p>
              <p style={{ margin: '6px 0', lineHeight: '1.4' }}>
                <strong>⏸️ Pause briefly</strong> between complex terms
              </p>
              <p style={{ margin: '6px 0', lineHeight: '1.4' }}>
                <strong>🔄 Repeat</strong> if not recognized correctly
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
