// Azure Keyword Recognition Client
// Provides initialization for keyword spotting ("Hey Pal") using Azure Speech SDK.
// Falls back via callbacks if model load fails.

// Dynamic SDK loader (avoid build-time SSR/module resolution issues)
let _speechSdkModulePromise = null;
async function loadSpeechSDK() {
  if (_speechSdkModulePromise) return _speechSdkModulePromise;

  _speechSdkModulePromise = (async () => {
    try {
      // Try dynamic import first
      const SpeechSDKImport = await import('microsoft-cognitiveservices-speech-sdk');
      if (SpeechSDKImport && Object.keys(SpeechSDKImport).length > 0) {
        console.log('[AzureKWS] ✅ Loaded Speech SDK via direct import');
        return SpeechSDKImport;
      }
    } catch (err) {
      console.warn('[AzureKWS] Direct import failed:', err?.message || err);
    }

    // CDN fallback (browser global) if module import failed or returned empty
    if (typeof window !== 'undefined' && !window.SpeechSDK) {
      const CDN_URL = (import.meta.env.VITE_AZURE_SPEECH_SDK_CDN || 'https://aka.ms/csspeech/jsbrowserpackageraw');
      try {
        await new Promise((resolve, reject) => {
          const script = document.createElement('script');
            script.src = CDN_URL;
            script.async = true;
            script.onload = () => resolve();
            script.onerror = (e) => reject(new Error('CDN load failed: ' + CDN_URL));
            document.head.appendChild(script);
        });
        if (window.SpeechSDK) {
          console.log('[AzureKWS] Loaded Speech SDK from CDN');
          // Normalize to module-like shape so downstream code is unchanged
          return window.SpeechSDK;
        }
        throw new Error('CDN script loaded but window.SpeechSDK missing');
      } catch (cdnErr) {
        console.error('[AzureKWS] All Speech SDK load attempts failed.', cdnErr);
        throw cdnErr;
      }
    } else if (window.SpeechSDK) {
      return window.SpeechSDK;
    }
    throw new Error('Speech SDK not available after import and CDN attempts');
  })();

  return _speechSdkModulePromise;
}

/**
 * Initialize Azure keyword recognition.
 * @param {Object} opts
 * @param {function} opts.onWake - Called immediately when keyword detected.
 * @param {function} opts.onUserFinal - Called with final recognized user utterance after wake.
 * @param {function} [opts.onUserPartial] - Partial interim text callback.
 * @param {function} [opts.onError] - Error callback.
 * @param {function} [opts.onDebug] - Debug telemetry callback ({ engine, phase, text, hasWake }).
 * @param {string[]} [opts.phraseList] - Domain specific phrases to bias.
 * @param {function} [opts.onReady] - Called when keyword monitoring active.
 * @returns {{dispose:Function, stop:Function, start:Function, isActive:()=>boolean}}
 */
