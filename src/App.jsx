import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { BASE_WAKE_WORDS, POTENTIAL_WAKE_REGEX, normalizeTranscript, mergeBigrams, detectWake, suppressIfAIMatch } from './wakeDetection.js';
import './App.css';
import RevisionMode from './components/RevisionMode';

// VAD System imports (Sesame.com style - no wake words needed)
import VADDetector from './services/vadDetector';
import AzureStreamingClient from './services/azureStreamingClient';
import InterruptManager from './services/interruptManager';

const describeVADDisableReason = (code) => {
  switch (code) {
    case 'window-unavailable':
      return 'window object not available (likely server-side render)';
    case 'secure-context-required':
      return 'browser must run in a secure context (https:// or localhost)';
    case 'media-devices-unavailable':
      return 'navigator.mediaDevices.getUserMedia is unavailable';
    case 'web-audio-unavailable':
      return 'Web Audio API is not supported in this browser';
    case 'audio-worklet-unavailable':
      return 'AudioWorkletNode is not supported (required by VAD)';
    case 'env-pref-disabled':
      return 'disabled via VITE_ENABLE_VAD=false';
    case 'init-failed':
      return 'initialization failure (check console for details)';
    case null:
    case undefined:
      return 'no disable reason recorded';
    default:
      return code;
  }
};

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
  
  // Voice conversation history (separate from chat to prevent interference)
  const [voiceConversationHistory, setVoiceConversationHistory] = useState([]);
  // Refs to always have latest histories (avoid stale closures in async loops)
  const voiceHistoryRef = useRef([]);
  const chatHistoryRef = useRef([]);
  
  const [showConversation, setShowConversation] = useState(false);
  
  // Saved conversations (talks) state - initialize with stored talks
  const [savedTalks, setSavedTalks] = useState(() => {
    try {
      const stored = localStorage.getItem('highpal_saved_talks');
      if (!stored) return [];
      
      const talks = JSON.parse(stored);
      
      // Simple duplicate removal to prevent excessive processing
      const uniqueTalks = talks.filter((talk, index, self) => 
        index === self.findIndex(t => t.id === talk.id)
      );
      
      // Only save back if there were duplicates (avoid unnecessary writes)
      if (uniqueTalks.length !== talks.length) {
        setTimeout(() => {
          localStorage.setItem('highpal_saved_talks', JSON.stringify(uniqueTalks));
        }, 0);
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
  const voiceStateRef = useRef('idle');
  useEffect(() => { voiceStateRef.current = voiceState; }, [voiceState]);
  
  // Wake word interrupt system (only for interrupting AI speech)
  const [isPassiveListening, setIsPassiveListening] = useState(false);
  const [isProcessingInterrupt, setIsProcessingInterrupt] = useState(false);
  const passiveRecognitionRef = useRef(null);
  const lastInterruptTime = useRef(0);
  
  // Prevent multiple AI instances speaking simultaneously
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const aiSpeakingRef = useRef(false);
  const welcomePlayedRef = useRef(false); // prevent duplicate welcome playback
  const [audioRef, setAudioRef] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  // Global stop flag to immediately halt ongoing/queued speech
  const stopRequestedRef = useRef(false);
  // Track current AI spoken text to reduce self-trigger (wake word detected from AI's own speech leaking into mic)
  const currentAIAudioTextRef = useRef('');
  const aiSpeechStartTimeRef = useRef(0);
  // Configurable delay between AI speech end and starting active listening (ms)
  const ACTIVE_LISTEN_DELAY_MS = 80; // tuned low for responsiveness
  // Simple earcon utility (short beep) when entering active listening
  const playEarcon = useCallback(() => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1040, ctx.currentTime);
      gain.gain.setValueAtTime(0.0001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + 0.005);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.18);
      osc.connect(gain); gain.connect(ctx.destination);
      osc.start(); osc.stop(ctx.currentTime + 0.2);
    } catch (e) {
      console.log('Earcon failed:', e?.message || e);
    }
  }, []);
  
  // Debug logging control for development
  const [isDebugLoggingEnabled, setIsDebugLoggingEnabled] = useState(true);
  
  // Function to stop debug logging (called when END button is clicked)
  const stopDebugLogging = () => {
    setIsDebugLoggingEnabled(false);
    console.log('🔇 Debug logging DISABLED - END button clicked');
  };
  
  // Function to enable debug logging (for testing)
  const enableDebugLogging = () => {
    setIsDebugLoggingEnabled(true);
    console.log('🔊 Debug logging ENABLED');
  };
  
  const PASSIVE_LOG_ICON = '🎧';
  const ACTIVE_LOG_ICON = '🎙️';

  // Passive listening status helper
  const logPassiveListeningStatus = (context) => {
    console.log(`${PASSIVE_LOG_ICON} 📊 PASSIVE LISTENING STATUS [${context}]:`, {
      active: isPassiveListening,
      hasRecognition: !!passiveRecognitionRef.current,
      conversationActive: isConversationActive,
      voiceState: voiceState,
      aiSpeaking: aiSpeakingRef.current,
      processingInterrupt: isProcessingInterrupt
    });
  };
  
  // Voice conversation history debug helper
  const debugVoiceHistory = (context) => {
    console.log(`🧠 VOICE HISTORY DEBUG [${context}]:`, {
      historyLength: voiceConversationHistory.length,
      lastFewEntries: voiceConversationHistory.slice(-3),
      conversationActive: isConversationActive,
      turnCount: turnCount
    });
  };
  
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
  // Recognition confidence score for quality feedback
  const [recognitionConfidence, setRecognitionConfidence] = useState(1.0);
  // Speech recognition locale/accent selection
  const [speechLocale, setSpeechLocale] = useState(() => {
    try {
      return localStorage.getItem('highpal_speech_locale') || 'en-IN';
    } catch {
      return 'en-IN';
    }
  });
  
  // Locale options with flags
  const SPEECH_LOCALE_OPTIONS = [
    { value: 'en-IN', label: 'English (India)', flag: '🇮🇳' },
    { value: 'en-US', label: 'English (US)', flag: '🇺🇸' },
    { value: 'en-GB', label: 'English (UK)', flag: '🇬🇧' },
    { value: 'en-AU', label: 'English (Australia)', flag: '🇦🇺' },
    { value: 'en-CA', label: 'English (Canada)', flag: '🇨🇦' },
    { value: 'en-NZ', label: 'English (New Zealand)', flag: '🇳🇿' },
  ];
  
  // Save locale preference
  useEffect(() => {
    try {
      localStorage.setItem('highpal_speech_locale', speechLocale);
    } catch (e) {
      console.log('Could not save locale preference:', e);
    }
  }, [speechLocale]);
  
  // Watchdog timer to ensure passive listening remains active
  const interruptWatchdogRef = useRef(null);
  // Track when active user recognition (foreground STT) is running to avoid conflicts with passive wake-word
  const activeUserRecognitionRef = useRef(false);
  
  // VAD System refs (Sesame.com style - natural speech detection)
  const vadCapability = useMemo(() => {
    if (typeof window === 'undefined') {
      return { supported: false, reason: 'window-unavailable' };
    }

    const secure = window.isSecureContext;
    const hasNavigator = typeof navigator !== 'undefined';
    const hasMediaDevices = hasNavigator && !!navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function';
    const hasAudioContext = !!(window.AudioContext || window.webkitAudioContext);
    const hasWorklet = typeof window.AudioWorkletNode !== 'undefined';

    if (!secure) return { supported: false, reason: 'secure-context-required' };
    if (!hasMediaDevices) return { supported: false, reason: 'media-devices-unavailable' };
    if (!hasAudioContext) return { supported: false, reason: 'web-audio-unavailable' };
    if (!hasWorklet) return { supported: false, reason: 'audio-worklet-unavailable' };

    return { supported: true, reason: null };
  }, []);

  const vadEnvPreference = import.meta.env.VITE_ENABLE_VAD;
  const envAllowsVAD = vadEnvPreference ? vadEnvPreference === 'true' : true;
  const initialVADEnabled = envAllowsVAD && vadCapability.supported;
  const initialVADDisableReason = initialVADEnabled ? null : (envAllowsVAD ? vadCapability.reason : 'env-pref-disabled');

  const vadDetectorRef = useRef(null);
  const azureStreamingRef = useRef(null);
  const interruptManagerRef = useRef(null);
  const vadEnabledRef = useRef(initialVADEnabled);
  const vadDisabledReasonRef = useRef(initialVADDisableReason);
  const vadInitializedRef = useRef(false);
  const deferPassiveWakeStartRef = useRef(false); // Defer passive wake until after first user turn

  // Keep refs in sync with state to avoid stale closures inside async flows
  useEffect(() => {
    voiceHistoryRef.current = voiceConversationHistory;
  }, [voiceConversationHistory]);
  useEffect(() => {
    chatHistoryRef.current = conversationHistoryPal;
  }, [conversationHistoryPal]);
  
  // Session-specific uploaded files for current conversation
  const [sessionUploadedFiles, setSessionUploadedFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(''); // 'uploading', 'success', 'error'

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

  // Save current conversation as a talk (memoized to prevent unnecessary re-renders)
  const saveCurrentTalk = useCallback(() => {
    const currentHistory = chatMode === 'pal' ? conversationHistoryPal : conversationHistoryBook;
    if (currentHistory.length === 0) return;

    const talkId = currentTalkId || Date.now().toString();
    
    setSavedTalks(prevSavedTalks => {
      // Check if this conversation already exists and is identical
      const existingTalk = prevSavedTalks.find(talk => talk.id === talkId);
      if (existingTalk && JSON.stringify(existingTalk.history) === JSON.stringify(currentHistory)) {
        // No changes, don't save
        return prevSavedTalks;
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

      const updatedTalks = prevSavedTalks.filter(talk => talk.id !== talkId);
      updatedTalks.unshift(newTalk);
      
      // Save to localStorage
      saveTalksToStorage(updatedTalks);
      
      return updatedTalks;
    });
    
    setCurrentTalkId(talkId);
  }, [chatMode, conversationHistoryPal, conversationHistoryBook, currentTalkId]);

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

  // Expose wake word debug helpers for troubleshooting
  useEffect(() => {
    window.highpalWakeDebug = {
      enable: enableDebugLogging,
      disable: stopDebugLogging,
      restartPassive: () => safeRestartInterruptListening(0),
      killAllAudio: killAllAudio,
      state: () => ({
        aiSpeaking: aiSpeakingRef.current,
        passiveActive: !!passiveRecognitionRef.current,
        voiceState,
        conversationActive: isConversationActive,
        isProcessingInterrupt,
      }),
      vadStatus: () => ({
        supported: vadCapability.supported,
        enabled: vadEnabledRef.current,
        initialized: vadInitializedRef.current,
        reason: vadEnabledRef.current ? null : (vadDisabledReasonRef.current || vadCapability.reason)
      })
    };
    console.log('🛠️ HighPal Wake Debug available at window.highpalWakeDebug');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (vadEnabledRef.current) {
      console.log('🟢 Natural over-talk detection (VAD) enabled by default');
    } else {
      const reason = describeVADDisableReason(vadDisabledReasonRef.current);
      console.log('⚠️ Natural over-talk detection (VAD) disabled:', reason);
    }
  }, []);

  // Auto-save current conversation when it changes (but not on initial load)
  useEffect(() => {
    if (!isInitialLoad && conversationHistoryPal.length > 0 && chatMode === 'pal') {
      const timeoutId = setTimeout(() => saveCurrentTalk(), 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [conversationHistoryPal, isInitialLoad, chatMode, saveCurrentTalk]);

  useEffect(() => {
    if (!isInitialLoad && conversationHistoryBook.length > 0 && chatMode === 'book') {
      const timeoutId = setTimeout(() => saveCurrentTalk(), 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [conversationHistoryBook, isInitialLoad, chatMode, saveCurrentTalk]);

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
    
    // Add keyboard shortcut for testing wake word detection
    const handleKeyPress = (event) => {
      // Press 'P' key to simulate "Pal" wake word
      if (event.key.toLowerCase() === 'p' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        console.log('🔥 KEYBOARD WAKE WORD TRIGGERED! (Ctrl+P)');
        if (aiSpeakingRef.current || voiceState === 'speaking') {
          handleInterrupt('pal test command');
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyPress);
    
    // Log improvements loaded
    console.log('🚀 WAKE WORD IMPROVEMENTS LOADED:');
    console.log('   • Multiple wake word variations: pal, paul, pel, pow, pol, pail, pale');
    console.log('   • Interim results enabled for faster detection');
    console.log('   • Keyboard shortcut: Ctrl+P to test interrupt');
    console.log('   • Enhanced audio stopping with multiple attempts');
    
    // Cleanup on unmount
    return () => {
      document.removeEventListener('keydown', handleKeyPress);
      
      // Cleanup VAD system if active
      if (vadEnabledRef.current && vadInitializedRef.current) {
        cleanupVADSystem();
      }
    };
  }, []);

  // Note: Wake word detection ("Pal") has replaced keyboard interrupts
  // Passive listening is always active during voice conversations

  // Azure Speech Service configuration from environment variables (memoized to prevent re-creation)
  const azureSpeechConfig = useMemo(() => ({
    subscriptionKey: import.meta.env.VITE_AZURE_SPEECH_KEY,
    region: import.meta.env.VITE_AZURE_SPEECH_REGION || "centralindia",
    voiceName: "en-US-AriaNeural", // Force AriaNeural voice
    endpoint: `https://${import.meta.env.VITE_AZURE_SPEECH_REGION || "centralindia"}.tts.speech.microsoft.com/`
  }), []);

  // Debug logging for voice configuration (only once)
  useEffect(() => {
    if (isDebugLoggingEnabled) console.log('🎤 Azure Speech Config:', {
      region: azureSpeechConfig.region,
      voiceName: azureSpeechConfig.voiceName,
      endpoint: azureSpeechConfig.endpoint,
      hasKey: !!azureSpeechConfig.subscriptionKey
    });
  }, [azureSpeechConfig]);

  // Utility function for requests with timeout
  const fetchWithTimeout = (url, options, timeout = 12000) => { // Increased from 4000 to 12000ms for better context processing
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
      if (isDebugLoggingEnabled) console.log('💬 Conversational query detected - using enhanced timeout for better context');
      return 10000; // Increased from 3000 to 10000ms (10 seconds) for enhanced context processing
    } else {
      if (isDebugLoggingEnabled) console.log('🎓 Educational query detected - using extended timeout');
      return 15000; // Increased from 5000 to 15000ms (15 seconds) for complex educational queries
    }
  };

  const processMathematicalText = (text) => {
  if (isDebugLoggingEnabled) console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Original speech input:`, text);
    
    // Don't process conversational text mathematically
    if (isConversationalQuery(text)) {
      if (isDebugLoggingEnabled) console.log('✅ Detected as conversational, keeping original:', text);
      return text;
    }

    // Only apply mathematical processing if it seems like a math question
    if (!isMathematicalQuery(text)) {
      if (isDebugLoggingEnabled) console.log('✅ Not mathematical, keeping original:', text);
      return text;
    }

    if (isDebugLoggingEnabled) console.log('🧮 Applying mathematical processing to:', text);

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
        if (isDebugLoggingEnabled) console.log('✅ Nuclear stopped Azure audio');
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
      if (isDebugLoggingEnabled) console.log('✅ Nuclear stopped speech synthesis');
    } catch (e) {
      if (isDebugLoggingEnabled) console.log('Error in nuclear speech stop:', e);
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
        if (isDebugLoggingEnabled) console.log('Attempting Web Audio API suspension');
      }
    } catch (e) {
      if (isDebugLoggingEnabled) console.log('No Web Audio to stop');
    }
    
    // CRITICAL: Unlock AI speech when force-stopping audio
    if (isDebugLoggingEnabled) console.log('🔓 FORCE UNLOCKING AI speech due to killAllAudio');
    aiSpeakingRef.current = false;
    setIsAISpeaking(false);
    if (isDebugLoggingEnabled) console.log('🔓 Force unlock - AI speaking state set to:', aiSpeakingRef.current);
  };

  // Enhanced audio stopping functionality
  const stopCurrentAudio = () => {
    if (isDebugLoggingEnabled) console.log('🛑 FORCE STOPPING all audio due to barge-in');
    
    // Use nuclear option first
    killAllAudio();
    
    // Immediately switch to listening state after interruption
    setVoiceState('listening');
  if (isDebugLoggingEnabled) console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Voice state set to listening after barge-in`);
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
    // CRITICAL: Don't start if AI is speaking to prevent feedback loop
    if (aiSpeakingRef.current) {
      console.log('🛡️ Skipping barge-in start - AI is currently speaking');
      return;
    }
    
    if (audioMonitoringRef.current) {
      if (isDebugLoggingEnabled) console.log('Barge-in detection already running');
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
            if (isDebugLoggingEnabled) console.log('⏹️ Audio monitoring stopped');
            return;
          }
          
          // CRITICAL: Skip monitoring completely if AI is speaking to prevent feedback loop
          if (aiSpeakingRef.current) {
            requestAnimationFrame(checkAudioLevel);
            return;
          }
          
          // SIMPLIFIED: Only pause detection if explicitly in listening mode with no audio
          const currentVoiceState = voiceStateRef.current;
          if (currentVoiceState === 'listening' && !currentAudio && !speechSynthesis.speaking) {
            // Still monitor but don't interrupt during user speech
            requestAnimationFrame(checkAudioLevel);
            return;
          }
          
          if (isDebugLoggingEnabled) console.log('🔊 Current voice state:', currentVoiceState);
          
          analyser.getByteFrequencyData(dataArray);
          
          // Calculate average volume
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const average = sum / bufferLength;
          
          // If we detect significant audio while AI is speaking, trigger barge-in
          // Always log audio levels for debugging  
          // Audio level debug log removed per request
          
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
      // Use higher threshold for first 2s of AI speech to avoid immediate false barge-in
      const elapsedSinceAISTart = Date.now() - aiSpeechStartTimeRef.current;
      // Higher initial threshold, tapering down more gradually to reduce false self-interrupts
      const dynamicThreshold = elapsedSinceAISTart < 1500 ? 12 : elapsedSinceAISTart < 3500 ? 6 : 2.2;
      // Maintain a rolling window of recent averages to require sustained sound
      if (!window.__hpRecentLevels) window.__hpRecentLevels = [];
      window.__hpRecentLevels.push(average);
      if (window.__hpRecentLevels.length > 12) window.__hpRecentLevels.shift();
      const sustained = window.__hpRecentLevels.filter(v => v > dynamicThreshold).length >= 4; // need at least 4 frames over threshold
      // CRITICAL: Never trigger if AI speaking ref is true (prevents feedback loop)
      if (aiSpeakingRef.current) {
        requestAnimationFrame(checkAudioLevel);
        return;
      }
      
      // Guard: do not barge-in if ONLY AI audio is playing and no mic user speech (heuristic: average below 18 while AI playing is likely TTS energy bleed)
      const aiOnly = (currentAudio || speechSynthesis.speaking) && currentVoiceState === 'speaking' && average < 18;
      const triggered = !aiOnly && sustained && timeSinceLastInterruption > cooldownPeriod && (currentAudio || speechSynthesis.speaking || currentVoiceState === 'speaking');
      if (!triggered && aiOnly && isDebugLoggingEnabled && sustained) {
        console.log('🛡️ Suppressed self barge-in (AI-only audio) avg=', average.toFixed(2), 'threshold=', dynamicThreshold);
      }
      if (triggered) {
            
            // EMERGENCY INTERRUPT log simplified (removed audio level detail)
            if (isDebugLoggingEnabled) console.log('💥 EMERGENCY INTERRUPT triggered');
            if (isDebugLoggingEnabled) console.log('🚨 Conditions: Audio=', !!currentAudio, 'Speech=', speechSynthesis.speaking, 'State=', currentVoiceState, 'Avg=', average.toFixed(2), 'Threshold=', dynamicThreshold);
            console.log('� VOICE INTERRUPTION detected');
            console.log('� BARGE-IN DETECTED');
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
        
        if (isDebugLoggingEnabled) console.log('🔊 Starting audio level monitoring loop...');
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
      recognition.lang = speechLocale; // Use user-selected locale
      recognition.maxAlternatives = 1; // Focus on best result for long speech

      let finalTranscript = '';
      let timeout = setTimeout(() => {
        if (isDebugLoggingEnabled) console.log('⏰ Speech recognition timeout reached');
        recognition.stop();
        if (finalTranscript.trim()) {
          console.log('✅ Using partial transcript:', finalTranscript.trim());
          const processedTranscript = processMathematicalText(finalTranscript.trim());
          setLastRecognizedText(finalTranscript.trim());
          setLastProcessedText(processedTranscript);
          resolve(processedTranscript);
        } else {
          if (isDebugLoggingEnabled) console.log('❌ No speech detected, returning empty string');
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
            if (isDebugLoggingEnabled) console.log(`${ACTIVE_LOG_ICON} [ACTIVE] FINAL SPEECH:`, finalTranscript);
            
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
            
            // Validate processed transcript
            if (!processedTranscript || processedTranscript.trim().length === 0) {
              console.warn('🚨 Empty processed transcript, using fallback');
              resolve("Could you please repeat that? I didn't catch what you said clearly.");
              return;
            }
            
            // Check for garbled speech patterns
            const cleanTranscript = processedTranscript.trim();
            if (cleanTranscript.length < 2 || /^[^a-zA-Z]*$/.test(cleanTranscript)) {
              console.warn('🚨 Possibly garbled speech:', cleanTranscript);
              resolve("I didn't understand that clearly. Could you please try again?");
              return;
            }
            
            console.log('🧮 PROCESSED:', processedTranscript);
            setLastRecognizedText(finalTranscript.trim());
            setLastProcessedText(processedTranscript);
            recognition.stop();
            resolve(processedTranscript);
            return;
          } else {
            interimTranscript += transcript;
            console.log(`${ACTIVE_LOG_ICON} [ACTIVE] INTERIM:`, interimTranscript.length > 50 ? interimTranscript.substring(0, 50) + '...' : interimTranscript);
            
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
            if (voiceStateRef.current === 'speaking' && interimTranscript.trim().length > 2) {
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
  if (isDebugLoggingEnabled) console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Speech recognition started - speak now!`);
      };

      recognition.onend = () => {
  console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Speech recognition ended`);
        clearTimeout(timeout);
        // Mark foreground recognition as no longer active
        activeUserRecognitionRef.current = false;
        // Proactively restart passive listening shortly after active listen ends
        // so wake-word is available while we process/speak next response.
        safeRestartInterruptListening(150);
        
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
        // Foreground recognition about to start
        activeUserRecognitionRef.current = true;
        recognition.start();
      } catch (error) {
        reject(new Error(`Failed to start recognition: ${error.message}`));
      }
    });
  };

  /**
   * Initialize VAD system (Sesame.com style - no wake words)
   */
  const initializeVADSystem = async () => {
    try {
      console.log('🎯 Initializing VAD system (Sesame.com style - no wake words)...');
      
      if (vadInitializedRef.current) {
        console.log('✅ VAD already initialized');
        return true;
      }
      
      // 1. Create Interrupt Manager
      const interruptManager = new InterruptManager();
      interruptManagerRef.current = interruptManager;
      
      // State change callback
      interruptManager.onStateChange = (newState, oldState) => {
        console.log(`📊 VAD State: ${oldState} → ${newState}`);
        
        // Update UI state
        if (newState === 'USER_SPEAKING') {
          setVoiceState('listening');
        } else if (newState === 'PROCESSING') {
          setVoiceState('processing');
        } else if (newState === 'AI_SPEAKING') {
          setVoiceState('speaking');
        } else if (newState === 'IDLE') {
          setVoiceState('idle');
        }
      };
      
      // 2. Initialize Azure Streaming Client
      const azureStreaming = new AzureStreamingClient();
      const azureInitialized = await azureStreaming.initialize(
        azureSpeechConfig.subscriptionKey,
        azureSpeechConfig.region,
        speechLocale
      );
      
      if (!azureInitialized) {
        throw new Error('Azure Streaming initialization failed');
      }
      azureStreamingRef.current = azureStreaming;
      
      // Setup Azure callbacks
      azureStreaming.onInterimTranscript = (text) => {
        console.log('📝 VAD Interim:', text);
        setLastRecognizedText(text);
      };
      
      azureStreaming.onFinalTranscript = async (text, confidence = 1.0) => {
        console.log('✅ VAD Final transcript:', text);
        
        // CRITICAL: Ignore all transcripts if conversation is not active
        if (!conversationActiveRef.current) {
          console.log('⚠️ Conversation ended - ignoring transcript:', text);
          return;
        }
        
        // Update confidence indicator
        setRecognitionConfidence(confidence);
        
        if (!text || text.trim().length === 0) {
          console.log('⚠️ Empty transcript, ignoring');
          return;
        }
        
        // Check if we're in a state that should process speech
        const currentState = interruptManagerRef.current?.getState();
        
        // Allow processing if:
        // 1. State is USER_SPEAKING or PROCESSING (normal flow)
        // 2. State is IDLE and we have a real transcript (VAD may have been too strict)
        if (currentState === 'AI_SPEAKING') {
          console.log('⚠️ Ignoring transcript - AI is currently speaking:', currentState);
          return;
        }
        
        // ENHANCED ECHO DETECTION: Check if transcript matches AI's recent speech
        if (currentAIAudioTextRef.current) {
          const normalizedTranscript = text.trim().toLowerCase();
          const aiText = currentAIAudioTextRef.current.toLowerCase();
          
          // Check for ANY overlap with AI speech (even partial matches)
          const transcriptWords = normalizedTranscript.split(/\s+/);
          const aiWords = aiText.split(/\s+/);
          
          // If 70% or more words match AI speech, it's likely echo
          let matchCount = 0;
          for (const word of transcriptWords) {
            if (word.length > 3 && aiWords.includes(word)) {
              matchCount++;
            }
          }
          const matchRatio = transcriptWords.length > 0 ? matchCount / transcriptWords.length : 0;
          
          if (matchRatio >= 0.7) {
            console.log('🛡️ VAD: Echo detected -', Math.round(matchRatio * 100) + '% word match with AI speech');
            console.log('🛡️ Transcript:', normalizedTranscript.substring(0, 50));
            console.log('🛡️ AI speech:', aiText.substring(0, 50));
            return;
          }
        }
        
        // If IDLE, trigger VAD speech detection manually (catch missed detections)
        if (currentState === 'IDLE') {
          console.log('🎯 IDLE state with transcript - triggering speech detection');
          interruptManagerRef.current?.handleSpeechDetected();
        }
        
        // Process user speech
        const processedText = processMathematicalText(text.trim());
        setLastRecognizedText(text.trim());
        setLastProcessedText(processedText);
        
        if (aiSpeakingRef.current && currentAIAudioTextRef.current) {
          const normalizedTranscript = processedText.toLowerCase();
          const aiText = currentAIAudioTextRef.current;
          const isLikelySelfSpeech = normalizedTranscript.length >= 12 && aiText.includes(normalizedTranscript);
          if (isLikelySelfSpeech) {
            if (isDebugLoggingEnabled) {
              console.log('🛡️ VAD: Ignoring transcript matching current AI speech to prevent self-listening');
            }
            interruptManagerRef.current?.setIdle();
            return;
          }
        }

        interruptManagerRef.current?.setProcessing();
        
        try {
          // Get AI response (voice pathway keeps history separate)
          const aiResponse = await getVoiceAIResponse(processedText);
          
          if (aiResponse && aiResponse.trim().length > 0) {
            await playAIResponse(aiResponse);
          }
          
        } catch (error) {
          console.error('❌ Error processing VAD input:', error);
          setVoiceConversationHistory(prev => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            if (lastIndex >= 0 && updated[lastIndex].answer === '...') {
              updated[lastIndex].answer = "Sorry, I ran into an issue, but I'm ready whenever you are.";
            }
            const trimmed = updated.slice(-10);
            voiceHistoryRef.current = trimmed;
            return trimmed;
          });
        } finally {
          // Back to idle
          interruptManagerRef.current?.setIdle();
        }
      };
      
      azureStreaming.onError = (error) => {
        console.error('❌ Azure streaming error:', error);
        interruptManagerRef.current?.setIdle();
      };
      
      // 3. Initialize VAD Detector
      const vad = new VADDetector();
      vad.setSpeechStartGuard(() => {
        console.log('🛡️ VAD GUARD CALLED - AI speaking:', aiSpeakingRef.current);
        
        if (!aiSpeakingRef.current) {
          console.log('✅ VAD guard: AI not speaking, allowing detection');
          return true; // AI not speaking, allow all detections
        }

        // AI is speaking - require STRONG evidence of real user speech
        if (typeof window === 'undefined') {
          console.log('🛡️ VAD guard: Window undefined, blocking');
          return false;
        }

        const recentLevels = Array.isArray(window.__hpRecentLevels)
          ? window.__hpRecentLevels
          : [];

        const elapsedSinceAIAudio = Date.now() - (aiSpeechStartTimeRef.current || 0);
        
        console.log('🛡️ VAD guard check:', {
          elapsed: elapsedSinceAIAudio + 'ms',
          recentLevels: recentLevels.length,
          levels: recentLevels
        });

        // Block all detections in first 2 seconds of AI speech (definitely echo)
        if (elapsedSinceAIAudio < 2000) {
          console.log('🛡️ VAD guard: Blocking first 2s of AI speech (echo protection)');
          return false;
        }

        // Without mic level data, require 8 seconds before allowing (very conservative echo protection)
        if (!recentLevels.length) {
          if (elapsedSinceAIAudio < 8000) {
            console.log('🛡️ VAD guard: No mic levels, blocking first 8s (echo protection)');
            return false;
          }
          console.log('✅ VAD guard: >8s elapsed without mic data, allowing (user likely interrupting)');
          return true;
        }

        // Between 2s-8s with mic levels: require VERY strong sustained input OR 5s elapsed
        // After 5 seconds with mic data, even weak signals likely indicate real speech
        if (elapsedSinceAIAudio > 5000) {
          console.log('✅ VAD guard: >5s elapsed with mic data, allowing (user likely interrupting)');
          return true;
        }

        // Before 3s: require VERY strong sustained input to interrupt (prevents echo)
        const veryStrongSamples = recentLevels.filter(value => value >= 35).length;
        const sustained = veryStrongSamples >= 5;
        
        console.log('🛡️ VAD guard strength check:', {
          strongSamples: veryStrongSamples,
          required: 5,
          sustained
        });

        if (!sustained) {
          console.log('🛡️ VAD guard: Suppressing - insufficient sustained strong input');
          return false;
        }

        console.log('✅ VAD guard: Strong sustained input detected - allowing interrupt');
        return true;
      });
      const vadInitialized = await vad.initialize();
      
      if (!vadInitialized) {
        throw new Error('VAD initialization failed');
      }
      vadDetectorRef.current = vad;
      
      // 4. Connect VAD to system
      vad.onSpeechStart = () => {
  console.log(`${ACTIVE_LOG_ICON} [ACTIVE] VAD: User started speaking`);
        
        // Handle based on current state
        const currentState = interruptManagerRef.current?.getState();
        
        if (currentState === 'AI_SPEAKING') {
          // User is interrupting AI
          console.log('⚡ VAD: User interrupting AI!');
          interruptManagerRef.current?.handleSpeechDetected();
          killAllAudio(); // Stop AI immediately
        } else {
          // User started speaking normally
          interruptManagerRef.current?.handleSpeechDetected();
        }
        
        // Azure is already streaming, no need to start it
      };
      
      vad.onSpeechEnd = (audioData) => {
        console.log('🔇 VAD: User stopped speaking');
        
        // Signal that user stopped speaking
        interruptManagerRef.current?.handleSpeechEnded();
        
        // Don't stop Azure - keep it running continuously
      };
      
      // 5. Start VAD
      vad.start();
      
      // 6. Start Azure continuous streaming (always ready to capture speech)
      console.log('🎙️ Starting continuous Azure streaming (always ready)');
      azureStreamingRef.current?.startStreaming();
      
      vadInitializedRef.current = true;
      
      console.log('✅ VAD system initialized!');
      console.log('💬 You can now speak naturally - no wake words needed!');
      console.log('⚡ Just talk to interrupt AI anytime');
      
      return true;
      
    } catch (error) {
      console.error('❌ VAD system initialization failed:', error);
      console.log('⚠️ Falling back to wake-word system');
      vadInitializedRef.current = false;
      return false;
    }
  };

  /**
   * Cleanup VAD system
   */
  const cleanupVADSystem = () => {
    console.log('🧹 Cleaning up VAD system...');
    
    // CRITICAL: Destroy Azure streaming FIRST to prevent late transcripts
    if (azureStreamingRef.current) {
      azureStreamingRef.current.destroy();
      azureStreamingRef.current = null;
    }
    
    // Then destroy VAD detector
    if (vadDetectorRef.current) {
      vadDetectorRef.current.destroy();
      vadDetectorRef.current = null;
    }
    
    // Finally destroy interrupt manager
    if (interruptManagerRef.current) {
      interruptManagerRef.current.destroy();
      interruptManagerRef.current = null;
    }
    
    vadInitializedRef.current = false;
    
    console.log('✅ VAD system cleaned up');
  };

  const endConversation = () => {
    if (isDebugLoggingEnabled) console.log('Ending conversation');
    debugVoiceHistory('BEFORE_END_CONVERSATION');
    console.log('🧠 PRESERVING voice conversation history with', voiceConversationHistory.length, 'entries');
    
    // Cleanup VAD if active
    if (vadEnabledRef.current && vadInitializedRef.current) {
      cleanupVADSystem();
    }
    // Signal all speech/playback to stop immediately
    stopRequestedRef.current = true;
    
    // First, ensure all audio is stopped
    killAllAudio();
    
    // Stop interrupt listening
  console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 📴 ENDING conversation - stopping passive listening`);
    stopInterruptListening();
    
    // Then reset all states
    setIsConversationActive(false);
    conversationActiveRef.current = false; // This will stop the conversation loop
    conversationPausedRef.current = false;
    setVoiceState('idle');
    setTurnCount(0);
    setIsConversationPaused(false);
    setShowVoiceOverlay(false);
    
    // Reset AI speaking locks
    aiSpeakingRef.current = false;
    setIsAISpeaking(false);

    // Stop watchdog
    if (interruptWatchdogRef.current) {
      clearInterval(interruptWatchdogRef.current);
      interruptWatchdogRef.current = null;
    }
    
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
    // If a stop has been requested, abort immediately
    if (stopRequestedRef.current) {
      if (isDebugLoggingEnabled) console.log('⛔ playAIResponse aborted: stop requested');
      return;
    }
    // CRITICAL: Prevent multiple AI instances speaking simultaneously
    if (aiSpeakingRef.current) {
      console.log('🚫 BLOCKED: AI is already speaking, preventing duplicate speech');
      console.log('🚫 Current AI text:', text.substring(0, 50) + '...');
      return; // Don't start another instance
    }

    try {
      // Note: Passive listening stays active during AI speech to allow wake-word interrupts
      // Non-wake-word transcripts are filtered in the result handler
      if (isDebugLoggingEnabled) console.log('🔐 LOCKING AI speech - starting playback');
      aiSpeakingRef.current = true;
      setIsAISpeaking(true);
      if (isDebugLoggingEnabled) console.log('🔐 AI speaking state set to:', aiSpeakingRef.current);
      
      // Tell VAD interrupt manager AI is speaking (if VAD enabled)
      if (vadEnabledRef.current && interruptManagerRef.current) {
        interruptManagerRef.current.setAISpeaking(null); // Will set audio element later
      }
      
      if (isDebugLoggingEnabled) console.log('Playing AI response:', text);
  // Record AI text for self-trigger suppression
  currentAIAudioTextRef.current = (text || '').toLowerCase();
  aiSpeechStartTimeRef.current = Date.now();
      
      // PREVENT OVERLAPPING: Stop any existing audio first
      if (currentAudio || speechSynthesis.speaking) {
        console.log('🛑 Stopping existing audio to prevent overlap');
        killAllAudio();
        await new Promise(resolve => setTimeout(resolve, 100)); // Wait for stop
      }
      
      if (isDebugLoggingEnabled) console.log('🎤 Voice config:', azureSpeechConfig.voiceName);
      if (isDebugLoggingEnabled) console.log('🔑 Has Azure key:', !!azureSpeechConfig.subscriptionKey);
      
      // Set voice state to speaking BEFORE starting audio
      setVoiceState('speaking');
      
      // Reset barge-in flag before starting
      bargeInDetectedRef.current = false;
      
      // Start simplified barge-in detection immediately
      startBargeInDetection();
      
      // Try Azure Speech Service first
      try {
        if (isDebugLoggingEnabled) console.log('🎵 Attempting Azure Speech Service...');
        
        console.log('🎵 Starting Azure TTS request:', { 
          text: text.substring(0, 50) + '...',
          endpoint: azureSpeechConfig.endpoint,
          voiceName: azureSpeechConfig.voiceName 
        });
        
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
        }).catch(error => {
          console.error('❌ Azure fetch failed:', error);
          throw new Error(`Azure TTS fetch error: ${error.message}`);
        });

        console.log('🎵 Azure fetch response:', {
          status: response.status,
          statusText: response.statusText,
          ok: response.ok,
          contentType: response.headers.get('content-type'),
          contentLength: response.headers.get('content-length')
        });

        if (response.ok) {
          const audioBlob = await response.blob();
          console.log('🎵 Azure response received:', {
            status: response.status,
            contentType: response.headers.get('content-type'),
            blobSize: audioBlob.size,
            blobType: audioBlob.type
          });
          
          // Validate audio blob
          if (audioBlob.size === 0) {
            throw new Error('Azure returned empty audio blob');
          }
          
          if (!audioBlob.type.includes('audio')) {
            console.warn('⚠️ Unexpected blob type:', audioBlob.type);
          }
          
          const audioUrl = URL.createObjectURL(audioBlob);
          console.log('🎵 Created audio URL:', audioUrl);
          
          return new Promise((resolve, reject) => {
            const audio = new Audio(audioUrl);
            audio.preload = 'auto'; // Preload for faster playback
            audio.onloadstart = () => { // Start playing as soon as loading begins
              if (stopRequestedRef.current) {
                try { audio.pause(); } catch {}
                return; // Do not proceed if stop requested
              }
              console.log(`${PASSIVE_LOG_ICON} [PASSIVE] Audio loading - starting barge-in detection`);
              
              // Ensure barge-in detection is active when audio starts
              if (!audioMonitoringRef.current) {
                startBargeInDetection();
              }
              
              audio.play().then(() => {
                setCurrentAudio(audio);
                console.log('🔊 Azure audio playing - detection active');
                console.log('🔊 Audio state:', {
                  paused: audio.paused,
                  muted: audio.muted,
                  volume: audio.volume,
                  duration: audio.duration,
                  currentTime: audio.currentTime,
                  readyState: audio.readyState
                });
                
                // Update VAD interrupt manager with audio element (if VAD enabled)
                if (vadEnabledRef.current && interruptManagerRef.current) {
                  interruptManagerRef.current.setAISpeaking(audio);
                }
              }).catch((playError) => {
                console.error('❌ Audio play() failed:', playError);
                // Fallback to canplay if immediate play fails
                audio.oncanplay = () => {
                  audio.play().then(() => {
                    setCurrentAudio(audio);
                    console.log('🔊 Azure audio playing (after canplay)');
                  }).catch(reject);
                };
              });
            };
            audio.onended = () => {
              if (isDebugLoggingEnabled) console.log('Audio playback finished');
              URL.revokeObjectURL(audioUrl);
              setCurrentAudio(null);
              // Stop barge-in detection when audio ends
              stopBargeInDetection();
              // Clear AI text tracking after small delay (allows late recognizer flush)
              setTimeout(() => { currentAIAudioTextRef.current = ''; }, 400);
              // CRITICAL: Unlock AI speech when audio actually ends
              console.log('🔓 UNLOCKING AI speech - Azure audio finished');
              aiSpeakingRef.current = false;
              setIsAISpeaking(false);
              
              // Tell VAD interrupt manager AI finished (if VAD enabled)
              if (vadEnabledRef.current && interruptManagerRef.current) {
                interruptManagerRef.current.setIdle();
              }
              
              console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ✅ Passive listening now accepting all speech (not just wake words)`);
              // Auto-start active listening quickly if conversation loop not already foreground listening
              if (conversationActiveRef.current === 'RUNNING' && !activeUserRecognitionRef.current && !stopRequestedRef.current) {
                setTimeout(() => {
                  if (!aiSpeakingRef.current && conversationActiveRef.current === 'RUNNING' && !activeUserRecognitionRef.current) {
                    playEarcon();
                    safeRestartInterruptListening(0); // keep passive ready
                  }
                }, ACTIVE_LISTEN_DELAY_MS);
              }
              resolve();
            };
            audio.onerror = (error) => {
              console.error('🚨 AUDIO PLAYBACK ERROR:', error);
              console.error('🚨 Error details:', {
                audioSrc: audio.src,
                audioError: audio.error,
                errorCode: audio.error?.code,
                errorMessage: audio.error?.message,
                networkState: audio.networkState,
                readyState: audio.readyState,
                currentTime: audio.currentTime,
                duration: audio.duration
              });
              
              // Clean up
              URL.revokeObjectURL(audioUrl);
              // Stop barge-in detection on error
              stopBargeInDetection();
              // CRITICAL: Unlock AI speech on error too
              console.log('🔓 UNLOCKING AI speech - Azure audio error');
              aiSpeakingRef.current = false;
              setIsAISpeaking(false);
              
              // Tell VAD interrupt manager AI finished (if VAD enabled)
              if (vadEnabledRef.current && interruptManagerRef.current) {
                interruptManagerRef.current.setIdle();
              }
              currentAIAudioTextRef.current = '';
              
              // If a stop was requested, do not attempt fallback
              if (stopRequestedRef.current) {
                reject(new Error('Playback stopped by user'));
                return;
              }
              // Try browser fallback instead of rejecting
              console.warn('🔄 Azure audio failed, attempting browser speech fallback');
              reject(new Error(`Audio playback failed: ${audio.error?.message || 'Unknown error'}`));
            };
          });
        } else {
          // Handle non-200 responses from Azure
          const errorText = await response.text().catch(() => 'Unable to read error response');
          console.error('❌ Azure TTS API error:', {
            status: response.status,
            statusText: response.statusText,
            errorText: errorText,
            headers: Object.fromEntries(response.headers.entries())
          });
          throw new Error(`Azure TTS API error: ${response.status} ${response.statusText} - ${errorText}`);
        }
      } catch (azureError) {
        console.warn('❌ Azure Speech failed, using browser fallback:', {
          error: azureError.message,
          stack: azureError.stack,
          endpoint: azureSpeechConfig.endpoint,
          timestamp: new Date().toISOString()
        });
        
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
              currentAIAudioTextRef.current = (text || '').toLowerCase();
              aiSpeechStartTimeRef.current = Date.now();
            };
            
            utterance.onend = () => {
              console.log('Browser speech finished');
              // Stop barge-in detection when speech ends
              stopBargeInDetection();
              setTimeout(() => { currentAIAudioTextRef.current = ''; }, 400);
              // CRITICAL: Unlock AI speech when browser speech ends
              console.log('🔓 UNLOCKING AI speech - browser speech finished');
              aiSpeakingRef.current = false;
              setIsAISpeaking(false);
              if (conversationActiveRef.current === 'RUNNING' && !activeUserRecognitionRef.current && !stopRequestedRef.current) {
                setTimeout(() => {
                  if (!aiSpeakingRef.current && conversationActiveRef.current === 'RUNNING' && !activeUserRecognitionRef.current) {
                    playEarcon();
                    safeRestartInterruptListening(0);
                  }
                }, ACTIVE_LISTEN_DELAY_MS);
              }
              resolve();
            };
            utterance.onerror = (error) => {
              console.error('Browser speech error:', error);
              // Stop barge-in detection on error
              stopBargeInDetection();
              // CRITICAL: Unlock AI speech on browser speech error
              console.log('🔓 UNLOCKING AI speech - browser speech error');
              aiSpeakingRef.current = false;
              setIsAISpeaking(false);
              currentAIAudioTextRef.current = '';
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
      // CRITICAL: Unlock AI speech on error
      console.log('🔓 UNLOCKING AI speech - playback error');
      aiSpeakingRef.current = false;
      setIsAISpeaking(false);
      throw error;
    }
  };

  // Main voice conversation handler for continuous mode
  const handleVoiceConversation = async () => {
    enableDebugLogging(); // Enable logging when voice conversation starts
    console.log('Voice button clicked, current state:', voiceState, 'Active:', isConversationActive);
    console.log('🧠 VOICE HISTORY DEBUG: Current history length:', voiceConversationHistory.length);
    console.log('🧠 VOICE HISTORY DEBUG: History content:', voiceConversationHistory.slice(-3));
    logPassiveListeningStatus('CONVERSATION_START');
    
    if (isConversationActive) {
      // Stop any ongoing audio immediately to prevent overlap
      console.log('🛑 Stopping voice conversation - killing all audio first');
      killAllAudio();
      
      // End the conversation cleanly
      setOverlayAnimation('slide-down');
      
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
    console.log('Starting continuous conversation with natural flow');
    debugVoiceHistory('CONVERSATION_START');
    
    // Prevent multiple conversation instances
    if (conversationActiveRef.current === 'RUNNING') {
      console.log('🚫 BLOCKED: Conversation already running, preventing duplicate');
      return;
    }
    
    // Ensure clean state
    killAllAudio();
    aiSpeakingRef.current = false;
    setIsAISpeaking(false);
    // Clear any previous stop request for a fresh session
    stopRequestedRef.current = false;
    
    setIsConversationActive(true);
    conversationActiveRef.current = true;  // Will be set to 'RUNNING' in conversationLoop
    conversationPausedRef.current = false;
    setTurnCount(0);
    
    // Re-evaluate VAD availability for each session (allows retry after temporary failures)
    if (envAllowsVAD && vadCapability.supported && !vadInitializedRef.current) {
      vadEnabledRef.current = true;
      vadDisabledReasonRef.current = null;
    }

    // Check if VAD should be used (Sesame.com style)
    if (vadEnabledRef.current) {
      console.log('🎯 Attempting to initialize VAD system (Sesame.com style)...');
      const vadSuccess = await initializeVADSystem();
      
      if (vadSuccess) {
        console.log('✅ Using VAD system - no wake words needed!');
        console.log('💬 Just start talking naturally to interact');
        console.log('⚡ Interrupt AI anytime by simply speaking');
        
        // Play welcome message
        setVoiceState('speaking');
        const vadWelcomeMessage = "Hi! I'm Pal, your AI tutor. You can start talking naturally - no wake word needed. Just speak whenever you're ready, and feel free to interrupt me anytime.";
        
        try {
          await playAIResponse(vadWelcomeMessage);
        } catch (error) {
          console.error('Error playing VAD welcome:', error);
        }
        
        // VAD system is now running continuously
        return;
      } else {
        console.log('⚠️ VAD initialization failed, falling back to wake-word system');
        vadDisabledReasonRef.current = 'init-failed';
        vadEnabledRef.current = false;
        console.log('⚠️ Natural over-talk detection (VAD) disabled:', describeVADDisableReason(vadDisabledReasonRef.current));
      }
    }
    
    // Fallback to wake-word system
    console.log('📢 Using wake-word system (say \"Listen Pal\" to interrupt)');
    
    // Welcome message with interrupt protection
    setVoiceState('speaking');
    let playWelcome = !welcomePlayedRef.current;
    const welcomeMessage = "Hi! I'm Pal, your AI tutor. I'm ready for our conversation - what would you like to learn about today? Just start talking naturally after I finish. If you need to interrupt me later while I'm speaking, just say 'Listen Pal' or 'Pal Listen'.";
    
    try {
      // CRITICAL: Do NOT start interrupt listening during welcome message - AI is speaking!
  console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 📴 Welcome message starting - passive listening & barge-in disabled during intro`);
      
      if (playWelcome) {
        welcomePlayedRef.current = true;
        await playAIResponse(welcomeMessage);
      } else {
        if (isDebugLoggingEnabled) console.log('🛑 Skipping duplicate welcome message');
      }
    } catch (error) {
      console.error('Error playing welcome message:', error);
    } finally {
      // CRITICAL: Start interrupt listening AFTER welcome message
  console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🌟 INTRO COMPLETE: enabling passive wake AFTER initial auto-listen turn`);
  // Instead of starting passive listening immediately, we jump straight to active foreground listening for the user's first input.
  // Passive wake listening will be started only AFTER the first user turn completes, to avoid early accidental self-trigger during intro tail.
  deferPassiveWakeStartRef.current = true;
      // Start watchdog to ensure passive listening remains active
      if (!interruptWatchdogRef.current) {
        interruptWatchdogRef.current = setInterval(() => {
          const active = isConversationActive || conversationActiveRef.current === 'RUNNING' || conversationActiveRef.current === true;
          // Don't try to (re)start passive listening while AI is speaking or foreground recognition is running
          if (active && !aiSpeakingRef.current && !activeUserRecognitionRef.current && !stopRequestedRef.current) {
            // If recognition object is missing, restart
            if (!passiveRecognitionRef.current) {
              console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🛡️ WATCHDOG: Passive listening missing - restarting`);
              startInterruptListening();
            }
          }
        }, 1500);
      }
      
      // Set conversation as active before starting loop
      conversationActiveRef.current = true;
    }
    
    // Small delay to ensure state is updated, then start the conversation loop
    setTimeout(() => {
      conversationLoop();
    }, 400);
  };

  const conversationLoop = async () => {
    console.log('ConversationLoop started, conversationActiveRef:', conversationActiveRef.current);
    
    // Prevent multiple conversation loops from running simultaneously
    if (conversationActiveRef.current === 'RUNNING') {
      console.log('🚫 BLOCKED: Conversation loop already running, preventing duplicate');
      return;
    }
    
    // Mark conversation loop as running
    conversationActiveRef.current = 'RUNNING';
    
    while (conversationActiveRef.current === 'RUNNING' && !conversationPausedRef.current) {
      if (stopRequestedRef.current) {
        console.log('🛑 Stop requested flag set - breaking loop');
        break;
      }
      try {
        console.log('Starting new turn in conversation loop');
        debugVoiceHistory('LOOP_TURN_START');
        
        // Double check if conversation was ended or paused
        if (conversationActiveRef.current !== 'RUNNING' || conversationPausedRef.current) {
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
        
  // IMPORTANT: Stop passive wake-word listening to avoid dual-recognizer conflicts
  stopInterruptListening();
  // Listen for user input (foreground recognition)
        const userInput = await startContinuousListening().catch(e => {
          console.log('Foreground recognition error captured:', e?.message || e);
          return '';
        });
        console.log('User said:', userInput);
        
        // Clear inactivity timer since user spoke
        if (inactivityTimeout) {
          clearTimeout(inactivityTimeout);
          setInactivityTimeout(null);
        }
        
        // Skip processing if input is empty or just whitespace
        if (!userInput || userInput.trim().length === 0) {
          console.log('Empty input received, continuing conversation...');
          if (deferPassiveWakeStartRef.current) {
            console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ▶️ Starting deferred passive wake listening (empty first attempt)`);
            deferPassiveWakeStartRef.current = false;
            startInterruptListening();
          }
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
        
        // Process the question using voice-specific AI (doesn't interfere with chat)
        setVoiceState('processing');
        debugVoiceHistory('BEFORE_AI_RESPONSE');
        let aiResponse;
        try {
          aiResponse = await getVoiceAIResponse(userInput);
        } catch (error) {
          console.log('Error in getVoiceAIResponse, using fallback:', error);
          aiResponse = "I heard what you said and I'd love to continue our conversation. What would you like to talk about next?";
        }
        
        // Ensure passive listening is ON before AI speaks so wake word works
        if (!passiveRecognitionRef.current && (isConversationActive || conversationActiveRef.current === 'RUNNING' || conversationActiveRef.current === true)) {
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔄 Ensuring passive listening is active before AI speaks`);
          startInterruptListening();
        }

        // Speak the response (AI already includes conversation-continuing questions)
        setVoiceState('speaking');
        
        try {
          // Keep passive listening ON during AI speech to allow wake-word interrupts
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔁 Keeping passive listening ON during AI speech for wake-word interrupts`);
          
          await playAIResponse(aiResponse);
        } catch (error) {
          console.log('Error in playAIResponse, continuing conversation:', error);
          // Continue conversation even if audio fails
        } finally {
          // Passive listening should remain active; watchdog will also maintain it
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ✅ Passive listening confirmed/ensured during AI speech`);
        }
        
        // Increment turn count
        setTurnCount(prev => prev + 1);
        
        // After first completed user turn, if passive wake was deferred, enable it now
        if (deferPassiveWakeStartRef.current) {
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ✅ First user turn complete - enabling passive wake listening now`);
          deferPassiveWakeStartRef.current = false;
          setTimeout(() => startInterruptListening(), 250);
        }

        // Minimal pause for immediate conversation flow
        await new Promise(resolve => setTimeout(resolve, 200));
        
      } catch (error) {
        console.log('Conversation error:', error.message);
        
        if (error.message === 'Speech timeout' || error.message === 'Request timeout') {
          // Handle timeout gracefully - continue conversation instead of ending
          console.log('Timeout occurred - continuing conversation');
          if (!stopRequestedRef.current) {
            await playAIResponse("Sorry, I didn't catch that. Could you try again?");
          }
          continue;
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
          if (!stopRequestedRef.current) {
            await playAIResponse("Sorry about that technical hiccup. Let's continue our conversation!");
          }
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
      
      // Store the current history BEFORE adding temp entry
      const historyToSend = [...conversationHistoryPal];
      
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
          is_first_message: historyToSend.length === 0,
          is_conversational: isConversational,  // Tell backend the query type
          priority: isConversational ? 'fast' : 'detailed',
          conversation_history: historyToSend, // Send history WITHOUT the current question
          mode: 'pal'  // Learn with Pal mode - uses shared knowledge base
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

  // Voice-only AI response (doesn't update chat history to prevent interference)
  const getVoiceAIResponse = async (question) => {
    try {
      // Input validation and cleaning
      if (!question || typeof question !== 'string') {
        console.warn('🚨 Invalid question input:', question);
        return "I didn't catch that clearly. Could you please repeat your question?";
      }
      
      const cleanQuestion = question.trim();
      if (cleanQuestion.length === 0) {
        console.warn('🚨 Empty question after cleaning');
        return "I didn't hear your question clearly. Could you please try again?";
      }
      
      console.log('🎤 Voice AI processing clean question:', `"${cleanQuestion}"`);
      console.log('🎤 Original question:', `"${question}"`);
      console.log('🎤 Question length:', cleanQuestion.length);
      debugVoiceHistory('VOICE_AI_START');
      
      const isConversational = isConversationalQuery(cleanQuestion);
      const smartTimeout = getSmartTimeout(cleanQuestion);
      
      console.log('🔍 Is conversational:', isConversational);
      console.log('⏱️ Timeout set to:', smartTimeout, 'ms');
  console.log('🧠 Voice conversation history:', voiceHistoryRef.current.slice(-3));
      
  // Store the current voice history BEFORE adding temp entry
  // IMPORTANT: read from ref to avoid stale value inside async loops
  const historyToSend = [...voiceHistoryRef.current];
      
      // CONTEXT PRESERVATION: If voice history is empty but we have chat history,
      // merge them to maintain context across different input methods
      if (historyToSend.length === 0 && chatHistoryRef.current.length > 0) {
        console.log('🧠 CONTEXT MERGE: Using chat history for voice context');
        historyToSend.push(...chatHistoryRef.current);
      }
      
      // Safeguard: Warn if history is unexpectedly empty when it shouldn't be
      if (turnCount > 0 && historyToSend.length === 0) {
        console.warn('🚨 CONTEXT LOSS WARNING: Turn count is', turnCount, 'but voice history is empty!');
        console.warn('🚨 This means conversation context has been lost!');
      }
      
      // Add to voice history (not chat history)
      const tempHistoryEntry = { question: cleanQuestion, answer: '...' };
      console.log('🧠 ADDING to voice history - Question:', cleanQuestion);
      console.log('🧠 BEFORE adding - History length:', voiceConversationHistory.length);
      setVoiceConversationHistory(prev => {
        const updated = [...prev, tempHistoryEntry];
        console.log('🧠 AFTER adding - New history length:', updated.length);
        const trimmed = updated.slice(-10);
        voiceHistoryRef.current = trimmed;
        return trimmed;
      });
      
      const requestPayload = {
        question: cleanQuestion,
        uploaded_files: [],
        is_first_message: historyToSend.length === 0,
        is_conversational: isConversational,
        priority: isConversational ? 'fast' : 'detailed',
        conversation_history: historyToSend // Always send history, regardless of conversation state
      };
      
      console.log('📡 Sending to backend:', JSON.stringify(requestPayload, null, 2));
      console.log('🧠 CONTEXT CHECK: Sending', requestPayload.conversation_history.length, 'history entries');
      console.log('🧠 CONTEXT CHECK: History contains:');
      requestPayload.conversation_history.forEach((entry, index) => {
        console.log(`  [${index}] Q: "${entry.question}" | A: "${entry.answer?.substring(0, 100)}..."`);
      });
      
      const response = await fetchWithTimeout('http://localhost:8003/ask_question/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload)
      }, smartTimeout);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📥 Backend response:', JSON.stringify(data, null, 2));
      
      const aiResponse = data.answer || "I'd love to continue our conversation. What would you like to talk about?";
      console.log('🤖 AI Response:', `"${aiResponse}"`);
      
      // Check for problematic responses that indicate confusion
      if (aiResponse.includes("mix-up in your message") || 
          aiResponse.includes("how you can help me") ||
          aiResponse.includes("seems like there might have been")) {
        console.warn('🚨 AI seems confused, input might be unclear');
        console.warn('🚨 Original question was:', `"${cleanQuestion}"`);
        console.warn('🚨 Conversation history:', voiceConversationHistory.slice(-3));
      }
      
      // Update voice history with the response
      console.log('🧠 UPDATING voice history with AI response');
      setVoiceConversationHistory(prev => {
        const lastIndex = prev.length - 1;
        console.log('🧠 BEFORE response update - History length:', prev.length, '| Last entry answer:', prev[lastIndex]?.answer);
        
        if (lastIndex >= 0 && prev[lastIndex].answer === '...') {
          // Create new array with updated entry (avoid mutation)
          const updated = prev.map((entry, idx) => 
            idx === lastIndex ? { ...entry, answer: aiResponse } : entry
          );
          console.log('🧠 UPDATED last entry with AI response');
          console.log('🧠 CONTEXT SYNC: Keeping voice exchange separate from chat history');
          console.log('🧠 AFTER response update - History length:', updated.length);
          
          const trimmed = updated.slice(-10);
          voiceHistoryRef.current = trimmed;
          return trimmed;
        } else {
          console.warn('🧠 WARNING: Could not update last entry - lastIndex:', lastIndex, '| answer:', prev[lastIndex]?.answer);
          // Return previous state unchanged
          return prev;
        }
      });
      
      return aiResponse;
      
    } catch (error) {
      console.error('Voice AI response error:', error);
      
      // Update voice history with error message
      setVoiceConversationHistory(prev => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        if (lastIndex >= 0 && updated[lastIndex].answer === '...') {
          updated[lastIndex].answer = "I'd love to continue our conversation. What else would you like to discuss?";
        }
        const trimmed = updated.slice(-10);
        voiceHistoryRef.current = trimmed;
        return trimmed;
      });
      
      if (error.message === 'Request timeout') {
        return 'That took a bit longer than expected. Let me try to help you quickly!';
      } else {
        return "I'd love to continue our conversation. What else would you like to discuss?";
      }
    }
  };

  // Interrupt-only wake word detection (only active when AI is speaking)
  const startInterruptListening = () => {
    if (vadEnabledRef.current && vadInitializedRef.current) {
      if (isDebugLoggingEnabled) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⏭️ Skipping passive wake listener start - VAD is handling interrupts`);
      }
      return;
    }

    if (!('webkitSpeechRecognition' in window)) {
      console.log('Speech recognition not supported');
      return;
    }

    // Allow passive listening even while AI is speaking to catch wake word "Pal"
    // We rely on pattern filters below to avoid self-interruption
    if (aiSpeakingRef.current) {
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ℹ️ Starting passive listening while AI speaking (wake-word only mode)`);
    }

    if (passiveRecognitionRef.current) {
      passiveRecognitionRef.current.stop();
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true; // Enable interim results for faster detection
    // Use user-selected locale for better accent matching
    recognition.lang = speechLocale;
    recognition.maxAlternatives = 3; // Get more alternatives to catch variations

    // Try to bias recognition towards wake words if grammar API is available (best-effort)
    try {
      const SpeechGrammarList = window.SpeechGrammarList || window.webkitSpeechGrammarList;
      if (SpeechGrammarList) {
        const grammarList = new SpeechGrammarList();
  // Include new wake phrases (single + combined). JSGF does not easily express bigram matching as a single token,
  // but including both words increases likelihood of early detection before custom logic merges "listen pal".
  const wakeWordChoices = 'pal | paul | pell | pale | pail | pow | pol | paal | pahl | listen | listen pal | hey pal';
        const grammar = `#JSGF V1.0; grammar wake; public <wake> = ${wakeWordChoices};`;
        if (typeof grammarList.addFromString === 'function') {
          grammarList.addFromString(grammar, 1);
          recognition.grammars = grammarList;
          if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 📘 Wake-word grammar applied:`, grammar);
        }
      }
    } catch (e) {
      if (isDebugLoggingEnabled) console.log('Grammar hint not applied:', e?.message || e);
    }

    recognition.onstart = () => {
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🟢 PASSIVE LISTENING STARTED - Monitoring for wake words`);
      if (aiSpeakingRef.current) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⚠️ AI is speaking - passive will ONLY respond to wake words (ignoring other speech)`);
      }
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔍 Target wake words: pal, paul, pel, pow, pol, pail, pale, listen, listen pal`);
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔊 Listening mode: continuous =`, recognition.continuous, '| interim =', recognition.interimResults);
      if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ✅ Interrupt listening STARTED SUCCESSFULLY - say "Pal" to interrupt AI`);
      if (isDebugLoggingEnabled) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] Recognition continuous:`, recognition.continuous);
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] Recognition lang:`, recognition.lang);
      }
      setIsPassiveListening(true);
      // Safety watchdog: if still marked passive after 45s with no results and not speaking, restart
      try {
        setTimeout(() => {
          if (isPassiveListening && !aiSpeakingRef.current && !activeUserRecognitionRef.current && passiveRecognitionRef.current === recognition) {
            console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🕒 PASSIVE WATCHDOG: No activity, restarting passive listener`);
            try { recognition.stop(); } catch {}
          }
        }, 45000);
      } catch {}
    };

    recognition.onresult = (event) => {
      // Only process if we're not already processing an interrupt
      if (isProcessingInterrupt) {
        if (isDebugLoggingEnabled) console.log('⏸️ Already processing interrupt, ignoring');
        return;
      }

      // Rate limiting
      const now = Date.now();
      if (now - lastInterruptTime.current < 2000) {
        if (isDebugLoggingEnabled) console.log('⏸️ Interrupt cooldown active');
        return;
      }

      let finalTranscript = '';
      let interimTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      // Log what passive listening is catching
      if (finalTranscript.trim()) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 📝 FINAL transcript caught:`, `"${finalTranscript.trim()}"`);
      }
      if (interimTranscript.trim()) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 📄 INTERIM transcript caught:`, `"${interimTranscript.trim()}"`);
      }

  // Process both final and interim results for faster wake word detection
  const rawCombined = (finalTranscript + ' ' + interimTranscript);
  const allTranscript = rawCombined.toLowerCase().trim();
      
  console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔍 ANALYZING:`, `"${allTranscript}"`, '| AI speaking:', aiSpeakingRef.current, '| Voice state:', voiceStateRef.current);
  if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] Interrupt listening heard:`, `"${allTranscript}"`);
  if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] Current AI speaking state:`, aiSpeakingRef.current);
  if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] Current voice state:`, voiceStateRef.current);

      // EARLY FILTER: While AI is speaking, skip deep analysis unless transcript hints a wake word pattern
      if (aiSpeakingRef.current) {
        if (!POTENTIAL_WAKE_REGEX.test(allTranscript)) {
          if (isDebugLoggingEnabled && allTranscript.length < 60) {
            console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⏭️ Skipping non-wake fragment during AI speech (likely AI's own voice)`);
          }
          return;
        }
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ✅ Potential wake word detected during AI speech - analyzing...`);
      }
      
      // Enhanced filter for AI's own speech patterns
      const aiPatterns = ["i'm pal", "hi i'm pal", "your ai tutor", "ready for our conversation", 
                         "tutoring services", "specific subject", "provide more details", "clarify your request", 
                         "looking for information", "could you please", "seems like you", "please provide", 
                         "information about", "how can i", "what would you", "hello", "hi there", "hello there",
                         "assist you today", "help you", "can i assist", "how may i", "biodiversity",
                         "you can just", "start talking", "after i finish", "no wake word", "just start"];
      
      const matchedPattern = aiPatterns.find(pattern => allTranscript.includes(pattern));
      
      if (aiSpeakingRef.current && matchedPattern) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🚫 FILTERING AI SPEECH - Pattern:`, `"${matchedPattern}"`, '| Full transcript:', `"${allTranscript}"`);
        if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🚫 IGNORED: Detected AI's own speech during AI speaking`);
        return;
      }
      
      if (aiSpeakingRef.current) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⚠️ AI SPEAKING candidate - further wake analysis`);
      }
      
      // Robust wake word detection using utility module
      const normalized = normalizeTranscript(allTranscript);
      const tokens = mergeBigrams(normalized.split(' ').filter(Boolean));

      // SELF-TRIGGER SUPPRESSION: If AI is speaking and transcript is wholly contained in AI text window, ignore
      if (aiSpeakingRef.current && currentAIAudioTextRef.current) {
        const elapsed = Date.now() - aiSpeechStartTimeRef.current;
        if (suppressIfAIMatch(tokens, currentAIAudioTextRef.current, BASE_WAKE_WORDS, elapsed)) {
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🙈 SUPPRESSED wake candidate (matches AI speech tokens only):`, tokens.join(' '));
          return;
        }
      }

      const { matched, simpleFound, hasWakeWord: containsWakeWord, detectedWakeWords } = detectWake(allTranscript);
      // While AI is speaking, require bigram form (listenpal or pallisten) to proceed
      if (aiSpeakingRef.current && containsWakeWord) {
  const tokenSet = new Set(tokens);
  const hasBigram = tokenSet.has('listenpal') || tokenSet.has('pallisten') || tokenSet.has('heypal');
        if (!hasBigram) {
          if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ❎ Wake token ignored (single word not allowed during AI speech)`);
          return;
        }
      }

      if (isDebugLoggingEnabled) {
  console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔍 WAKE WORD SCAN:`, {
          transcript: `"${allTranscript}"`,
          tokens,
          matched,
          simpleFound,
          hasWakeWord: containsWakeWord,
          aiSpeaking: aiSpeakingRef.current,
          lang: recognition.lang
        });
      }

      if (containsWakeWord) {
  console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🚨 WAKE WORD DETECTED!`, detectedWakeWords, '| Triggering interrupt!');
        if (isDebugLoggingEnabled) console.log('🚨 WAKE WORD DETECTED!');
        if (isDebugLoggingEnabled) console.log('🛑 IMMEDIATE INTERRUPT TRIGGERED!');
        if (isDebugLoggingEnabled) console.log('🛑 Full transcript:', `"${allTranscript}"`);
        if (isDebugLoggingEnabled) console.log('🛑 AI speaking state:', aiSpeakingRef.current);
        // If AI is speaking, stop immediately before any other logic
        if (aiSpeakingRef.current) {
          try {
            killAllAudio();
          } catch (e) {
            console.log('Error killing audio on wake word:', e);
          }
        }
        // Play a quick beep sound for immediate feedback
        try {
          const audioContext = new (window.AudioContext || window.webkitAudioContext)();
          const oscillator = audioContext.createOscillator();
          const gainNode = audioContext.createGain();
          
          oscillator.connect(gainNode);
          gainNode.connect(audioContext.destination);
          
          oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
          gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
          
          oscillator.start(audioContext.currentTime);
          oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
          console.log('Audio beep failed:', e);
        }
        
        // Immediate interrupt - don't wait for validation
        lastInterruptTime.current = now;
        handleInterrupt(allTranscript);
        return; // Exit immediately after processing
      } else {
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ❌ NO WAKE WORD - transcript:`, `"${allTranscript}"`);
        if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] No wake word detected in:`, allTranscript);
      }
    };

    recognition.onerror = (event) => {
      if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ❌ Interrupt listening error:`, event.error);
      if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] Error details:`, event);
      
      // Use safe restart on certain errors
      if (event.error === 'no-speech' || event.error === 'aborted') {
        if (isDebugLoggingEnabled) console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔄 Restarting interrupt listening due to:`, event.error);
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔄 ERROR RECOVERY: Using safe restart method`);
        // If we aborted due to foreground recognition starting, wait a bit longer
        safeRestartInterruptListening(event.error === 'aborted' ? 700 : 500);
      }
    };

    recognition.onend = () => {
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⏹️ PASSIVE LISTENING ENDED - Wake word monitoring stopped`);
      logPassiveListeningStatus('RECOGNITION_ENDED');
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🗘️ Status check: Conversation active:`, isConversationActive, '| Processing interrupt:', isProcessingInterrupt);
      setIsPassiveListening(false); // ensure flag resets
      
      // Use safe restart when there's an active voice session hint and we're not in the middle of an interrupt
      const sessionActiveHint = (isConversationActive || conversationActiveRef.current === 'RUNNING' || conversationActiveRef.current === true || showVoiceOverlay);
      if (sessionActiveHint && !isProcessingInterrupt) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔄 AUTO-RESTART: Using safe restart method`);
        safeRestartInterruptListening(300);
      } else {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⛔ NO RESTART: Conversation inactive or interrupt in progress`);
      }
    };

    passiveRecognitionRef.current = recognition;
    try {
      recognition.start();
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ✅ PASSIVE LISTENING ACTIVE - Recognition engine started successfully`);
      logPassiveListeningStatus('START_SUCCESS');
    } catch (error) {
      console.error('Failed to start interrupt listening:', error);
    }
  };

  // Handle interrupt when AI is speaking
  const handleInterrupt = async (transcript) => {
    if (isProcessingInterrupt) return;

    try {
      setIsProcessingInterrupt(true);
      console.log('� === PROCESSING INTERRUPT ===');
      console.log('🛑 STOPPING ALL AUDIO IMMEDIATELY!');
      
      // Stop AI speech immediately and aggressively - try multiple times
      killAllAudio();
      setTimeout(() => killAllAudio(), 100); // Backup stop
      setTimeout(() => killAllAudio(), 300); // Second backup
      // Ensure AI speaking lock is cleared so no additional speech continues
      aiSpeakingRef.current = false;
      setIsAISpeaking(false);
      
      // Force stop interrupt listening
      if (passiveRecognitionRef.current) {
        try {
          passiveRecognitionRef.current.stop();
          passiveRecognitionRef.current.abort();
        } catch (e) {
          console.log('Error stopping passive recognition:', e);
        }
      }
      
      // Force set voice state
      setVoiceState('listening');
      
  console.log(`${ACTIVE_LOG_ICON} [ACTIVE] INTERRUPT PROCESSED - Ready for user input`);
      
      // Check if user provided command in same utterance
      const words = transcript.split(/\s+/);
      const palIndex = words.findIndex(word => word.includes('pal'));
      const commandWords = palIndex >= 0 ? words.slice(palIndex + 1) : [];
      
      if (commandWords.length > 0) {
        // User said "Pal [command]" - process immediately
        const command = commandWords.join(' ').trim();
  console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Interrupt with immediate command:`, command);
        
        setVoiceState('processing');
        const aiResponse = await getVoiceAIResponse(command);
        setVoiceState('speaking');
        await playAIResponse(aiResponse);
      } else {
        // User said only "Pal" - enter an active capture mode for the next utterance
  console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Wake word only ("Pal") detected - initiating active listening for follow-up question`);
        setVoiceState('listening');
        // Stop passive listening to avoid dual recognizers
        stopInterruptListening();
        try {
          // Small delay to ensure previous recognizers fully stopped
          await new Promise(r => setTimeout(r, 200));
          const userInput = await startContinuousListening();
          if (userInput && userInput.trim().length > 0) {
            console.log('✅ Captured follow-up after wake word:', userInput);
            setVoiceState('processing');
            const aiResponse = await getVoiceAIResponse(userInput);
            setVoiceState('speaking');
            await playAIResponse(aiResponse);
          } else {
            console.log('ℹ️ No follow-up captured after wake word');
          }
        } catch (e) {
          console.log('Error capturing follow-up after wake word:', e);
        } finally {
          // Resume passive wake word monitoring if conversation still active and not currently speaking
          if (!aiSpeakingRef.current && (isConversationActive || conversationActiveRef.current === 'RUNNING')) {
            safeRestartInterruptListening(300);
          }
        }
      }
      
      // Resume normal conversation flow
      setVoiceState('listening');
      
    } catch (error) {
      console.error('Error handling interrupt:', error);
      setVoiceState('listening');
    } finally {
      setIsProcessingInterrupt(false);
    }
  };

  const stopInterruptListening = () => {
    console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔴 STOPPING PASSIVE LISTENING - No longer monitoring for wake words`);
    if (passiveRecognitionRef.current) {
      console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⏹️ Stopping active recognition instance`);
      try { passiveRecognitionRef.current.stop(); } catch {}
      passiveRecognitionRef.current = null;
    }
    if (isPassiveListening) setIsPassiveListening(false);
    console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🚫 Passive listening state set to: false`);
  };
  
  // Safe function to restart passive listening with proper timing
  const safeRestartInterruptListening = (delayMs = 500) => {
    if (vadEnabledRef.current && vadInitializedRef.current) {
      if (isDebugLoggingEnabled) {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⏱️ SAFE RESTART skipped - VAD is active`);
      }
      return;
    }

    console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ⏱️ SAFE RESTART: Scheduling passive listening restart in ${delayMs}ms`);
    setTimeout(() => {
      // Determine if we should consider the session active enough to keep passive listening on
      const sessionActiveHint = (
        isConversationActive ||
        conversationActiveRef.current === 'RUNNING' ||
        conversationActiveRef.current === true ||
        showVoiceOverlay
      );
      const aiSpeaking = aiSpeakingRef.current;
      const noForegroundRecognition = !activeUserRecognitionRef.current;
      const notStopped = !stopRequestedRef.current;

      const shouldRestart = (sessionActiveHint || aiSpeaking) && noForegroundRecognition && notStopped;

      if (shouldRestart) {
        if (aiSpeaking) {
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 🔁 SAFE RESTART: AI is speaking but wake monitoring must stay active. Restarting passive listening.`);
        } else {
          console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ✅ SAFE RESTART: Conditions met - starting passive listening`);
        }
        startInterruptListening();
      } else {
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] ❌ SAFE RESTART: Cancelled - conditions not met`);
        console.log(`${PASSIVE_LOG_ICON} [PASSIVE] 📊 Status: AI speaking:`, aiSpeaking,
                    '| Conversation active (state/ref):', isConversationActive, '/', conversationActiveRef.current,
                    '| Overlay visible:', showVoiceOverlay,
                    '| Foreground listening active:', activeUserRecognitionRef.current,
                    '| Stop requested:', stopRequestedRef.current);
      }
    }, delayMs);
  };
  const handleMicClick = () => {
    if (!listening) {
      const recognition = new window.webkitSpeechRecognition();
      
      // Enhanced settings for better speech recognition
      recognition.continuous = true; // Allow longer speech
      recognition.interimResults = true; // Show real-time results
      recognition.lang = speechLocale; // Use user-selected locale
      recognition.maxAlternatives = 3; // Multiple alternatives
      
      let finalTranscript = '';
      
      recognition.onresult = (event) => {
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
            console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Mic Final:`, finalTranscript);
            
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
            console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Mic Interim:`, interimTranscript);
            
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
  console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Mic recognition ended`);
        setListening(false);
      };
      
      recognition.onstart = () => {
  console.log(`${ACTIVE_LOG_ICON} [ACTIVE] Mic recognition started`);
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
    
    // Create display text that shows if images/files are included
    const hasFiles = sessionUploadedFiles.length > 0;
    const displayQuestion = hasFiles 
      ? `${questionText} [📎 ${sessionUploadedFiles.length} file(s) attached]`
      : questionText;
    
    const newEntry = {
      id: Date.now(),
      question: displayQuestion,
      answer: '🔄 Processing your question and analyzing uploaded content... Please wait',
      timestamp: new Date().toISOString(),
      user: user?.name || 'Anonymous',
      hasAttachments: hasFiles,
      attachments: sessionUploadedFiles.map(f => ({ name: f.name, type: f.type }))
    };
    
    setConversationHistoryPal(prev => [...prev, newEntry]);
    
    try {
      // CONTEXT PRESERVATION: Combine chat and voice history for full context
      const combinedHistory = [...conversationHistoryPal];
      
      // Add recent voice conversations to context if they exist
      if (voiceConversationHistory.length > 0) {
        console.log('🧠 CONTEXT MERGE: Adding voice history to chat context');
        voiceConversationHistory.forEach(voiceEntry => {
          // Convert voice format to chat format
          const chatEntry = {
            id: Date.now() + Math.random(),
            question: voiceEntry.question,
            answer: voiceEntry.answer,
            timestamp: new Date().toISOString(),
            user: 'Voice User',
            hasAttachments: false,
            attachments: []
          };
          combinedHistory.push(chatEntry);
        });
      }
      
      console.log('🧠 CHAT CONTEXT: Using', combinedHistory.length, 'total entries (', conversationHistoryPal.length, 'chat +', voiceConversationHistory.length, 'voice )');
      
      const requestBody = {
        question: questionText,
        uploaded_files: sessionUploadedFiles.map(f => f.id), // Send file IDs
        has_images: sessionUploadedFiles.some(f => f.type === 'image'),
        file_context: sessionUploadedFiles.map(f => ({
          name: f.name,
          type: f.type,
          id: f.id
        })),
        conversation_history: combinedHistory, // Use combined history for full context
        is_first_message: combinedHistory.length === 0,
        mode: 'pal'  // Learn with Pal mode - uses shared knowledge base
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
        
        // Clear session files after successful submission
        setSessionUploadedFiles([]);
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
    
    // Combine existing uploaded files with session files
    const allFiles = [...uploadedFiles, ...sessionUploadedFiles];
    const hasFiles = allFiles.length > 0;
    const displayQuestion = sessionUploadedFiles.length > 0 
      ? `${questionText} [📎 ${sessionUploadedFiles.length} new file(s) attached]`
      : questionText;
    
    const newEntry = {
      id: Date.now(),
      question: displayQuestion,
      answer: '🔄 Processing your question and analyzing documents... Please wait',
      timestamp: new Date().toISOString(),
      user: user?.name || 'Anonymous',
      hasAttachments: sessionUploadedFiles.length > 0,
      attachments: sessionUploadedFiles.map(f => ({ name: f.name, type: f.type }))
    };
    
    setConversationHistoryBook(prev => [...prev, newEntry]);
    
    try {
      const requestBody = {
        question: questionText,
        uploaded_files: allFiles.map(f => f.id), // Include all files
        has_images: allFiles.some(f => f.type === 'image'),
        file_context: allFiles.map(f => ({
          name: f.name,
          type: f.type,
          id: f.id
        })),
        conversation_history: conversationHistoryBook, // Include conversation history
        is_first_message: conversationHistoryBook.length === 0,
        mode: 'book'  // My Book mode - uses personal uploaded documents
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
        
        // Clear session files after successful submission
        setSessionUploadedFiles([]);
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

  // Enhanced file upload handler with session management
  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setUploading(true);
    setUploadStatus('uploading');

    const newSessionFiles = [];

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
          
          // Check if the upload was actually successful
          if (data.success !== false) {
            const newFile = {
              id: data.document_id || Date.now(),
              name: file.name,
              url: data.url || URL.createObjectURL(file),
              type: file.type.includes('pdf') ? 'pdf' : file.type.includes('image') ? 'image' : 'document',
              status: 'uploaded',
              uploadedAt: new Date().toISOString()
            };
            
            // Add to both global and session files
            setUploadedFiles(prev => [...prev, newFile]);
            newSessionFiles.push(newFile);
            console.log('✅ File uploaded successfully:', file.name);
          } else {
            console.error('❌ Upload failed:', data.message || data.error);
            setUploadStatus('error');
          }
        } else {
          // Handle HTTP error responses
          const errorData = await response.json().catch(() => ({}));
          console.error('❌ Upload HTTP error:', response.status, errorData);
        }
      } catch (error) {
        console.error('Upload error:', error);
        setUploadStatus('error');
      }
    }

    // Add new files to session uploads
    setSessionUploadedFiles(prev => [...prev, ...newSessionFiles]);
    setUploadStatus(newSessionFiles.length > 0 ? 'success' : 'error');
    setUploading(false);
    
    // Clear the input
    event.target.value = '';
    
    // Clear upload status after 3 seconds
    setTimeout(() => {
      setUploadStatus('');
    }, 3000);
  };

  // Remove file from session uploads
  const removeSessionFile = (fileId) => {
    setSessionUploadedFiles(prev => prev.filter(file => file.id !== fileId));
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
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                        <span>🤔</span>
                        <div style={{ flex: 1 }}>
                          <div>{entry.question}</div>
                          {entry.hasAttachments && (
                            <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                              {entry.attachments.map((att, i) => (
                                <span key={i} style={{ background: '#e1e5e9', padding: '2px 6px', borderRadius: '4px' }}>
                                  {att.type === 'pdf' ? '📄' : '🖼️'} {att.name}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div style={{ padding: '12px', background: '#7c4afd', color: 'white', borderRadius: '12px' }}>
                      {entry.answer}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upload Status and Session Files Display */}
          {(uploadStatus || sessionUploadedFiles.length > 0) && (
            <div style={{ marginBottom: '12px', padding: '12px', background: '#f8f9fa', borderRadius: '12px', border: '1px solid #e1e5e9' }}>
              {uploadStatus === 'uploading' && (
                <div style={{ color: '#7c4afd', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '16px', height: '16px', border: '2px solid #7c4afd', borderTop: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}>  </div>
                  Uploading files...
                </div>
              )}
              
              {uploadStatus === 'success' && (
                <div style={{ color: '#28a745', fontSize: '0.9rem', marginBottom: sessionUploadedFiles.length > 0 ? '8px' : '0' }}>
                  ✅ Files uploaded successfully!
                </div>
              )}
              
              {uploadStatus === 'error' && (
                <div style={{ color: '#dc3545', fontSize: '0.9rem', marginBottom: sessionUploadedFiles.length > 0 ? '8px' : '0' }}>
                  ❌ Upload failed. Please try again.
                </div>
              )}
              
              {sessionUploadedFiles.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '6px', fontWeight: '600' }}>
                    📎 Uploaded for this conversation:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {sessionUploadedFiles.map((file) => (
                      <div 
                        key={file.id} 
                        style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '6px', 
                          padding: '4px 8px', 
                          background: 'white', 
                          borderRadius: '6px', 
                          border: '1px solid #ddd',
                          fontSize: '0.8rem'
                        }}
                      >
                        <span>{file.type === 'pdf' ? '📄' : '🖼️'}</span>
                        <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {file.name}
                        </span>
                        <button
                          onClick={() => removeSessionFile(file.id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#999',
                            cursor: 'pointer',
                            padding: '2px',
                            borderRadius: '3px',
                            fontSize: '0.7rem'
                          }}
                          title="Remove file"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Input Form */}
          <form onSubmit={e => { 
            e.preventDefault(); 
            enableDebugLogging(); // Enable logging when chat starts
            if (chatMode === 'pal') {
              handleAskPal();
            } else {
              handleAskBook();
            }
          }} style={{ display: 'flex', gap: '12px', padding: '16px', background: 'white', borderRadius: '16px', boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }}>
            
            {/* Universal file upload icon - works for both modes */}
            <label 
              htmlFor="universal-file-upload" 
              style={{ 
                cursor: 'pointer', 
                padding: '12px', 
                background: 'linear-gradient(135deg, #7c4afd, #a084fa)', 
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: '48px',
                height: '48px',
                transition: 'all 0.3s ease',
                boxShadow: '0 2px 8px rgba(124, 74, 253, 0.3)'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'scale(1.05)';
                e.target.style.boxShadow = '0 4px 12px rgba(124, 74, 253, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'scale(1)';
                e.target.style.boxShadow = '0 2px 8px rgba(124, 74, 253, 0.3)';
              }}
              title={chatMode === 'pal' ? "Upload images or documents with your question" : "Upload additional documents"}
            >
              <svg 
                width="20" 
                height="20" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="white" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              >
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              <input 
                id="universal-file-upload"
                type="file" 
                accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif,.bmp,.webp,.svg" 
                style={{ display: 'none' }} 
                onChange={handleFileUpload}
                disabled={uploading}
                multiple
              />
            </label>

            <input
              type="text"
              value={chatMode === 'pal' ? questionPal : questionBook}
              onChange={e => chatMode === 'pal' ? setQuestionPal(e.target.value) : setQuestionBook(e.target.value)}
              placeholder={chatMode === 'pal' ? "Ask me anything..." : (uploadedFiles.length === 0 ? "Upload documents first..." : "Ask me anything...")}
              style={{
                flex: 1,
                padding: '12px 16px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1rem'
              }}
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
          
          {/* Wake Word Tip */}
          <div style={{
            marginTop: '12px',
            padding: '8px 16px',
            background: 'rgba(124, 74, 253, 0.1)',
            borderRadius: '8px',
            fontSize: '0.85rem',
            color: '#7c4afd',
            textAlign: 'center',
            border: '1px solid rgba(124, 74, 253, 0.2)'
          }}>
            💡 <strong>Pro tip:</strong> Just speak after I'm quiet. To interrupt while I'm talking, say <strong>"Listen Pal"</strong> or <strong>"Pal Listen"</strong>.
          </div>
          
          {/* Wake Word Debug Panel (only show during voice conversations) */}
          {isConversationActive && (
            <div style={{
              marginTop: '12px',
              padding: '8px 12px',
              background: 'rgba(40, 167, 69, 0.1)',
              borderRadius: '6px',
              fontSize: '0.8rem',
              color: '#28a745',
              border: '1px solid rgba(40, 167, 69, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <span>
                🎧 <strong>Interrupt Mode:</strong> Only active during AI speech – say "Listen Pal" or "Pal Listen" to interrupt | 
                AI Speaking: {aiSpeakingRef.current ? 'Yes' : 'No'} | 
                State: {voiceState}
              </span>
            </div>
          )}
        </div>
      )}
      
      </div> {/* Close Main Content Area */}
      
      {/* Voice Conversation Overlay */}
      {showVoiceOverlay && (
        <div className={`voice-overlay ${overlayAnimation}`}>
          <div className="voice-overlay__content">
            <div className="pal-stage">
              <div className={`pal-avatar pal-avatar--${voiceState}${isConversationPaused ? ' pal-avatar--paused' : ''}`}>
                <div className="pal-avatar__pulse pal-avatar__pulse--outer" />
                <div className="pal-avatar__pulse pal-avatar__pulse--inner" />
                <div className="pal-avatar__image" />
              </div>
              <div className="pal-stage__controls">
                <button
                  className={`pal-stage__button pal-stage__button--action ${isConversationPaused ? 'pal-stage__button--resume' : 'pal-stage__button--pause'}`}
                  onClick={isConversationPaused ? resumeConversation : pauseConversation}
                  disabled={voiceState === 'processing' || voiceState === 'speaking'}
                >
                  {isConversationPaused ? '▶ Resume' : '⏸ Pause'}
                </button>
                <button
                  className="pal-stage__button pal-stage__button--end"
                  onClick={async () => {
                    stopDebugLogging();
                    setOverlayAnimation('slide-down');
                    endConversation();
                  }}
                >
                  🔴 End
                </button>
              </div>
              <div className="pal-stage__meta">
                <span>Turns: {turnCount}</span>
                <span>{voiceState === 'speaking' ? 'Say "Listen Pal" to interrupt.' : 'Interrupt anytime by speaking.'}</span>
              </div>
            </div>

            <aside className="voice-transcript-panel">
              <header className="voice-transcript-panel__header">
                <h3>Live Transcript</h3>
                <span className={`voice-dot voice-dot--${isConversationPaused ? 'paused' : voiceState}`} aria-hidden="true"></span>
              </header>

              <div className="voice-locale-selector">
                <label htmlFor="speech-locale" className="voice-locale-selector__label">
                  🌐 Accent
                </label>
                <select
                  id="speech-locale"
                  value={speechLocale}
                  onChange={(e) => setSpeechLocale(e.target.value)}
                  className="voice-locale-selector__dropdown"
                  disabled={voiceState === 'listening' || voiceState === 'processing'}
                >
                  {SPEECH_LOCALE_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.flag} {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {lastRecognizedText && (
                <div className="voice-transcript-panel__live">
                  <div className="voice-chip voice-chip--live">Live</div>
                  <p>{lastRecognizedText}</p>
                  {lastProcessedText && lastProcessedText !== lastRecognizedText && (
                    <p className="voice-transcript-panel__math">{lastProcessedText}</p>
                  )}
                  {recognitionConfidence < 0.9 && (
                    <div className="voice-confidence-warning">
                      ⚠️ Low confidence ({(recognitionConfidence * 100).toFixed(0)}%) - Please speak clearly
                    </div>
                  )}
                </div>
              )}

              <div className="voice-transcript-panel__list">
                {voiceConversationHistory.length === 0 ? (
                  <p className="voice-transcript-panel__empty">Start talking to see your transcript here.</p>
                ) : (
                  voiceConversationHistory.map((entry, index) => (
                    <div className="voice-transcript-item" key={`voice-history-${index}`}>
                      <div className="voice-transcript-item__bubble voice-transcript-item__bubble--user">
                        <span className="voice-transcript-item__speaker">You</span>
                        <p>{entry.question}</p>
                      </div>
                      {entry.answer && entry.answer !== '...' && (
                        <div className="voice-transcript-item__bubble voice-transcript-item__bubble--pal">
                          <span className="voice-transcript-item__speaker">Pal</span>
                          <p>{entry.answer}</p>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </aside>
          </div>
        </div>
      )}
      
    </div>
  );
}

export default App;
