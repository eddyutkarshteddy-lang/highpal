import React from 'react';
import './SearchResults.css';

const SearchResults = ({ results, query, isLoading, onAskQuestion }) => {
  const getScoreColor = (score) => {
    if (score >= 0.8) return 'high-relevance';    // Green
    if (score >= 0.5) return 'medium-relevance';  // Yellow  
    return 'low-relevance';                       // Red
  };

  const getScoreIcon = (score) => {
    if (score >= 0.8) return '🟢';
    if (score >= 0.5) return '🟡';
    return '🔴';
  };

  const formatScore = (score) => {
    return Math.round(score * 100); // Convert 0.89 → 89%
  };

  const formatFileSize = (size) => {
    if (!size) return 'Unknown size';
    if (size > 1024 * 1024) {
      return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    }
    if (size > 1024) {
      return `${(size / 1024).toFixed(1)} KB`;
    }
    return `${size} bytes`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown date';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  const handleAskQuestion = (result) => {
    const question = `Tell me more about the content in ${result.filename}`;
    if (onAskQuestion) {
      onAskQuestion(question, result);
    }
  };

  const handleViewDocument = (result) => {
    // Future: Open document viewer
    console.log('View document:', result.filename);
  };

  if (isLoading) {
    return (
      <div className="search-results loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Searching documents...</p>
        </div>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="search-results empty">
        <div className="empty-state">
          <span className="empty-icon">🔍</span>
          <h3>No results found</h3>
          <p>Try different keywords or upload more documents</p>
        </div>
      </div>
    );
  }

  // Group results by relevance
  const highRelevance = results.filter(r => r.score >= 0.8);
  const mediumRelevance = results.filter(r => r.score >= 0.5 && r.score < 0.8);
  const lowRelevance = results.filter(r => r.score < 0.5);

  return (
    <div className="search-results">
      <div className="results-header">
        <h2>Search Results for "{query}"</h2>
        <div className="results-stats">
          <span className="total-count">{results.length} documents found</span>
          {highRelevance.length > 0 && (
            <span className="relevance-stat high">
              🟢 {highRelevance.length} highly relevant
            </span>
          )}
          {mediumRelevance.length > 0 && (
            <span className="relevance-stat medium">
              🟡 {mediumRelevance.length} moderately relevant
            </span>
          )}
          {lowRelevance.length > 0 && (
            <span className="relevance-stat low">
              🔴 {lowRelevance.length} weakly relevant
            </span>
          )}
        </div>
      </div>
      
      <div className="results-list">
        {results.map((result, index) => (
          <div key={index} className="result-card">
            <div className="result-header">
              <div className="filename">
                {getScoreIcon(result.score)} 
                <span className="file-name">{result.filename || 'Unknown Document'}</span>
                <span className="file-type-badge">
                  {result.file_type?.split('/')[1]?.toUpperCase() || 'DOC'}
                </span>
              </div>
              <div className={`relevance-score ${getScoreColor(result.score)}`}>
                {formatScore(result.score)}% Match
              </div>
            </div>
            
            <div className="result-content">
              <p>
                {result.content?.substring(0, 300) || 'No preview available'}
                {result.content?.length > 300 && '...'}
              </p>
            </div>
            
            <div className="result-metadata">
              <span className="metadata-item">
                📄 {formatFileSize(result.file_size)}
              </span>
              <span className="metadata-item">
                📅 {formatDate(result.upload_date)}
              </span>
              {result.tags && result.tags.length > 0 && (
                <span className="metadata-item">
                  🏷️ {result.tags.join(', ')}
                </span>
              )}
              {result.search_method && (
                <span className="metadata-item method">
                  🔍 {result.search_method}
                </span>
              )}
            </div>
            
            <div className="result-actions">
              <button 
                className="ask-button primary"
                onClick={() => handleAskQuestion(result)}
              >
                💬 Ask about this document
              </button>
              <button 
                className="view-button secondary"
                onClick={() => handleViewDocument(result)}
              >
                👁️ View Details
              </button>
            </div>
          </div>
        ))}
      </div>
      
      {results.length > 5 && (
        <div className="results-footer">
          <p className="search-tip">
            💡 <strong>Tip:</strong> Focus on results with higher relevance scores (🟢) for the most accurate information.
          </p>
        </div>
      )}
    </div>
  );
};

export default SearchResults;