export async function initAzureKeyword(opts) {
  const {
    onWake,
    onUserFinal,
    onUserPartial,
  onError,
  onDebug,
    phraseList = [],
    onReady
  } = opts || {};

  const key = import.meta.env.VITE_AZURE_SPEECH_KEY;
  const region = import.meta.env.VITE_AZURE_SPEECH_REGION;
  const modelPath = import.meta.env.VITE_AZURE_KEYWORD_MODEL || '/hey_pal.table';

  if (!key || !region) {
    onError?.(new Error('Azure Speech key/region missing. Set VITE_AZURE_SPEECH_KEY & VITE_AZURE_SPEECH_REGION.'));
    throw new Error('Azure Speech key/region missing');
  }

  // Load SDK dynamically
  let SpeechSDK;
  try {
    SpeechSDK = await loadSpeechSDK();
  } catch (e) {
    onError?.(new Error('Azure Speech SDK load failed: ' + (e?.message || e)));
    throw e;
  }

  let keywordModel;
  try {
    keywordModel = SpeechSDK.KeywordRecognitionModel.fromFile(modelPath);
  } catch (e) {
    // Browser SDKs currently don't implement KeywordRecognitionModel.fromFile.
    // Fall back to plain continuous recognition and detect the wake phrase in-text.
    console.warn('[AzureKWS] Keyword model unavailable, using STT fallback:', e?.message || e);
    // Initialize SpeechConfig and Recognizer for fallback path below.
    let speechConfig;
    try {
      speechConfig = SpeechSDK.SpeechConfig.fromSubscription(key, region);
    } catch (se) {
      onError?.(new Error('SpeechConfig init failed: ' + (se?.message || se)));
      throw se;
    }
    speechConfig.speechRecognitionLanguage = 'en-US';
    
    // Optimized timeouts for fast wake word detection (Option B enhancement)
    try {
      // Shorter initial silence for faster wake detection
      speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, '500');
      // Shorter end silence for quicker response
      speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, '400');
      // Enable segmentation for better phrase detection
      speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps, 'true');
      // Enable profanity filter
      speechConfig.setProfanity(SpeechSDK.ProfanityOption.Raw);
    } catch (e) {
      console.warn('[AzureKWS] Could not set optimized properties:', e?.message);
    }

    let audioConfig;
    try {
      // Enhanced audio config with better microphone settings (Option B)
      audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
      
      // Try to enable enhanced audio processing
      try {
        audioConfig.setProperty(SpeechSDK.PropertyId.Speech_SegmentationSilenceTimeoutMs, '500');
      } catch {}
    } catch (ae) {
      onError?.(new Error('AudioConfig init failed: ' + (ae?.message || ae)));
      throw ae;
    }
    let recognizer;
    try {
      recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
    } catch (re) {
      onError?.(new Error('SpeechRecognizer init failed: ' + (re?.message || re)));
      throw re;
    }
    // Enhanced phrase boosting for better wake word detection (Option B)
    if (phraseList.length) {
      try {
        const pl = SpeechSDK.PhraseListGrammar.fromRecognizer(recognizer);
        // Add phrases with clear marking for debugging
        phraseList.forEach(p => {
          pl.addPhrase(p);
          // Boost wake word variants with higher weight
          if (p.toLowerCase().includes('hey') || p.toLowerCase().includes('pal')) {
            pl.addPhrase(p); // Add twice for extra boosting
          }
        });
        console.log('[AzureKWS] Enhanced phrase list applied:', phraseList.length, 'phrases');
      } catch (e) {
        console.warn('[AzureKWS] Phrase list error:', e?.message);
      }
    }

    let disposed = false;
    let state = 'LISTENING'; // LISTENING | CAPTURING | STOPPED
    let captureBuffer = [];
    let captureTimer = null;
    const WAKE_REGEX = /\bhey\s+pal\b/i;

    const endCaptureSoon = (delay = 650) => {
      if (captureTimer) clearTimeout(captureTimer);
      captureTimer = setTimeout(() => {
        if (disposed || state !== 'CAPTURING') return;
        const finalText = captureBuffer.join(' ').replace(/\s+/g,' ').trim();
        if (finalText) {
          try { onUserFinal?.(finalText); } catch {}
        }
        captureBuffer = [];
        state = 'LISTENING';
      }, delay);
    };

    recognizer.recognizing = (_, e) => {
      if (!e?.result?.text) return;
      if (state === 'CAPTURING') {
        const t = e.result.text.trim();
        if (t && onUserPartial) { try { onUserPartial(t); } catch {} }
        try { onDebug && onDebug({ engine: 'azure-stt-fallback', phase: 'partial', text: t, hasWake: /\bhey\s+pal\b/i.test(t.toLowerCase()) }); } catch {}
      }
    };

    recognizer.recognized = (_, e) => {
      if (!e?.result) return;
      const { result } = e;
      if (result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
        const text = (result.text || '').trim();
        if (!text) return;
        try { onDebug && onDebug({ engine: 'azure-stt-fallback', phase: 'final', text, hasWake: WAKE_REGEX.test(text.toLowerCase()) }); } catch {}
        if (state !== 'CAPTURING' && WAKE_REGEX.test(text.toLowerCase())) {
          // Wake phrase heard
          try { onWake?.(); } catch {}
          state = 'CAPTURING';
          captureBuffer = [];
          // Do not include the wake phrase itself; capture subsequent speech
          return;
        }
        if (state === 'CAPTURING') {
          // Accumulate user's first full utterance after wake
          captureBuffer.push(text);
          endCaptureSoon();
        }
      }
    };

    recognizer.canceled = (_, e) => {
      onError?.(new Error('Recognizer canceled (fallback): ' + (e?.errorDetails || e?.reason)));
      if (state !== 'STOPPED') {
        try { recognizer.stopContinuousRecognitionAsync(() => recognizer.startContinuousRecognitionAsync()); } catch {}
      }
    };

    recognizer.sessionStopped = () => {
      if (disposed || state === 'STOPPED') return;
      try { recognizer.startContinuousRecognitionAsync(); } catch {}
    };

    // Stats indicator for fallback engine
    if (!window.highpalWakeStats) {
      window.highpalWakeStats = { detections: 0, userTurns: 0, keywordActive: false, engine: 'azure-stt-fallback' };
    } else {
      window.highpalWakeStats.engine = 'azure-stt-fallback';
    }

    // Start fallback continuous recognition
    recognizer.startContinuousRecognitionAsync(() => {
      try { onReady?.(); } catch {}
    }, err => onError?.(err));

    return {
      stop() {
        if (disposed) return;
        state = 'STOPPED';
        try { recognizer.stopContinuousRecognitionAsync(()=>{},()=>{}); } catch {}
      },
      dispose() {
        if (disposed) return; this.stop(); disposed = true; try { recognizer.close(); } catch {}
      },
      start() {
        if (disposed) return; if (state === 'STOPPED') state = 'LISTENING';
        try { recognizer.startContinuousRecognitionAsync(); } catch {}
      },
      isActive: () => !disposed && state !== 'STOPPED'
    };
  }

  let speechConfig;
  try {
    speechConfig = SpeechSDK.SpeechConfig.fromSubscription(key, region);
  } catch (e) {
    onError?.(new Error('SpeechConfig init failed: ' + (e?.message || e)));
    throw e;
  }
  speechConfig.speechRecognitionLanguage = 'en-US';
  
  // Optimized settings for professional-grade wake word detection (Option B)
  try {
    // Faster response times
    speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, '500');
    speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, '400');
    // Enable word-level timestamps for better accuracy
    speechConfig.setProperty(SpeechSDK.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps, 'true');
    // Better segmentation
    speechConfig.setProperty(SpeechSDK.PropertyId.Speech_SegmentationSilenceTimeoutMs, '500');
    // Raw profanity (don't censor user speech)
    speechConfig.setProfanity(SpeechSDK.ProfanityOption.Raw);
    console.log('[AzureKWS] Optimized speech config applied');
  } catch (e) {
    console.warn('[AzureKWS] Could not apply all optimizations:', e?.message);
  }

  let audioConfig;
  try {
    audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
  } catch (e) {
    onError?.(new Error('AudioConfig init failed: ' + (e?.message || e)));
    throw e;
  }
  let recognizer;
  try {
    recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
  } catch (e) {
    onError?.(new Error('SpeechRecognizer init failed: ' + (e?.message || e)));
    throw e;
  }

  // Enhanced phrase list for domain boosting (Option B - professional quality)
  if (phraseList.length) {
    try {
      const pl = SpeechSDK.PhraseListGrammar.fromRecognizer(recognizer);
      phraseList.forEach(p => {
        pl.addPhrase(p);
        // Double-boost wake word variants
        if (p.toLowerCase().includes('hey') || p.toLowerCase().includes('pal')) {
          pl.addPhrase(p);
        }
      });
      console.log('[AzureKWS] Keyword recognizer phrase list applied:', phraseList.length, 'phrases');
    } catch (e) {
      console.warn('[AzureKWS] Phrase list error:', e?.message);
    }
  }

  let state = 'KEYWORD'; // KEYWORD | CAPTURING | STOPPED
  let disposed = false;

  function restartKeyword() {
    if (disposed || state === 'STOPPED') return;
    state = 'KEYWORD';
    recognizer.startKeywordRecognitionAsync(keywordModel, () => {
      window.highpalWakeStats && (window.highpalWakeStats.keywordActive = true);
      onReady?.();
    }, err => {
      window.highpalWakeStats && (window.highpalWakeStats.keywordActive = false);
      onError?.(err);
    });
  }

  recognizer.recognizing = (_, e) => {
    if (state === 'CAPTURING' && e?.result?.text && onUserPartial) {
      onUserPartial(e.result.text);
    }
  };

  recognizer.recognized = (_, e) => {
    if (!e || !e.result) return;
    const { result } = e;

    if (result.reason === SpeechSDK.ResultReason.RecognizedKeyword) {
      try { onDebug && onDebug({ engine: 'azure-kws', phase: 'keyword', text: '(keyword)', hasWake: true }); } catch {}
      window.highpalWakeStats && (window.highpalWakeStats.detections = (window.highpalWakeStats.detections||0) + 1);
      try { onWake?.(); } catch {}
      // Switch to continuous recognition mode for full utterance
      try {
        recognizer.stopKeywordRecognitionAsync(() => {
          if (disposed) return;
          state = 'CAPTURING';
          recognizer.startContinuousRecognitionAsync();
        });
      } catch (err) {
        onError?.(err);
      }
      return;
    }

    // Fallback: Sometimes keyword models miss in noisy conditions but raw speech text still contains phrase.
    // If we are still in KEYWORD mode and we got normal speech containing 'hey pal', treat it as a wake.
    if (state === 'KEYWORD' && result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
      const lower = (result.text || '').toLowerCase();
      try { onDebug && onDebug({ engine: 'azure-kws', phase: 'speech', text: result.text || '', hasWake: /\bhey\s+pal\b/.test(lower) }); } catch {}
      if (/\bhey\s+pal\b/.test(lower)) {
        window.highpalWakeStats && (window.highpalWakeStats.fallbackDetections = (window.highpalWakeStats.fallbackDetections||0) + 1);
        try { onWake?.(); } catch {}
        try {
          recognizer.stopKeywordRecognitionAsync(() => {
            if (disposed) return;
            state = 'CAPTURING';
            recognizer.startContinuousRecognitionAsync();
          });
        } catch (err) {
          onError?.(err);
        }
        return;
      }
    }

    if (state === 'CAPTURING' && result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
      if (result.text?.trim()) {
        onUserFinal?.(result.text.trim());
        window.highpalWakeStats && (window.highpalWakeStats.userTurns = (window.highpalWakeStats.userTurns||0) + 1);
      }
      // Reset to keyword mode
      try {
        recognizer.stopContinuousRecognitionAsync(() => restartKeyword());
      } catch (err) {
        onError?.(err);
      }
    }
  };

  recognizer.canceled = (_, e) => {
    if (disposed) return;
    onError?.(new Error('Recognizer canceled: ' + (e?.errorDetails || e?.reason)));
    if (state === 'CAPTURING') {
      // Attempt to resume keyword
      try { recognizer.stopContinuousRecognitionAsync(() => restartKeyword()); } catch {}
    } else if (state === 'KEYWORD') {
      setTimeout(restartKeyword, 600);
    }
  };

  recognizer.sessionStopped = () => {
    if (disposed) return;
    if (state === 'KEYWORD') setTimeout(restartKeyword, 400);
  };

  // Expose basic stats object if not present
  if (!window.highpalWakeStats) {
    window.highpalWakeStats = { detections: 0, userTurns: 0, keywordActive: false, engine: 'azure-kws' };
  } else {
    window.highpalWakeStats.engine = 'azure-kws';
  }

  // Start keyword spotting
  restartKeyword();

  return {
    stop() {
      if (disposed) return;
      state = 'STOPPED';
      try { recognizer.stopContinuousRecognitionAsync(()=>{},()=>{}); } catch {}
      try { recognizer.stopKeywordRecognitionAsync(()=>{},()=>{}); } catch {}
    },
    dispose() {
      if (disposed) return;
      this.stop();
      disposed = true;
      recognizer.close();
    },
    start() { if (disposed) return; if (state !== 'KEYWORD') restartKeyword(); },
    isActive: () => !disposed && state !== 'STOPPED'
  };
}

export default { initAzureKeyword };
