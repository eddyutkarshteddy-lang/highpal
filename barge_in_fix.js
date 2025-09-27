// Simple and working barge-in detection - copy this into App.jsx

// Replace the entire checkAudioLevel function with this clean version:
const checkAudioLevel = () => {
  if (!audioMonitoringRef.current) {
    console.log('⏹️ Audio monitoring stopped');
    return;
  }
  
  analyser.getByteFrequencyData(dataArray);
  
  // Calculate average volume
  let sum = 0;
  for (let i = 0; i < bufferLength; i++) {
    sum += dataArray[i];
  }
  const average = sum / bufferLength;
  
  // Log audio levels
  console.log('🎤 Audio level:', Math.round(average));
  
  // SIMPLE RULE: If sound level > 0.8, interrupt immediately
  if (average > 0.8) {
    console.log('🛑 INTERRUPTION! Level:', Math.round(average));
    
    // Stop everything and start listening
    bargeInDetectedRef.current = true;
    stopCurrentAudio();
    stopBargeInDetection();
    setVoiceState('listening');
    
    // Capture the interruption
    setTimeout(async () => {
      try {
        const userInput = await startContinuousListening();
        if (userInput && userInput.trim().length > 0) {
          setVoiceState('processing');
          const aiResponse = await getAIResponse(userInput);
          setVoiceState('speaking');
          await playAIResponse(aiResponse);
        }
        bargeInDetectedRef.current = false;
        setVoiceState('listening');
      } catch (error) {
        console.log('Error:', error);
        bargeInDetectedRef.current = false;
        setVoiceState('listening');
      }
    }, 200);
    
    return;
  }
  
  // Continue monitoring
  requestAnimationFrame(checkAudioLevel);
};