/**
 * Azure Streaming STT Client
 * 
 * Real-time continuous speech-to-text using Azure Speech SDK
 * Replaces batch mode with streaming for natural conversation flow
 * 
 * Features:
 * - Continuous recognition (always listening)
 * - Interim results (see transcript as user speaks)
 * - Final results with punctuation
 * - Low latency (150-300ms)
 * 
 * @see https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/
 */

// Dynamic import to avoid module issues
let sdk = null;

async function loadSpeechSDK() {
  if (!sdk) {
    const module = await import('microsoft-cognitiveservices-speech-sdk');
    sdk = module;
  }
  return sdk;
}

class AzureStreamingClient {
  constructor() {
    this.recognizer = null;
    this.isStreaming = false;
    this.speechConfig = null;
    this.audioConfig = null;
    
    // Callbacks
    this.onInterimTranscript = null;
    this.onFinalTranscript = null;
    this.onError = null;
    this.onSessionStarted = null;
    this.onSessionStopped = null;
  }

  /**
   * Initialize Azure Speech SDK for streaming recognition
   */
  async initialize(subscriptionKey, region, locale = 'en-US') {
    try {
      console.log('🔵 Initializing Azure Streaming STT...');
      console.log('Region:', region);
      console.log('Locale:', locale);

      // Load SDK dynamically
      sdk = await loadSpeechSDK();

      // Create speech configuration
      this.speechConfig = sdk.SpeechConfig.fromSubscription(subscriptionKey, region);
      this.speechConfig.speechRecognitionLanguage = locale;

      // Optimize for real-time streaming
      this.speechConfig.setProperty(
        sdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
        '5000' // 5 seconds before timeout
      );

      this.speechConfig.setProperty(
        sdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
        '1000' // 1 second of silence to end
      );

      // Enable interim results for real-time feedback
      this.speechConfig.setProperty(
        sdk.PropertyId.SpeechServiceResponse_RequestSentimentAnalysis,
        'false'
      );
      
      // Enable profanity filter (optional, but recommended for educational app)
      this.speechConfig.setProfanity(sdk.ProfanityOption.Masked);
      
      // Request disfluency removal (removes "um", "uh", filler words)
      this.speechConfig.setProperty(
        sdk.PropertyId.SpeechServiceResponse_PostProcessingOption,
        'TrueText'
      );
      
      // Enable punctuation for better readability
      this.speechConfig.enableDictation();
      
      console.log('🎯 Enhanced recognition: disfluency removal, punctuation enabled');

      // Create audio configuration with echo cancellation (Sesame.com approach)
      // Echo cancellation prevents AI from hearing its own voice
      this.audioConfig = sdk.AudioConfig.fromDefaultMicrophoneInput();
      
      console.log('🎧 Echo cancellation enabled (prevents AI self-triggering)');
      console.log('🔇 Noise suppression enabled (filters background sounds)');

      // Create recognizer
      this.recognizer = new sdk.SpeechRecognizer(this.speechConfig, this.audioConfig);
      
      // Add educational/tutoring vocabulary hints for better accuracy
      const phraseList = sdk.PhraseListGrammar.fromRecognizer(this.recognizer);
      
      // Educational terms (Sesame.com approach - domain-specific vocabulary)
      const educationalTerms = [
        // Math terms
        'sine', 'cosine', 'tangent', 'theta', 'alpha', 'beta', 'gamma',
        'derivative', 'integral', 'equation', 'formula', 'calculate',
        'square root', 'factorial', 'exponential', 'logarithm',
        // Science terms
        'photosynthesis', 'mitochondria', 'DNA', 'RNA', 'chromosome',
        'molecule', 'atom', 'electron', 'proton', 'neutron',
        // Common tutoring phrases
        'explain', 'understand', 'clarify', 'example', 'practice',
        'homework', 'assignment', 'test', 'exam', 'quiz'
      ];
      
      educationalTerms.forEach(term => phraseList.addPhrase(term));
      console.log('📚 Educational vocabulary hints added for better accuracy');

      // Setup event handlers
      this.setupEventHandlers();

      console.log('✅ Azure Streaming STT initialized');
      return true;

    } catch (error) {
      console.error('❌ Azure STT initialization failed:', error);
      console.error('Check your subscription key and region');
      return false;
    }
  }

