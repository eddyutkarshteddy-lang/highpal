import React, { useState, useEffect } from 'react';
import './TrainingInfo.css';

const TrainingInfo = () => {
  const [trainingData, setTrainingData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTrainingInfo, setShowTrainingInfo] = useState(false);

  const loadTrainingInfo = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8003/training_info');
      if (response.ok) {
        const data = await response.json();
        setTrainingData(data);
      } else {
        console.warn('Failed to load training info:', response.status);
      }
    } catch (error) {
      console.error('Error loading training info:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (showTrainingInfo) {
      loadTrainingInfo();
    }
  }, [showTrainingInfo]);

  const formatCategory = (category) => {
    return category.charAt(0).toUpperCase() + category.slice(1);
  };

  const getCategoryEmoji = (category) => {
    const emojiMap = {
      'academic': '🎓',
      'research': '🔬',
      'documentation': '📚',
      'faq': '❓',
      'technical': '⚙️',
      'general': '📄',
      'product': '📦',
      'guide': '📖'
    };
    return emojiMap[category.toLowerCase()] || '📄';
  };

  return (
    <div className="training-info-container">
      {/* Toggle Button */}
      <button 
        className="training-info-toggle"
        onClick={() => setShowTrainingInfo(!showTrainingInfo)}
        title="View training documents that make Pal smarter"
      >
        🧠 {showTrainingInfo ? 'Hide' : 'Show'} Training Data
      </button>

      {/* Training Info Panel */}
      {showTrainingInfo && (
        <div className="training-info-panel">
          <div className="training-info-header">
            <h3>🧠 Pal's Knowledge Base</h3>
            <p>Documents that make Pal smarter and more helpful</p>
          </div>

          {loading ? (
            <div className="training-loading">
              <div className="loading-spinner"></div>
              <p>Loading training data...</p>
            </div>
          ) : trainingData ? (
            <div className="training-content">
              {/* Statistics */}
              <div className="training-stats">
                <div className="stat-item">
                  <span className="stat-number">{trainingData.total_training_documents}</span>
                  <span className="stat-label">Training Documents</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">{Object.keys(trainingData.categories || {}).length}</span>
                  <span className="stat-label">Categories</span>
                </div>
                <div className="stat-item">
                  <span className="stat-status">{trainingData.status}</span>
                  <span className="stat-label">Status</span>
                </div>
              </div>

              {/* Categories */}
              {trainingData.categories && Object.keys(trainingData.categories).length > 0 && (
                <div className="training-categories">
                  <h4>📂 Knowledge Categories</h4>
                  <div className="categories-grid">
                    {Object.entries(trainingData.categories).map(([category, count]) => (
                      <div key={category} className="category-item">
                        <span className="category-emoji">{getCategoryEmoji(category)}</span>
                        <span className="category-name">{formatCategory(category)}</span>
                        <span className="category-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sample Documents */}
              {trainingData.sample_documents && trainingData.sample_documents.length > 0 && (
                <div className="training-samples">
                  <h4>📄 Sample Training Documents</h4>
                  <div className="samples-list">
                    {trainingData.sample_documents.map((doc, index) => (
                      <div key={index} className="sample-doc">
                        <div className="sample-header">
                          <span className="sample-emoji">{getCategoryEmoji(doc.category)}</span>
                          <span className="sample-filename">{doc.filename}</span>
                          <span className="sample-category">{formatCategory(doc.category)}</span>
                        </div>
                        <p className="sample-preview">{doc.content_preview}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer Info */}
              <div className="training-footer">
                <p>🔄 Last updated: {new Date(trainingData.last_updated).toLocaleString()}</p>
                <p>💡 These documents help Pal provide accurate and helpful responses to your questions.</p>
              </div>
            </div>
          ) : (
            <div className="training-error">
              <p>❌ Unable to load training data</p>
              <button onClick={loadTrainingInfo} className="retry-button">
                🔄 Retry
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TrainingInfo;
