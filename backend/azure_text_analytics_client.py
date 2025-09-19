"""
Azure Text Analytics Client for HighPal Emotional Intelligence
Handles sentiment analysis and emotion detection from text and speech transcripts
"""

import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AzureTextAnalyticsClient:
    """Azure Text Analytics client for emotion detection and sentiment analysis"""
    
    def __init__(self):
        """Initialize Azure Text Analytics client"""
        self.key = os.getenv('AZURE_TEXT_ANALYTICS_KEY')
        self.endpoint = os.getenv('AZURE_TEXT_ANALYTICS_ENDPOINT')
        
        if not self.key or self.key == 'your_azure_text_analytics_key_here':
            logger.warning("Azure Text Analytics key not configured. Using fallback emotion detection.")
            self.client = None
        else:
            try:
                credential = AzureKeyCredential(self.key)
                self.client = TextAnalyticsClient(endpoint=self.endpoint, credential=credential)
                logger.info("Azure Text Analytics client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Text Analytics client: {e}")
                self.client = None
    
    def analyze_sentiment_and_emotions(self, text: str) -> Dict:
        """
        Analyze sentiment and emotions from text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict: Emotional analysis results
        """
        if not self.client:
            # Fallback emotion detection when Azure Text Analytics is not available
            return self._fallback_emotion_detection(text)
        
        try:
            # Analyze sentiment
            sentiment_response = self.client.analyze_sentiment(documents=[text])[0]
            
            # Analyze key phrases for emotional context
            key_phrases_response = self.client.extract_key_phrases(documents=[text])[0]
            
            # Process results
            emotional_analysis = {
                "sentiment": {
                    "overall": sentiment_response.sentiment,
                    "confidence_scores": {
                        "positive": sentiment_response.confidence_scores.positive,
                        "neutral": sentiment_response.confidence_scores.neutral,
                        "negative": sentiment_response.confidence_scores.negative
                    }
                },
                "emotional_indicators": {
                    "stress_level": self._calculate_stress_level(sentiment_response),
                    "confidence_level": self._calculate_confidence_level(sentiment_response, key_phrases_response),
                    "engagement_level": self._calculate_engagement_level(key_phrases_response)
                },
                "key_phrases": key_phrases_response.key_phrases if not key_phrases_response.is_error else [],
                "emotional_state": self._determine_emotional_state(sentiment_response),
                "suggested_response_tone": self._suggest_response_tone(sentiment_response)
            }
            
            logger.info(f"Emotional analysis completed: {emotional_analysis['emotional_state']}")
            return emotional_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing emotions: {e}")
            return self._fallback_emotion_detection(text)
    
    def _calculate_stress_level(self, sentiment_response) -> str:
        """Calculate stress level based on sentiment analysis"""
        negative_score = sentiment_response.confidence_scores.negative
        
        if negative_score > 0.7:
            return "high"
        elif negative_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_confidence_level(self, sentiment_response, key_phrases_response) -> str:
        """Calculate confidence level based on sentiment and key phrases"""
        positive_score = sentiment_response.confidence_scores.positive
        
        # Check for confidence-related key phrases
        confidence_indicators = ["confident", "sure", "certain", "believe", "understand", "know"]
        uncertainty_indicators = ["confused", "unsure", "maybe", "don't know", "not sure"]
        
        key_phrases = key_phrases_response.key_phrases if not key_phrases_response.is_error else []
        
        has_confidence_phrases = any(phrase.lower() in " ".join(key_phrases).lower() for phrase in confidence_indicators)
        has_uncertainty_phrases = any(phrase.lower() in " ".join(key_phrases).lower() for phrase in uncertainty_indicators)
        
        if positive_score > 0.6 and has_confidence_phrases:
            return "high"
        elif has_uncertainty_phrases or positive_score < 0.3:
            return "low"
        else:
            return "medium"
    
    def _calculate_engagement_level(self, key_phrases_response) -> str:
        """Calculate engagement level based on key phrases"""
        key_phrases = key_phrases_response.key_phrases if not key_phrases_response.is_error else []
        
        engagement_indicators = ["question", "why", "how", "explain", "more", "interested", "curious"]
        
        engagement_count = sum(1 for phrase in key_phrases 
                             if any(indicator in phrase.lower() for indicator in engagement_indicators))
        
        if engagement_count >= 2:
            return "high"
        elif engagement_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _determine_emotional_state(self, sentiment_response) -> str:
        """Determine overall emotional state"""
        sentiment = sentiment_response.sentiment
        confidence_scores = sentiment_response.confidence_scores
        
        if sentiment == "positive" and confidence_scores.positive > 0.7:
            return "confident_and_positive"
        elif sentiment == "positive":
            return "positive"
        elif sentiment == "negative" and confidence_scores.negative > 0.7:
            return "stressed_or_frustrated"
        elif sentiment == "negative":
            return "slightly_negative"
        else:
            return "neutral"
    
    def _suggest_response_tone(self, sentiment_response) -> str:
        """Suggest appropriate response tone"""
        sentiment = sentiment_response.sentiment
        negative_score = sentiment_response.confidence_scores.negative
        
        if sentiment == "negative" and negative_score > 0.7:
            return "calm_and_supportive"
        elif sentiment == "negative":
            return "encouraging"
        elif sentiment == "positive":
            return "enthusiastic"
        else:
            return "neutral_and_helpful"
    
    def _fallback_emotion_detection(self, text: str) -> Dict:
        """
        Fallback emotion detection when Azure Text Analytics is not available
        Uses simple keyword-based analysis
        """
        text_lower = text.lower()
        
        # Simple keyword-based emotion detection
        stress_keywords = ["stressed", "worried", "anxious", "nervous", "panic", "overwhelmed"]
        positive_keywords = ["good", "great", "excellent", "understand", "clear", "confident"]
        negative_keywords = ["confused", "difficult", "hard", "don't understand", "stuck"]
        
        stress_level = "high" if any(keyword in text_lower for keyword in stress_keywords) else "low"
        
        if any(keyword in text_lower for keyword in positive_keywords):
            sentiment = "positive"
            emotional_state = "confident_and_positive"
            response_tone = "enthusiastic"
        elif any(keyword in text_lower for keyword in negative_keywords):
            sentiment = "negative"
            emotional_state = "confused_or_frustrated"
            response_tone = "calm_and_supportive"
        else:
            sentiment = "neutral"
            emotional_state = "neutral"
            response_tone = "neutral_and_helpful"
        
        return {
            "sentiment": {
                "overall": sentiment,
                "confidence_scores": {
                    "positive": 0.5 if sentiment == "positive" else 0.3,
                    "neutral": 0.4,
                    "negative": 0.5 if sentiment == "negative" else 0.3
                }
            },
            "emotional_indicators": {
                "stress_level": stress_level,
                "confidence_level": "medium",
                "engagement_level": "medium"
            },
            "key_phrases": [],
            "emotional_state": emotional_state,
            "suggested_response_tone": response_tone,
            "fallback_mode": True
        }

# Example usage
if __name__ == "__main__":
    client = AzureTextAnalyticsClient()
    
    # Test with sample student input
    test_texts = [
        "I'm really stressed about the JEE exam and don't understand calculus",
        "I feel confident about this topic now, thank you for explaining",
        "Can you explain more about photosynthesis? I'm curious about the process"
    ]
    
    for text in test_texts:
        print(f"\nAnalyzing: '{text}'")
        result = client.analyze_sentiment_and_emotions(text)
        print(f"Emotional State: {result['emotional_state']}")
        print(f"Stress Level: {result['emotional_indicators']['stress_level']}")
        print(f"Suggested Response Tone: {result['suggested_response_tone']}")
