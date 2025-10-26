/**
 * VAD Detector - Voice Activity Detection using Silero VAD
 * 
 * Detects when user is speaking (any words, no wake word needed)
 * FREE and open source alternative to Porcupine wake word detection
 * 
 * Features:
 * - Real-time speech detection (<50ms latency)
 * - ML-based (95%+ accuracy)
 * - Filters background noise automatically
 * - No cloud communication (runs locally)
 * 
 * @see https://github.com/ricky0123/vad
 */

// CDN fallbacks for heavy assets so Vite dev server doesn't need to serve WASM/ONNX blobs
const VAD_ASSET_BASE_URL = 'https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.28/dist/';
const ONNX_WASM_BASE_URL = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.23.0/dist/';

// Dynamic import helper (forces Vite to ESM-transform the CommonJS build)
let MicVAD = null;

async function loadVAD() {
  if (!MicVAD) {
    try {
      const vadPrimary = await import('@ricky0123/vad-web');
      const ortModule = await import('onnxruntime-web');
      if (ortModule?.env?.wasm) {
        ortModule.env.wasm.wasmPaths = ONNX_WASM_BASE_URL;
        ortModule.env.wasm.numThreads = 1; // multi-threaded build needs COOP/COEP; force single-thread for safety
      }
      MicVAD = vadPrimary.MicVAD || (vadPrimary.default && vadPrimary.default.MicVAD) || vadPrimary.default || vadPrimary;
      if (MicVAD && MicVAD.MicVAD) {
        // Handle namespace style default export
        MicVAD = MicVAD.MicVAD;
      }
      if (!MicVAD) {
        throw new Error('MicVAD export missing from @ricky0123/vad-web');
      }
    } catch (primaryError) {
      console.warn('Primary VAD import failed, trying explicit dist path...', primaryError);
      try {
        const vadFallback = await import('@ricky0123/vad-web/dist/index.js');
        const ortModule = await import('onnxruntime-web');
        if (ortModule?.env?.wasm) {
          ortModule.env.wasm.wasmPaths = ONNX_WASM_BASE_URL;
          ortModule.env.wasm.numThreads = 1;
        }
        MicVAD = vadFallback.MicVAD || (vadFallback.default && vadFallback.default.MicVAD) || vadFallback.default || vadFallback;
        if (MicVAD && MicVAD.MicVAD) {
          MicVAD = MicVAD.MicVAD;
        }
        if (!MicVAD) {
          throw new Error('MicVAD export missing from @ricky0123/vad-web/dist/index.js');
        }
      } catch (fallbackError) {
        console.error('VAD dynamic import failed:', fallbackError);
        MicVAD = null;
        throw fallbackError;
      }
    }
  }
  return MicVAD;
}

class VADDetector {
  constructor() {
    this.vad = null;
    this.isListening = false;
    this.onSpeechStart = null;
    this.onSpeechEnd = null;
    this.onVADMisfire = null;
    this.speechStartGuard = null;
    
    // Sesame-style filtering
    this.speechStartTime = null;
    this.minSpeechDuration = 300; // ms - ignore sounds shorter than 300ms
    this.lastSpeechEndTime = 0;
    this.minTimeBetweenUtterances = 500; // ms - debounce rapid triggers
  }

  setSpeechStartGuard(guardFn) {
    this.speechStartGuard = typeof guardFn === 'function' ? guardFn : null;
  }