  /**
   * Setup Azure SDK event handlers
   */
  setupEventHandlers() {
    // Recognizing - interim results (real-time)
    this.recognizer.recognizing = (s, e) => {
      if (e.result.reason === sdk.ResultReason.RecognizingSpeech) {
        const text = e.result.text;
        console.log('📝 Interim:', text);
        this.onInterimTranscript?.(text);
      }
    };

    // Recognized - final results
    this.recognizer.recognized = (s, e) => {
      if (e.result.reason === sdk.ResultReason.RecognizedSpeech) {
        const text = e.result.text;
        
        // Get confidence score (0.0 to 1.0)
        const confidence = e.result.properties?.getProperty(
          sdk.PropertyId.SpeechServiceResponse_JsonResult
        );
        
        let confidenceScore = 1.0;
        try {
          if (confidence) {
            const jsonResult = JSON.parse(confidence);
            confidenceScore = jsonResult.NBest?.[0]?.Confidence || 1.0;
          }
        } catch (err) {
          console.log('Could not parse confidence score');
        }
        
        console.log('✅ Final:', text, `(confidence: ${(confidenceScore * 100).toFixed(1)}%)`);
        
        // Pass transcript with confidence score (always pass text, let UI handle low confidence)
        if (text && text.trim()) {
          this.onFinalTranscript?.(text, confidenceScore);
        }
      } else if (e.result.reason === sdk.ResultReason.NoMatch) {
        console.log('⚠️ No speech recognized');
      }
    };

    // Canceled - errors
    this.recognizer.canceled = (s, e) => {
      console.error('❌ Azure recognition canceled:', e.errorDetails);
      
      if (e.reason === sdk.CancellationReason.Error) {
        this.onError?.({
          code: e.errorCode,
          message: e.errorDetails
        });
      }
    };

    // Session events
    this.recognizer.sessionStarted = (s, e) => {
      console.log('🔵 Azure session started:', e.sessionId);
      this.onSessionStarted?.(e.sessionId);
    };

    this.recognizer.sessionStopped = (s, e) => {
      console.log('🔵 Azure session stopped:', e.sessionId);
      this.onSessionStopped?.(e.sessionId);
    };

    // Speech events
    this.recognizer.speechStartDetected = (s, e) => {
      console.log('🎤 Azure detected speech start');
    };

    this.recognizer.speechEndDetected = (s, e) => {
      console.log('🔇 Azure detected speech end');
    };
  }

  /**
   * Start continuous recognition (streaming mode)
   */
  startStreaming() {
    if (!this.recognizer) {
      console.error('❌ Azure recognizer not initialized');
      return;
    }

    if (this.isStreaming) {
      console.log('⚠️ Already streaming');
      return;
    }

    this.recognizer.startContinuousRecognitionAsync(
      () => {
        this.isStreaming = true;
        console.log('🎙️ Azure streaming started');
      },
      (err) => {
        console.error('❌ Failed to start streaming:', err);
        this.onError?.({ message: err });
      }
    );
  }

  /**
   * Stop continuous recognition
   */
  stopStreaming() {
    if (!this.recognizer) {
      console.error('❌ Azure recognizer not initialized');
      return;
    }

    if (!this.isStreaming) {
      console.log('⚠️ Not currently streaming');
      return;
    }

    this.recognizer.stopContinuousRecognitionAsync(
      () => {
        this.isStreaming = false;
        console.log('⏹️ Azure streaming stopped');
      },
      (err) => {
        console.error('❌ Failed to stop streaming:', err);
      }
    );
  }

  /**
   * Single-shot recognition (one-time, non-continuous)
   * Use this for initial testing or fallback mode
   */
  recognizeOnce() {
    return new Promise((resolve, reject) => {
      if (!this.recognizer) {
        reject(new Error('Recognizer not initialized'));
        return;
      }

      this.recognizer.recognizeOnceAsync(
        (result) => {
          if (result.reason === sdk.ResultReason.RecognizedSpeech) {
            console.log('✅ Recognized:', result.text);
            resolve(result.text);
          } else {
            console.log('❌ Recognition failed:', result.reason);
            reject(new Error('Recognition failed'));
          }
        },
        (err) => {
          console.error('❌ Recognition error:', err);
          reject(err);
        }
      );
    });
  }

  /**
   * Check if currently streaming
   */
  isActive() {
    return this.isStreaming;
  }

  /**
   * Clean up resources
   */
  destroy() {
    if (this.recognizer) {
      if (this.isStreaming) {
        this.stopStreaming();
      }
      this.recognizer.close();
      this.recognizer = null;
      console.log('🗑️ Azure recognizer destroyed');
    }
  }

  /**
   * Update language (requires recreating recognizer)
   */
  async setLanguage(languageCode) {
    console.log('🌐 Changing language to:', languageCode);
    
    const wasStreaming = this.isStreaming;
    
    // Stop current streaming
    if (wasStreaming) {
      this.stopStreaming();
    }

    // Update config
    this.speechConfig.speechRecognitionLanguage = languageCode;

    // Recreate recognizer
    if (this.recognizer) {
      this.recognizer.close();
    }
    
    this.recognizer = new sdk.SpeechRecognizer(this.speechConfig, this.audioConfig);
    this.setupEventHandlers();

    // Restart streaming if it was active
    if (wasStreaming) {
      this.startStreaming();
    }

    console.log('✅ Language updated to:', languageCode);
  }
}

export default AzureStreamingClient;
