/**
 * Interrupt Manager
 * 
 * Manages conversation state and handles interruptions
 * Coordinates between VAD detection, AI audio, and user speech
 * 
 * States:
 * - IDLE: No activity, VAD monitoring
 * - USER_SPEAKING: User is talking
 * - PROCESSING: AI is thinking
 * - AI_SPEAKING: AI is responding (VAD still monitoring for interrupts)
 * 
 * Features:
 * - Smooth audio fade-out on interrupt
 * - State transition logging
 * - Interrupt detection during AI speech
 */

const States = {
  IDLE: 'IDLE',
  USER_SPEAKING: 'USER_SPEAKING',
  PROCESSING: 'PROCESSING',
  AI_SPEAKING: 'AI_SPEAKING'
};

class InterruptManager {
  constructor() {
    this.state = States.IDLE;
    this.currentAudio = null;
    this.fadeInterval = null;
    
    // Callbacks
    this.onInterruptDetected = null;
    this.onSpeechStart = null;
    this.onSpeechEnd = null;
    this.onStateChange = null;
  }

  /**
   * Handle speech detected by VAD
   */
  handleSpeechDetected() {
    const previousState = this.state;
    console.log(`🎯 Speech detected in state: ${this.state}`);
    
    if (this.state === States.AI_SPEAKING) {
      console.log('⚡ INTERRUPTING AI!');
      
      // Stop AI audio with smooth fade
      this.fadeOutAudio(this.currentAudio, 300);
      
      // Update state
      this.setState(States.USER_SPEAKING);
      
      // Notify interrupt detected
      this.onInterruptDetected?.();
      
    } else if (this.state === States.IDLE) {
      console.log('🎤 User started conversation');
      this.setState(States.USER_SPEAKING);
      this.onSpeechStart?.();
      
    } else if (this.state === States.USER_SPEAKING) {
      console.log('👂 User still speaking');
      // Already in speaking state, do nothing
      
    } else if (this.state === States.PROCESSING) {
      console.log('⚡ User interrupted during processing');
      this.setState(States.USER_SPEAKING);
      this.onInterruptDetected?.();
    }
  }

  /**
   * Handle speech ended by VAD
   */
  handleSpeechEnded() {
    console.log(`🔇 Speech ended in state: ${this.state}`);
    
    if (this.state === States.USER_SPEAKING) {
      this.setState(States.PROCESSING);
      this.onSpeechEnd?.();
    }
  }

  /**
   * Set AI speaking state (call when AI starts playing audio)
   */
  setAISpeaking(audioElement) {
    this.setState(States.AI_SPEAKING);
    this.currentAudio = audioElement;
    console.log('🗣️ AI speaking (VAD monitoring for interrupts)');
  }

  /**
   * Set idle state (call when AI finishes speaking)
   */
  setIdle() {
    this.setState(States.IDLE);
    this.currentAudio = null;
    console.log('✅ Back to idle (VAD monitoring)');
  }

  /**
   * Set processing state (call when sending to GPT)
   */
  setProcessing() {
    this.setState(States.PROCESSING);
    console.log('🤔 Processing user input...');
  }

  /**
   * Update state and notify listeners
   */
  setState(newState) {
    const oldState = this.state;
    this.state = newState;
    
    if (oldState !== newState) {
      console.log(`🔄 State transition: ${oldState} → ${newState}`);
      this.onStateChange?.(newState, oldState);
    }
  }

  /**
   * Get current state
   */
  getState() {
    return this.state;
  }

  /**
   * Check if AI is currently speaking
   */
  isAISpeaking() {
    return this.state === States.AI_SPEAKING;
  }

  /**
   * Check if user is currently speaking
   */
  isUserSpeaking() {
    return this.state === States.USER_SPEAKING;
  }

  /**
   * Smoothly fade out audio element
   * @param {HTMLAudioElement} audio - Audio element to fade out
   * @param {number} duration - Fade duration in milliseconds
   */
  fadeOutAudio(audio, duration = 300) {
    if (!audio) {
      console.log('⚠️ No audio element to fade out');
      return;
    }

    // Clear any existing fade
    if (this.fadeInterval) {
      clearInterval(this.fadeInterval);
    }

    const startVolume = audio.volume;
    const steps = Math.floor(duration / 10); // Update every 10ms
    const volumeStep = startVolume / steps;

    console.log(`🔉 Fading out audio from ${startVolume.toFixed(2)} over ${duration}ms`);

    this.fadeInterval = setInterval(() => {
      audio.volume = Math.max(0, audio.volume - volumeStep);
      
      if (audio.volume <= 0.01) {
        clearInterval(this.fadeInterval);
        this.fadeInterval = null;
        audio.pause();
        audio.currentTime = 0;
        audio.volume = startVolume; // Reset for next play
        console.log('✅ Audio faded out and stopped');
      }
    }, 10);
  }

  /**
   * Immediately stop audio (no fade)
   */
  stopAudioImmediately(audio) {
    if (audio) {
      if (this.fadeInterval) {
        clearInterval(this.fadeInterval);
        this.fadeInterval = null;
      }
      audio.pause();
      audio.currentTime = 0;
      console.log('⏹️ Audio stopped immediately');
    }
  }

  /**
   * Clean up resources
   */
  destroy() {
    if (this.fadeInterval) {
      clearInterval(this.fadeInterval);
      this.fadeInterval = null;
    }
    this.currentAudio = null;
    this.state = States.IDLE;
    console.log('🗑️ Interrupt manager destroyed');
  }
}

// Export States for external use
export { States };
export default InterruptManager;