  /**
   * Initialize VAD with optimized settings for educational conversation
   * Enhanced thresholds inspired by Sesame.com approach
   */
  async initialize() {
    try {
      console.log('🎤 Initializing VAD detector (Sesame.com optimized)...');

      // Load VAD library dynamically
      const MicVADClass = await loadVAD();

      this.vad = await MicVADClass.new({
        baseAssetPath: VAD_ASSET_BASE_URL,
        onnxWASMBasePath: ONNX_WASM_BASE_URL,
        // ENHANCED: Positive speech threshold (0.0-1.0)
        // Sesame-style: Higher threshold reduces false positives from background voices
        // 0.85 = requires clear, sustained speech (not just any sound)
        positiveSpeechThreshold: 0.85,

        // Negative speech threshold (0.0-1.0)
        // When to consider speech has ended
        negativeSpeechThreshold: 0.35,

        // ENHANCED: Minimum consecutive frames to consider speech
        // Each frame is ~30ms, so 5 frames = ~150ms of sustained speech required
        // Filters out brief sounds (coughs, clicks, short exclamations)
        minSpeechFrames: 5,

        // Pre-speech padding (capture audio just before speech detected)
        // Helps catch the first syllable
        preSpeechPadFrames: 2,

        // ENHANCED: Redemption frames (allow brief pauses within speech)
        // 10 frames allows natural pauses ("um", "uh") without ending detection
        // Matches conversational cadence better
        redemptionFrames: 10,

        // Frame processing interval
        frameSamples: 1536, // ~96ms at 16kHz

        // Callbacks with Sesame-style filtering
        onSpeechStart: () => {
          const now = Date.now();

          if (this.speechStartGuard && !this.speechStartGuard()) {
            console.log('🛡️ VAD: Speech start suppressed by guard');
            this.lastSpeechEndTime = now;
            this.speechStartTime = null;
            this.onVADMisfire?.();
            return;
          }
          
          // Debounce: Ignore if too soon after last speech
          if (now - this.lastSpeechEndTime < this.minTimeBetweenUtterances) {
            console.log('⏭️ VAD: Ignoring rapid re-trigger (debounce)');
            return;
          }
          
          this.speechStartTime = now;
          console.log('🗣️ VAD: Speech started');
          this.onSpeechStart?.();
        },

        onSpeechEnd: (audio) => {
          const now = Date.now();
          const duration = this.speechStartTime ? now - this.speechStartTime : 0;
          
          // Filter: Ignore speech shorter than minimum duration
          if (duration < this.minSpeechDuration) {
            console.log(`⏭️ VAD: Ignoring brief sound (${duration}ms < ${this.minSpeechDuration}ms)`);
            this.speechStartTime = null;
            return;
          }
          
          console.log(`🔇 VAD: Speech ended (duration: ${duration}ms)`);
          this.lastSpeechEndTime = now;
          this.speechStartTime = null;
          this.onSpeechEnd?.(audio);
        },

        onVADMisfire: () => {
          console.log('⚠️ VAD: False positive filtered');
          this.onVADMisfire?.();
        },

        onFrameProcessed: (probs) => {
          // Optional: Log speech probability for debugging
          // console.log('Speech probability:', probs.isSpeech.toFixed(3));
        }
      });

      console.log('✅ VAD detector initialized successfully');
      console.log('💡 VAD is FREE and runs locally (no API costs)');
      console.log('🎯 Sesame-style filtering: threshold=0.85, minDuration=300ms, minFrames=5');
      console.log('🛡️ Enhanced false-positive protection for multi-speaker environments');
      return true;

    } catch (error) {
      console.error('❌ VAD initialization failed:', error);
      console.error('Make sure @ricky0123/vad-web is installed:');
      console.error('npm install @ricky0123/vad-web');
      return false;
    }
  }

  /**
   * Start listening for speech
   */
  start() {
    if (!this.vad) {
      console.error('❌ VAD not initialized. Call initialize() first.');
      return;
    }

    this.vad.start();
    this.isListening = true;
    console.log('👂 VAD listening started (always on, no wake word needed)');
  }

  /**
   * Pause listening (but keep VAD loaded)
   */
  pause() {
    if (this.vad) {
      this.vad.pause();
      this.isListening = false;
      console.log('⏸️ VAD listening paused');
    }
  }

  /**
   * Clean up resources
   */
  async destroy() {
    if (this.vad) {
      await this.vad.destroy();
      this.vad = null;
      this.isListening = false;
      console.log('🗑️ VAD destroyed');
    }
  }

  /**
   * Check if VAD is currently listening
   */
  isActive() {
    return this.isListening && this.vad !== null;
  }

  /**
   * Update VAD sensitivity dynamically
   * @param {Object} thresholds - { positive, negative, minFrames }
   */
  updateThresholds(thresholds) {
    console.log('⚙️ Updating VAD thresholds:', thresholds);
    
    // Note: Current VAD library doesn't support runtime threshold updates
    // Would need to recreate VAD instance with new settings
    // Future enhancement: implement threshold hot-swapping
    console.warn('⚠️ Runtime threshold updates not yet supported');
    console.warn('Consider recreating VAD instance with new settings');
  }
}

export default VADDetector;
