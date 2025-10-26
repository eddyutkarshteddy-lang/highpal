/**
 * Statistics Dashboard
 * Display analytics and embeddings status
 */

import React, { useState, useEffect } from 'react';
import './StatisticsDashboard.css';

const StatisticsDashboard = () => {
  const [embeddingsStatus, setEmbeddingsStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [tags, setTags] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_BASE = 'http://localhost:8003';

  useEffect(() => {
    fetchAllStats();
  }, []);

  const fetchAllStats = async () => {
    setLoading(true);
    try {
      // Fetch embeddings status
      const embResponse = await fetch(`${API_BASE}/admin/embeddings/status`);
      const embData = await embResponse.json();
      setEmbeddingsStatus(embData);

      // Fetch content stats
      const statsResponse = await fetch(`${API_BASE}/admin/stats`);
      const statsData = await statsResponse.json();
      setStats(statsData);

      // Fetch available tags
      const tagsResponse = await fetch(`${API_BASE}/admin/tags`);
      const tagsData = await tagsResponse.json();
      setTags(tagsData);

    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateEmbeddings = async () => {
    if (!confirm('Regenerate embeddings for 100 documents?')) return;

    try {
      const response = await fetch(`${API_BASE}/admin/embeddings/regenerate?batch_size=100`, {
        method: 'POST'
      });
      const data = await response.json();
      alert(data.message || 'Regeneration complete!');
      fetchAllStats();
    } catch (err) {
      alert('Regeneration failed: ' + err.message);
    }
  };

  if (loading) {
    return <div className="stats-loading">⏳ Loading statistics...</div>;
  }

  return (
    <div className="statistics-dashboard">
      <div className="stats-header">
        <h2>📊 Statistics Dashboard</h2>
        <button className="refresh-btn" onClick={fetchAllStats}>
          🔄 Refresh
        </button>
      </div>

      {/* Embeddings Status */}
      {embeddingsStatus && (
        <div className="stats-grid">
          <div className="stat-card primary">
            <div className="stat-icon">🧠</div>
            <div className="stat-content">
              <h3>Vector Embeddings</h3>
              <div className="stat-value">
                {embeddingsStatus.embeddings_enabled ? '✅ Enabled' : '❌ Disabled'}
              </div>
              <p className="stat-desc">OpenAI text-embedding-3-small</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-content">
              <h3>Total Documents</h3>
              <div className="stat-value">{embeddingsStatus.total_documents.toLocaleString()}</div>
              <p className="stat-desc">Content chunks in database</p>
            </div>
          </div>

          <div className="stat-card success">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <h3>With Embeddings</h3>
              <div className="stat-value">{embeddingsStatus.with_embeddings.toLocaleString()}</div>
              <p className="stat-desc">{embeddingsStatus.coverage_percentage}% coverage</p>
            </div>
          </div>

          <div className="stat-card warning">
            <div className="stat-icon">⏳</div>
            <div className="stat-content">
              <h3>Without Embeddings</h3>
              <div className="stat-value">{embeddingsStatus.without_embeddings.toLocaleString()}</div>
              {embeddingsStatus.without_embeddings > 0 && (
                <button className="regenerate-btn" onClick={handleRegenerateEmbeddings}>
                  Generate Embeddings
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Coverage Progress Bar */}
      {embeddingsStatus && embeddingsStatus.total_documents > 0 && (
        <div className="coverage-section">
          <h3>Embedding Coverage</h3>
          <div className="progress-bar-large">
            <div
              className="progress-fill-large"
              style={{ width: `${embeddingsStatus.coverage_percentage}%` }}
            />
          </div>
          <p className="coverage-text">
            {embeddingsStatus.with_embeddings} / {embeddingsStatus.total_documents} documents ({embeddingsStatus.coverage_percentage}%)
          </p>
        </div>
      )}

      {/* Content by Exam Type */}
      {stats && stats.by_exam_type && (
        <div className="chart-section">
          <h3>📚 Content by Exam Type</h3>
          <div className="chart-bars">
            {stats.by_exam_type.map((item, index) => (
              <div key={index} className="chart-bar-item">
                <div className="bar-label">{item._id || 'Other'}</div>
                <div className="bar-container">
                  <div
                    className="bar-fill"
                    style={{
                      width: `${(item.count / Math.max(...stats.by_exam_type.map(i => i.count))) * 100}%`
                    }}
                  />
                </div>
                <div className="bar-value">{item.count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Content by Subject */}
      {stats && stats.by_subject && (
        <div className="chart-section">
          <h3>📖 Content by Subject</h3>
          <div className="chart-bars">
            {stats.by_subject.map((item, index) => (
              <div key={index} className="chart-bar-item">
                <div className="bar-label">{item._id || 'Other'}</div>
                <div className="bar-container">
                  <div
                    className="bar-fill subject"
                    style={{
                      width: `${(item.count / Math.max(...stats.by_subject.map(i => i.count))) * 100}%`
                    }}
                  />
                </div>
                <div className="bar-value">{item.count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Tags */}
      {tags && (
        <div className="tags-section">
          <h3>🏷️ Available Tags</h3>
          <div className="tags-grid">
            <div className="tag-group">
              <h4>Exam Types</h4>
              <div className="tag-list">
                {tags.exam_types?.map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
              </div>
            </div>
            <div className="tag-group">
              <h4>Subjects</h4>
              <div className="tag-list">
                {tags.subjects?.map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
              </div>
            </div>
            <div className="tag-group">
              <h4>Topics</h4>
              <div className="tag-list">
                {tags.topics?.slice(0, 10).map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
                {tags.topics?.length > 10 && (
                  <span className="tag">+{tags.topics.length - 10} more</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StatisticsDashboard;
