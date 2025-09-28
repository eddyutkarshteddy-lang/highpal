import { useState, useRef, useEffect } from 'react';
import './App.css';
import RevisionMode from './components/RevisionMode';

function App() {
  console.log('🚀 HighPal App component is rendering');
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
  
  // Saved conversations (talks) state - initialize with stored talks
  const [savedTalks, setSavedTalks] = useState(() => {
    try {
      const stored = localStorage.getItem('highpal_saved_talks');
      if (!stored) return [];
      
      const talks = JSON.parse(stored);
      
      // Remove duplicates based on title and complete history content
      const uniqueTalks = [];
      const seen = new Set();
      
      for (const talk of talks) {
        // Create a more comprehensive key for duplicate detection
        const historyKey = JSON.stringify(talk.history);
        const key = `${talk.title}-${historyKey}`;
        
        if (!seen.has(key)) {
          seen.add(key);
          uniqueTalks.push(talk);
        }
      }
      
      // If we removed duplicates, save the cleaned version
      if (uniqueTalks.length !== talks.length) {
        localStorage.setItem('highpal_saved_talks', JSON.stringify(uniqueTalks));
      }
      
      return uniqueTalks;
    } catch (e) {
      console.log('Could not load saved talks on init:', e);
      return [];
    }
  });
  const [currentTalkId, setCurrentTalkId] = useState(null);
  const [showTalksSidebar, setShowTalksSidebar] = useState(true);
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

  // Load saved talks from localStorage
  const loadSavedTalks = () => {
    try {
      const stored = localStorage.getItem('highpal_saved_talks');
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.log('Could not load saved talks:', e);
      return [];
    }
  };

  // Save talks to localStorage
  const saveTalksToStorage = (talks) => {
    try {
      localStorage.setItem('highpal_saved_talks', JSON.stringify(talks));
    } catch (e) {
      console.log('Could not save talks:', e);
    }
  };



  // Generate conversation title from first question
  const generateTalkTitle = (conversationHistory) => {
    if (conversationHistory.length === 0) return 'New Chat';
    const firstQuestion = conversationHistory[0].question;
    if (firstQuestion.length > 30) {
      return firstQuestion.substring(0, 30) + '...';
    }
    return firstQuestion;
  };

  // Save current conversation as a talk
  const saveCurrentTalk = () => {
    const currentHistory = chatMode === 'pal' ? conversationHistoryPal : conversationHistoryBook;
    if (currentHistory.length === 0) return;

    const talkId = currentTalkId || Date.now().toString();
    
    // Check if this conversation already exists and is identical
    const existingTalk = savedTalks.find(talk => talk.id === talkId);
    if (existingTalk && JSON.stringify(existingTalk.history) === JSON.stringify(currentHistory)) {
      // No changes, don't save
      return;
    }
    
    const title = generateTalkTitle(currentHistory);
    
    const newTalk = {
      id: talkId,
      title: title,
      mode: chatMode,
      history: [...currentHistory],
      createdAt: existingTalk ? existingTalk.createdAt : new Date().toISOString(),
      lastModified: new Date().toISOString()
    };

    const updatedTalks = savedTalks.filter(talk => talk.id !== talkId);
    updatedTalks.unshift(newTalk);
    
    setSavedTalks(updatedTalks);
    saveTalksToStorage(updatedTalks);
    setCurrentTalkId(talkId);
  };

  // Start a new chat
  const startNewChat = () => {
    // Save current conversation if it has content
    saveCurrentTalk();
    
    // Clear current conversation
    if (chatMode === 'pal') {
      setConversationHistoryPal([]);
    } else {
      setConversationHistoryBook([]);
    }
    setCurrentTalkId(null);
  };

  // Load a saved talk
  const loadTalk = (talk) => {
    // Save current conversation first if it has content and it's different from the one we're loading
    if (currentTalkId !== talk.id) {
      saveCurrentTalk();
    }

    // Load the selected talk
    setChatMode(talk.mode);
    if (talk.mode === 'pal') {
      setConversationHistoryPal(talk.history);
    } else {
      setConversationHistoryBook(talk.history);
    }
    setCurrentTalkId(talk.id);
  };

  // Delete a talk
  const deleteTalk = (talkId) => {
    const updatedTalks = savedTalks.filter(talk => talk.id !== talkId);
    setSavedTalks(updatedTalks);
    saveTalksToStorage(updatedTalks);
    
    // If we're deleting the current talk, clear the conversation
    if (currentTalkId === talkId) {
      if (chatMode === 'pal') {
        setConversationHistoryPal([]);
      } else {
        setConversationHistoryBook([]);
      }
      setCurrentTalkId(null);
    }
  };

  // Track if we're on initial load to prevent auto-save on restore
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  
  useEffect(() => {
    // Set initial load to false after component mounts
    const timer = setTimeout(() => setIsInitialLoad(false), 1000);
    
    // Clean up old localStorage system
    try {
      localStorage.removeItem('highpal_conversation_history');
    } catch (e) {
      console.log('Could not clean old storage:', e);
    }
    
    return () => clearTimeout(timer);
  }, []);

  // Auto-save current conversation when it changes (but not on initial load)
  useEffect(() => {
    if (!isInitialLoad && conversationHistoryPal.length > 0 && chatMode === 'pal') {
      const timeoutId = setTimeout(() => saveCurrentTalk(), 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [conversationHistoryPal, isInitialLoad]);

  useEffect(() => {
    if (!isInitialLoad && conversationHistoryBook.length > 0 && chatMode === 'book') {
      const timeoutId = setTimeout(() => saveCurrentTalk(), 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [conversationHistoryBook, isInitialLoad]);

  // Load existing documents from MongoDB on app start
  const loadExistingDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8003/documents', {
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

  // Keyboard interrupt support (backup for barge-in)
  useEffect(() => {
    const handleKeyPress = (event) => {
      // Press 'i' to interrupt while AI is speaking, or SPACEBAR for topic change
      // ONLY work when AI is actively speaking - prevent accidental triggers
      if ((event.key === 'i' || event.key === ' ') && 
          isConversationActive && 
          (voiceState === 'speaking' || currentAudio || speechSynthesis.speaking) &&
          !event.target.matches('input, textarea, [contenteditable]')) { // Don't trigger in form fields
        // Prevent default spacebar behavior (like scrolling or form submission)
        event.preventDefault();
        event.stopPropagation();
        
        const isTopicChange = event.key === ' '; // Spacebar = topic change
        const isCuriosityQuestion = event.key === 'i'; // 'i' = curiosity question
        
        if (isTopicChange) {
          console.log('🎹 Topic change interrupt triggered (spacebar)');
          console.log('🎯 Stopping AI to allow topic change...');
        } else {
          console.log('🎹 Curiosity question interrupt triggered (i key)');
          console.log('🤔 Stopping AI to allow curiosity question...');
        }
        
        killAllAudio();
        setVoiceState('listening');
        
        // Start listening based on interrupt type
        setTimeout(async () => {
          try {
            if (isTopicChange) {
              console.log('🎤 Listening for your new topic...');
            } else {
              console.log('🎤 Listening for your curiosity question...');
            }
            
            const userInput = await startContinuousListening();
            
            if (userInput && userInput.trim().length > 0) {
              if (isTopicChange) {
                console.log('✅ New topic:', userInput);
                // For topic change, send as new conversation
                setVoiceState('processing');
                const aiResponse = await getAIResponse(userInput);
                setVoiceState('speaking');
                await playAIResponse(aiResponse);
              } else {
                console.log('✅ Curiosity question:', userInput);
                
                // SIMPLE APPROACH: Just send the question directly
                // The backend now has conversation history, so it should maintain context automatically
                console.log('🧠 Sending curiosity question directly (backend will maintain context)');
                setVoiceState('processing');
                const aiResponse = await getAIResponse(userInput);
                setVoiceState('speaking');
                await playAIResponse(aiResponse);
              }
            } else {
              console.log('ℹ️ No input detected, continuing conversation...');
              setVoiceState('listening');
            }
          } catch (error) {
            console.log('Error with interrupt:', error);
            setVoiceState('listening');
          }
        }, 200);
      }
    };

    // Only add listener when conversation is active
    if (isConversationActive) {
      window.addEventListener('keydown', handleKeyPress, true); // Use capture phase
      return () => window.removeEventListener('keydown', handleKeyPress, true);
    }
  }, [voiceState, currentAudio]);

  // Azure Speech Service configuration from environment variables
  const azureSpeechConfig = {
    subscriptionKey: import.meta.env.VITE_AZURE_SPEECH_KEY,
    region: import.meta.env.VITE_AZURE_SPEECH_REGION || "centralindia",
    voiceName: "en-US-AriaNeural", // Force AriaNeural voice
    endpoint: `https://${import.meta.env.VITE_AZURE_SPEECH_REGION || "centralindia"}.tts.speech.microsoft.com/`
  };

  // Debug logging for voice configuration
  console.log('🎤 Azure Speech Config:', {
    region: azureSpeechConfig.region,
    voiceName: azureSpeechConfig.voiceName,
    endpoint: azureSpeechConfig.endpoint,
    hasKey: !!azureSpeechConfig.subscriptionKey
  });

  // Utility function for requests with timeout
  const fetchWithTimeout = (url, options, timeout = 4000) => {
    return Promise.race([
      fetch(url, options),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), timeout)
      )
    ]);
  };



  // Smart Mathematical expression post-processing (only for math questions)
  const isMathematicalQuery = (text) => {
    const cleanText = text.toLowerCase().trim();
    
    // If it's too short (like "hi"), it's definitely not math
    if (cleanText.length <= 5) {
      return false;
    }
    
    const mathKeywords = [
      'sin', 'cos', 'tan', 'theta', 'calculate', 'solve', 'find area', 'find the',
      'squared', 'power', 'equals', 'plus', 'minus', 'times', 'divided',
      'derivative', 'integral', 'limit', 'equation', 'formula', 'root',
      'triangle', 'rectangle', 'circle', 'square', 'geometry',
      '+', '-', '×', '÷', '=', '^', '²', '³', 'π', '∞'
    ];
    
    // Need at least 2 math indicators or very specific math terms
    const mathMatches = mathKeywords.filter(keyword => cleanText.includes(keyword));
    return mathMatches.length >= 1 && (cleanText.includes('what is') || cleanText.includes('calculate') || cleanText.includes('find') || cleanText.includes('area') || cleanText.includes('formula'));
  };

  const isConversationalQuery = (text) => {
    const cleanText = text.toLowerCase().trim();
    
    // Very short queries are likely conversational
    if (cleanText.length <= 15) {
      return true;
    }
    
    const conversationalKeywords = [
      'hi', 'hello', 'hey', 'how are you', 'good morning', 'good evening',
      'bye', 'goodbye', 'thanks', 'thank you', 'nice to meet you',
      'how do you do', 'what\'s up', 'how\'s it going', 'see you later',
      'hows it going', 'whats up', 'good day', 'greetings', 'what are you doing',
      'how\'s your day', 'hows your day', 'what\'s happening', 'whats happening',
      'how\'s everything', 'hows everything', 'nice weather', 'good to see you',
      'how have you been', 'long time no see', 'what\'s new', 'whats new',
      'sup', 'yo', 'wassup', 'howdy', 'morning', 'evening', 'night'
    ];
    
    return conversationalKeywords.some(keyword => cleanText.includes(keyword));
  };

  // Smart timeout function based on question type
  const getSmartTimeout = (question) => {
    if (isConversationalQuery(question)) {
      console.log('💬 Conversational query detected - using fast timeout');
      return 3000; // 3 seconds for conversations (reliable)
    } else {
      console.log('🎓 Educational query detected - using standard timeout');
      return 5000; // 5 seconds for educational questions
    }
  };

  const processMathematicalText = (text) => {
    console.log('🎤 Original speech input:', text);
    
    // Don't process conversational text mathematically
    if (isConversationalQuery(text)) {
      console.log('✅ Detected as conversational, keeping original:', text);
      return text;
    }

    // Only apply mathematical processing if it seems like a math question
    if (!isMathematicalQuery(text)) {
      console.log('✅ Not mathematical, keeping original:', text);
      return text;
    }

    console.log('🧮 Applying mathematical processing to:', text);

    let processedText = text.toLowerCase();
    
    // Only essential mathematical corrections (removed aggressive ones)
    const mathCorrections = {
      // Trigonometric functions (only when in math context)
      'sine': 'sin',
      'cosine': 'cos',
      'tangent': 'tan',
      
      // Powers and exponents
      'squared': '²',
      'cubed': '³',
      'to the power of 2': '²',
      'to the power of 3': '³',
      
      // Only clear Greek letters (removed problematic ones)
      'theta': 'θ',
      'pi': 'π',
      
      // Mathematical operators
      'plus': '+',
      'minus': '-',
      'times': '×',
      'divided by': '÷',
      'equals': '=',
      'square root': '√',
    };
    
    // Apply corrections with word boundaries (only in mathematical context)
    Object.entries(mathCorrections).forEach(([wrong, correct]) => {
      const regex = new RegExp(`\\b${wrong.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
      processedText = processedText.replace(regex, correct);
    });
    
    // Handle specific mathematical expressions
    processedText = processedText
      .replace(/sin\s*\^?\s*2/gi, 'sin²')
      .replace(/cos\s*\^?\s*2/gi, 'cos²')
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

  // Nuclear option: Stop ALL audio immediately
  const killAllAudio = () => {
    console.log('� NUCLEAR AUDIO STOP - Killing everything!');
    
    // Multiple attempts to stop current audio
    if (currentAudio) {
      try {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio.src = '';
        currentAudio.load();
        currentAudio.volume = 0; // Mute as backup
        setCurrentAudio(null);
        console.log('✅ Nuclear stopped Azure audio');
      } catch (e) {
        console.log('Error in nuclear Azure stop:', e);
      }
    }
    
    // Multiple attempts to stop speech synthesis
    try {
      speechSynthesis.cancel();
      speechSynthesis.pause();
      // Try multiple times for stubborn browsers
      setTimeout(() => speechSynthesis.cancel(), 10);
      setTimeout(() => speechSynthesis.cancel(), 50);
      console.log('✅ Nuclear stopped speech synthesis');
    } catch (e) {
      console.log('Error in nuclear speech stop:', e);
    }
    
    // Stop ALL audio elements on the page
    try {
      document.querySelectorAll('audio, video').forEach(element => {
        element.pause();
        element.currentTime = 0;
        element.volume = 0;
        element.src = '';
        console.log('✅ Nuclear stopped media element');
      });
    } catch (e) {
      console.log('Error stopping media elements:', e);
    }
    
    // Try to stop Web Audio API contexts
    try {
      if (window.AudioContext || window.webkitAudioContext) {
        // This is a more aggressive approach
        console.log('Attempting Web Audio API suspension');
      }
    } catch (e) {
      console.log('No Web Audio to stop');
    }
  };

  // Enhanced audio stopping functionality
  const stopCurrentAudio = () => {
    console.log('🛑 FORCE STOPPING all audio due to barge-in');
    
    // Use nuclear option first
    killAllAudio();
    
    // Immediately switch to listening state after interruption
    setVoiceState('listening');
    console.log('🎤 Voice state set to listening after barge-in');
  };

  // Simplified barge-in detection using audio level monitoring
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const microphoneRef = useRef(null);
  const bargeInDetectedRef = useRef(false);
  const audioMonitoringRef = useRef(false);
  const lastInterruptionTime = useRef(0);

  // Start simple audio level monitoring for barge-in
  const startBargeInDetection = () => {
    if (audioMonitoringRef.current) {
      console.log('Barge-in detection already running');
      return;
    }

    console.log('🎙️ Starting simplified barge-in detection...');
    
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        console.log('✅ Got microphone access for barge-in');
        audioMonitoringRef.current = true;
        
        // Create audio context and analyser
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const microphone = audioContext.createMediaStreamSource(stream);
        
        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        microphoneRef.current = microphone;
        
        microphone.connect(analyser);
        analyser.fftSize = 256;
        
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        // Monitor audio levels
        const checkAudioLevel = () => {
          if (!audioMonitoringRef.current) {
            console.log('⏹️ Audio monitoring stopped');
            return;
          }
          
          // SIMPLIFIED: Only pause detection if explicitly in listening mode with no audio
          if (voiceState === 'listening' && !currentAudio && !speechSynthesis.speaking) {
            // Still monitor but don't interrupt during user speech
            requestAnimationFrame(checkAudioLevel);
            return;
          }
          
          console.log('🔊 Current voice state:', voiceState);
          
          analyser.getByteFrequencyData(dataArray);
          
          // Calculate average volume
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const average = sum / bufferLength;
          
          // If we detect significant audio while AI is speaking, trigger barge-in
          // Always log audio levels for debugging  
          console.log('🎤 Audio level:', Math.round(average), '| Voice state:', voiceState, '| Audio:', !!currentAudio, '| Speech:', speechSynthesis.speaking);
          
          // Simple and aggressive - interrupt on ANY sound above 1
          const isAudioPlaying = currentAudio && !currentAudio.paused;
          const isSpeechActive = speechSynthesis.speaking;
          
          // Trigger interruption if there's any AI activity OR just any sound at all
          const shouldDetectBarge = isAudioPlaying || isSpeechActive || voiceState === 'speaking' || true; // Always allow interruption
          
          // EMERGENCY AGGRESSIVE interruption - interrupt on ANY significant sound
          const now = Date.now();
          const timeSinceLastInterruption = now - lastInterruptionTime.current;
          const cooldownPeriod = 500; // Very short cooldown
          
          // ULTRA SIMPLE: If sound is detected and any audio might be playing, INTERRUPT
          if (average > 0.2 && timeSinceLastInterruption > cooldownPeriod && 
              (currentAudio || speechSynthesis.speaking || voiceState === 'speaking')) {
            
            console.log('💥 EMERGENCY INTERRUPT! Audio level:', Math.round(average));
            console.log('🚨 Conditions: Audio=', !!currentAudio, 'Speech=', speechSynthesis.speaking, 'State=', voiceState);
            console.log('� VOICE INTERRUPTION! Level:', Math.round(average));
            console.log('� BARGE-IN DETECTED: Audio level:', average);
            // Set cooldown to prevent rapid re-triggering
            lastInterruptionTime.current = now;
            bargeInDetectedRef.current = true;
            
            // IMMEDIATELY kill all audio to prevent overlap
            killAllAudio();
            stopBargeInDetection();
            

            setVoiceState('listening');
            
            // Wait for audio to fully stop, then capture user's interruption
            setTimeout(async () => {
              try {

                const userInput = await startContinuousListening();
                
                if (userInput && userInput.trim().length > 0) {
                  console.log('✅ Processing interruption:', userInput);
                  setVoiceState('processing');
                  const aiResponse = await getAIResponse(userInput);
                  
                  setVoiceState('speaking');
                  await playAIResponse(aiResponse);
                }
                
                bargeInDetectedRef.current = false;
                setVoiceState('listening');
              } catch (error) {
                console.log('Error processing interruption:', error);
                bargeInDetectedRef.current = false;
                setVoiceState('listening');
              }
            }, 300); // Increased delay to ensure audio stops
            
            return;
          }
          

          
          // Continue monitoring
          requestAnimationFrame(checkAudioLevel);
        };
        
        console.log('🔊 Starting audio level monitoring loop...');
        checkAudioLevel();
        
      })
      .catch(error => {
        console.log('❌ Could not start barge-in detection:', error.message);
        audioMonitoringRef.current = false;
      });
  };

  // Stop barge-in detection
  const stopBargeInDetection = () => {
    console.log('🛑 Stopping barge-in detection');
    audioMonitoringRef.current = false;
    
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
        audioContextRef.current = null;
      } catch (e) {
        console.log('Error closing audio context:', e);
      }
    }
    
    if (microphoneRef.current) {
      try {
        microphoneRef.current.disconnect();
        microphoneRef.current = null;
      } catch (e) {
        console.log('Error disconnecting microphone:', e);
      }
    }
    
    analyserRef.current = null;
  };

  const startContinuousListening = () => {
    return new Promise((resolve, reject) => {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        reject(new Error('Speech recognition not supported'));
        return;
      }

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      // Optimize settings specifically for very long conversational sentences
      recognition.continuous = true; // Allow much longer speech
      recognition.interimResults = true; // Show results as user speaks
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1; // Focus on best result for long speech

      let finalTranscript = '';
      let timeout = setTimeout(() => {
        console.log('⏰ Speech recognition timeout reached');
        recognition.stop();
        if (finalTranscript.trim()) {
          console.log('✅ Using partial transcript:', finalTranscript.trim());
          const processedTranscript = processMathematicalText(finalTranscript.trim());
          setLastRecognizedText(finalTranscript.trim());
          setLastProcessedText(processedTranscript);
          resolve(processedTranscript);
        } else {
          console.log('❌ No speech detected, returning empty string');
          resolve(''); // Return empty string instead of rejecting
        }
      }, 25000); // 25 second timeout for very long conversational sentences

      recognition.onresult = (event) => {
        let interimTranscript = '';
        
        // Process all results
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            console.log('🎤 FINAL SPEECH:', finalTranscript);
            
            // For very long sentences, wait a bit more to ensure completeness
            if (finalTranscript.trim().length > 100) {
              console.log('📝 Very long sentence detected, ensuring completeness...');
              setTimeout(() => {
                clearTimeout(timeout);
                const processedTranscript = processMathematicalText(finalTranscript.trim());
                console.log('🧮 PROCESSED LONG SENTENCE:', processedTranscript);
                setLastRecognizedText(finalTranscript.trim());
                setLastProcessedText(processedTranscript);
                recognition.stop();
                resolve(processedTranscript);
              }, 1000); // Wait 1 second for very long sentences
              return;
            }
            
            // Normal processing for shorter sentences
            clearTimeout(timeout);
            const processedTranscript = processMathematicalText(finalTranscript.trim());
            console.log('🧮 PROCESSED:', processedTranscript);
            setLastRecognizedText(finalTranscript.trim());
            setLastProcessedText(processedTranscript);
            recognition.stop();
            resolve(processedTranscript);
            return;
          } else {
            interimTranscript += transcript;
            console.log('🎤 INTERIM:', interimTranscript.length > 50 ? interimTranscript.substring(0, 50) + '...' : interimTranscript);
            
            // For very long sentences, extend the timeout dynamically
            if (interimTranscript.trim().length > 80) {
              clearTimeout(timeout);
              timeout = setTimeout(() => {
                console.log('⏰ Extended timeout for long sentence');
                recognition.stop();
                if (finalTranscript.trim()) {
                  const processedTranscript = processMathematicalText(finalTranscript.trim());
                  setLastRecognizedText(finalTranscript.trim());
                  setLastProcessedText(processedTranscript);
                  resolve(processedTranscript);
                } else {
                  resolve(interimTranscript.trim());
                }
              }, 30000); // Extra 30 seconds for very long sentences
            }
            
            // Also check for barge-in on interim results for faster response
            if (voiceState === 'speaking' && interimTranscript.trim().length > 2) {
              console.log('🛑 INTERIM BARGE-IN: User interrupting with:', interimTranscript);
              stopCurrentAudio();
            }
          }
        }
      };

      recognition.onerror = (event) => {
        clearTimeout(timeout);
        console.error('Speech recognition error:', event.error);
        
        // Be more forgiving with speech recognition errors
        if (event.error === 'no-speech') {
          console.log('No speech detected - resolving with empty string');
          resolve(''); // Don't reject, just return empty
        } else if (event.error === 'audio-capture') {
          setTimeout(() => {
            console.log('Restarting speech recognition...');
            recognition.start();
          }, 500);
        } else if (event.error === 'network') {
          console.log('Network error - continuing conversation');
          resolve(''); // Don't end conversation on network issues
        } else {
          console.log('Speech recognition error:', event.error, '- continuing anyway');
          resolve(''); // Be forgiving, don't end conversation
        }
      };

      recognition.onstart = () => {
        console.log('🎤 Speech recognition started - speak now!');
      };

      recognition.onend = () => {
        console.log('🎤 Speech recognition ended');
        clearTimeout(timeout);
        
        // If we have some transcript, resolve with it instead of rejecting
        if (finalTranscript.trim()) {
          const processedTranscript = processMathematicalText(finalTranscript.trim());
          setLastRecognizedText(finalTranscript.trim());
          setLastProcessedText(processedTranscript);
          resolve(processedTranscript);
        }
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
      
      // PREVENT OVERLAPPING: Stop any existing audio first
      if (currentAudio || speechSynthesis.speaking) {
        console.log('🛑 Stopping existing audio to prevent overlap');
        killAllAudio();
        await new Promise(resolve => setTimeout(resolve, 100)); // Wait for stop
      }
      
      console.log('🎤 Voice config:', azureSpeechConfig.voiceName);
      console.log('🔑 Has Azure key:', !!azureSpeechConfig.subscriptionKey);
      
      // Set voice state to speaking BEFORE starting audio
      setVoiceState('speaking');
      
      // Reset barge-in flag before starting
      bargeInDetectedRef.current = false;
      
      // Start simplified barge-in detection immediately
      startBargeInDetection();
      
      // Try Azure Speech Service first
      try {
        console.log('🎵 Attempting Azure Speech Service...');
        const response = await fetchWithTimeout(`${azureSpeechConfig.endpoint}cognitiveservices/v1`, {
          method: 'POST',
          headers: {
            'Ocp-Apim-Subscription-Key': azureSpeechConfig.subscriptionKey,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'audio-16khz-64kbitrate-mono-mp3'
          },
          body: `
            <speak version='1.0' xml:lang='en-US'>
              <voice xml:lang='en-US' xml:gender='Female' name='${azureSpeechConfig.voiceName}'>
                <prosody rate='1.0' pitch='medium'>
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
            audio.preload = 'auto'; // Preload for faster playback
            audio.onloadstart = () => { // Start playing as soon as loading begins
              console.log('🎧 Audio loading - starting barge-in detection');
              
              // Ensure barge-in detection is active when audio starts
              if (!audioMonitoringRef.current) {
                startBargeInDetection();
              }
              
              audio.play().then(() => {
                setCurrentAudio(audio);
                console.log('🔊 Azure audio playing - detection active');
              }).catch(() => {
                // Fallback to canplay if immediate play fails
                audio.oncanplay = () => {
                  audio.play().then(() => setCurrentAudio(audio)).catch(reject);
                };
              });
            };
            audio.onended = () => {
              console.log('Audio playback finished');
              URL.revokeObjectURL(audioUrl);
              setCurrentAudio(null);
              // Stop barge-in detection when audio ends
              stopBargeInDetection();
              resolve();
            };
            audio.onerror = (error) => {
              console.error('Audio playback error:', error);
              URL.revokeObjectURL(audioUrl);
              // Stop barge-in detection on error
              stopBargeInDetection();
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
            
            utterance.onstart = () => {
              console.log('🔊 Browser speech started - ensuring barge-in detection');
              
              // Ensure barge-in detection is active for browser speech
              if (!audioMonitoringRef.current) {
                startBargeInDetection();
              }
            };
            
            utterance.onend = () => {
              console.log('Browser speech finished');
              // Stop barge-in detection when speech ends
              stopBargeInDetection();
              resolve();
            };
            utterance.onerror = (error) => {
              console.error('Browser speech error:', error);
              // Stop barge-in detection on error
              stopBargeInDetection();
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
      // Stop barge-in detection on any error
      stopBargeInDetection();
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
        
        // Check if a barge-in was detected
        if (bargeInDetectedRef.current) {
          console.log('Barge-in detected, resetting flag and continuing...');
          bargeInDetectedRef.current = false;
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
        
        // Skip processing if input is empty or just whitespace
        if (!userInput || userInput.trim().length === 0) {
          console.log('Empty input received, continuing conversation...');
          continue; // Skip this turn and continue listening
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
        let aiResponse;
        try {
          aiResponse = await getAIResponse(userInput);
        } catch (error) {
          console.log('Error in getAIResponse, using fallback:', error);
          aiResponse = "I heard what you said and I'd love to continue our conversation. What would you like to talk about next?";
        }
        
        // Speak the response (AI already includes conversation-continuing questions)
        setVoiceState('speaking');
        try {
          await playAIResponse(aiResponse);
        } catch (error) {
          console.log('Error in playAIResponse, continuing conversation:', error);
          // Continue conversation even if audio fails
        }
        
        // Increment turn count
        setTurnCount(prev => prev + 1);
        
        // Minimal pause for immediate conversation flow
        await new Promise(resolve => setTimeout(resolve, 200));
        
      } catch (error) {
        console.log('Conversation error:', error.message);
        
        if (error.message === 'Speech timeout' || error.message === 'Request timeout') {
          // Handle timeout gracefully - continue conversation instead of ending
          console.log('Timeout occurred - continuing conversation');
          await playAIResponse("Sorry, I didn't catch that. Could you try again?");
          continue; // Continue the conversation loop
        } else if (error.message.includes('no-speech') || error.message.includes('audio-capture')) {
          // Audio issues - continue conversation
          console.log('Audio issue - continuing conversation');
          continue;
        } else if (error.message.includes('TypeError') || error.message.includes('Failed to convert')) {
          // Browser compatibility issues - continue conversation
          console.log('Browser compatibility issue - continuing conversation');
          continue;
        } else {
          // Only end conversation on critical errors, but be more forgiving
          console.error('Error occurred but continuing conversation:', error);
          await playAIResponse("Sorry about that technical hiccup. Let's continue our conversation!");
          continue; // Continue instead of ending
        }
      }
    }
    console.log('ConversationLoop ended');
  };

  const getAIResponse = async (question) => {
    try {
      // Handle empty or very short questions
      if (!question || question.trim().length === 0) {
        return "I didn't catch that. Could you try saying that again?";
      }
      
      console.log('🚀 Sending to AI backend:', question);
      console.log('📝 Question type - Conversational?', isConversationalQuery(question));
      console.log('📝 Question type - Mathematical?', isMathematicalQuery(question));
      
      const isConversational = isConversationalQuery(question);
      const smartTimeout = getSmartTimeout(question);
      
      console.log('🚀 Processing question:', question);
      console.log('🔍 Is conversational:', isConversational);
      console.log('⏱️ Timeout set to:', smartTimeout, 'ms');
      console.log('🧠 Conversation history being sent:', conversationHistoryPal.slice(-5));
      console.log('📡 Making request to backend...');
      
      // IMPORTANT: Add question to history BEFORE sending request
      // This ensures the question is preserved even if the response is interrupted
      const tempHistoryEntry = { question: question, answer: '...' };
      setConversationHistoryPal(prev => [...prev, tempHistoryEntry]);
      
      const response = await fetchWithTimeout('http://localhost:8003/ask_question/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: question,
          uploaded_files: [],
          is_first_message: conversationHistoryPal.length === 0,
          is_conversational: isConversational,  // Tell backend the query type
          priority: isConversational ? 'fast' : 'detailed',
          conversation_history: conversationHistoryPal.slice(-5) // Send last 5 exchanges for context
        })
      }, smartTimeout);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📨 Received from AI backend:', data);
      console.log('✅ Request successful - no timeout');
      const aiResponse = data.answer || 'I apologize, but I couldn\'t process that question properly.';
      console.log('🤖 AI Response:', aiResponse);
      
      // Update conversation history with actual response (replace the temporary entry)
      setConversationHistoryPal(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].answer === '...') {
          // Replace the temporary entry with the actual response
          updated[updated.length - 1] = { question: question, answer: aiResponse };
        } else {
          // Fallback: add new entry if temp entry not found
          updated.push({ question: question, answer: aiResponse });
        }
        
        // DEBUG: Log the updated history
        console.log('🧠 Updated conversation history:', updated);
        
        // Persist to localStorage as backup
        try {
          localStorage.setItem('highpal_conversation_history', JSON.stringify(updated.slice(-10)));
        } catch (e) {
          console.log('Could not save to localStorage:', e);
        }
        
        return updated;
      });
      
      return aiResponse;
      
    } catch (error) {
      console.error('AI response error:', error);
      if (error.message === 'Request timeout') {
        return 'That took a bit longer than expected. Let me try to help you quickly!';
      } else if (error.message.includes('TypeError') || error.message.includes('Failed to convert')) {
        return 'I heard what you said about your plans - that sounds interesting! Tell me more.';
      } else {
        return 'I\'m having trouble processing that right now, but I\'d love to continue our conversation. What else is on your mind?';
      }
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

        const response = await fetch('http://localhost:8003/upload', {
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
    <div style={{ minHeight: '100vh', width: '100vw', background: 'radial-gradient(circle at 10% 10%, #f6f8fc 0%, #fff 100%)', display: 'flex', fontFamily: 'Inter, Arial, Helvetica, sans-serif', position: 'relative' }}>
      
      {/* Talks Sidebar */}
      <div style={{ width: '300px', background: 'rgba(255,255,255,0.95)', borderRight: '1px solid #e1e5e9', height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Sidebar Header */}
        <div style={{ padding: '20px', borderBottom: '1px solid #e1e5e9' }}>
          <h2 style={{ margin: '0', fontSize: '1.5rem', color: '#181c2a', fontWeight: '700' }}>Talks</h2>
          <button 
            onClick={startNewChat}
            style={{
              marginTop: '12px',
              width: '100%',
              padding: '12px 16px',
              background: 'linear-gradient(135deg, #7c4afd, #a084fa)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              boxShadow: '0 2px 8px rgba(124, 74, 253, 0.3)',
              transition: 'all 0.2s ease'
            }}
          >
            + New Chat
          </button>
        </div>
        
        {/* Talks List */}
        <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
          {savedTalks.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: '#666', fontSize: '0.9rem' }}>
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>💬</div>
              No conversations yet.<br/>Start chatting to create your first talk!
            </div>
          ) : (
            savedTalks.map((talk) => (
              <div 
                key={talk.id}
                onClick={() => loadTalk(talk)}
                style={{
                  padding: '12px',
                  margin: '4px 0',
                  background: currentTalkId === talk.id ? '#f0f0ff' : 'white',
                  border: currentTalkId === talk.id ? '2px solid #7c4afd' : '1px solid #e1e5e9',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                }}
                onMouseEnter={(e) => {
                  if (currentTalkId !== talk.id) {
                    e.target.style.background = '#f8f9fa';
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentTalkId !== talk.id) {
                    e.target.style.background = 'white';
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#181c2a', marginBottom: '4px', lineHeight: '1.3' }}>
                      {talk.title}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#666', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>{talk.mode === 'pal' ? '🎓' : '📚'}</span>
                      <span>{new Date(talk.lastModified).toLocaleDateString()}</span>
                      <span>•</span>
                      <span>{talk.history.length} messages</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteTalk(talk.id);
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#999',
                      cursor: 'pointer',
                      padding: '6px',
                      borderRadius: '6px',
                      marginLeft: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '28px',
                      height: '28px',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.color = '#dc3545';
                      e.target.style.background = '#ffebee';
                      e.target.style.transform = 'scale(1.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.color = '#999';
                      e.target.style.background = 'none';
                      e.target.style.transform = 'scale(1)';
                    }}
                    title="Delete conversation"
                  >
                    <svg 
                      width="14" 
                      height="14" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      stroke="currentColor" 
                      strokeWidth="2" 
                      strokeLinecap="round" 
                      strokeLinejoin="round"
                    >
                      <polyline points="3,6 5,6 21,6"></polyline>
                      <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
                      <line x1="10" y1="11" x2="10" y2="17"></line>
                      <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingTop: '40px', position: 'relative' }}>
      


      
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
      
      </div> {/* Close Main Content Area */}
      
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
