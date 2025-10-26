/**
 * Content Management Component
 * Search, filter, and manage uploaded content
 */

import React, { useState, useEffect } from 'react';
import './ContentManagement.css';

const ContentManagement = () => {
  const [query, setQuery] = useState('');
  const [examFilter, setExamFilter] = useState('');
  const [subjectFilter, setSubjectFilter] = useState('');
  const [results, setResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMethod, setSearchMethod] = useState('semantic');
  const [viewMode, setViewMode] = useState('documents'); // 'documents' or 'search'

  const API_BASE = 'http://localhost:8003';

  // Load uploaded documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/admin/documents`);
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Load documents error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (fileHash, filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?\n\nThis will permanently remove all ${documents.find(d => d.file_hash === fileHash)?.total_chunks || 0} chunks from the knowledge base.`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/admin/documents/${fileHash}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Delete failed');
      }

      const data = await response.json();
      alert(`✅ Successfully deleted ${data.deleted_chunks} chunks`);
      
      // Reload documents list
      await loadDocuments();
    } catch (err) {
      console.error('Delete error:', err);
      alert('❌ Failed to delete document: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      setViewMode('documents');
      return;
    }

    setViewMode('search');
    setLoading(true);
    try {
      const params = new URLSearchParams({
        query: query.trim(),
        use_semantic: searchMethod === 'semantic',
        limit: 20
      });
      
      if (examFilter) params.append('exam_type', examFilter);
      if (subjectFilter) params.append('subject', subjectFilter);

      const response = await fetch(`${API_BASE}/admin/content/search?${params}`);
      const data = await response.json();

      setResults(data.results || []);
    } catch (err) {
      console.error('Search error:', err);
      alert('Search failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="content-management">
      <div className="management-header">
        <h2>📚 Content Management</h2>
        <p>Search and manage uploaded educational content</p>
      </div>

      {/* Search Bar */}
      <div className="search-section">
        <div className="search-bar">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search content... (e.g., 'thermodynamics', 'calculus')"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? '⏳' : '🔍'} Search
          </button>
        </div>

        <div className="filters">
          <select value={examFilter} onChange={(e) => setExamFilter(e.target.value)}>
            <option value="">All Exams</option>
            <option value="JEE">JEE</option>
            <option value="NEET">NEET</option>
            <option value="CAT">CAT</option>
            <option value="GATE">GATE</option>
          </select>

          <select value={subjectFilter} onChange={(e) => setSubjectFilter(e.target.value)}>
            <option value="">All Subjects</option>
            <option value="Physics">Physics</option>
            <option value="Chemistry">Chemistry</option>
            <option value="Mathematics">Mathematics</option>
            <option value="Biology">Biology</option>
          </select>

          <select value={searchMethod} onChange={(e) => setSearchMethod(e.target.value)}>
            <option value="semantic">🧠 Semantic Search</option>
            <option value="keyword">🔤 Keyword Search</option>
          </select>
        </div>
      </div>

      {/* Results */}
      {viewMode === 'documents' && documents.length > 0 && (
        <div className="results-section">
          <div className="results-header">
            <h3>📄 Uploaded Documents ({documents.length})</h3>
            <p>Click on a document to see its chunks</p>
          </div>

          <div className="documents-list">
            {documents.map((doc, index) => (
              <div key={doc.file_hash || index} className="document-card">
                <div className="doc-header">
                  <span className="doc-icon">📄</span>
                  <div className="doc-title">
                    <h4>{doc.filename || 'Unknown'}</h4>
                    <span className="doc-meta">
                      {doc.total_chunks} chunks • {doc.has_embeddings} embedded • 
                      Uploaded {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="doc-body">
                  <div className="doc-tags">
                    <span className="tag">
                      📚 {Array.isArray(doc.exam_types) ? doc.exam_types.join(', ') : doc.exam_types || 'N/A'}
                    </span>
                    <span className="tag">📖 {doc.subject || 'N/A'}</span>
                    {doc.topic && <span className="tag">🎯 {doc.topic}</span>}
                  </div>

                  <div className="doc-stats">
                    <div className="stat">
                      <span className="stat-label">Coverage:</span>
                      <span className="stat-value">
                        {((doc.has_embeddings / doc.total_chunks) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Admin:</span>
                      <span className="stat-value">{doc.admin_id || 'Unknown'}</span>
                    </div>
                  </div>

                  <div className="doc-actions">
                    <button 
                      className="delete-btn"
                      onClick={() => handleDeleteDocument(doc.file_hash, doc.filename)}
                      disabled={loading}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {viewMode === 'search' && results.length > 0 && (
        <div className="results-section">
          <div className="results-header">
            <h3>{results.length} Results Found</h3>
            <button onClick={() => { setQuery(''); setViewMode('documents'); }} className="back-btn">
              ← Back to Documents
            </button>
          </div>

          <div className="content-table">
            {results.map((item, index) => (
              <div key={item._id || index} className="content-card">
                <div className="card-header">
                  <span className="card-index">#{index + 1}</span>
                  {item.has_embedding && <span className="embedding-badge">🧠 Embedded</span>}
                  {item.similarity && (
                    <span className="similarity-score">
                      {(item.similarity * 100).toFixed(1)}% match
                    </span>
                  )}
                </div>

                <div className="card-body">
                  <div className="card-meta">
                    <span className="meta-item">
                      📚 {Array.isArray(item.tags?.exam_type) 
                        ? item.tags.exam_type.join(', ') 
                        : item.tags?.exam_type || 'N/A'}
                    </span>
                    <span className="meta-item">
                      📖 {item.tags?.subject || 'N/A'}
                    </span>
                    {item.tags?.topic && (
                      <span className="meta-item">🎯 {item.tags.topic}</span>
                    )}
                  </div>

                  <div className="card-content">
                    <p>{item.content?.substring(0, 200)}...</p>
                  </div>

                  <div className="card-footer">
                    <span className="source-info">
                      {item.source_filename || item.source_url || 'Unknown source'}
                    </span>
                    <span className="chunk-info">
                      Chunk {item.chunk_index + 1}/{item.total_chunks}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {results.length === 0 && query && !loading && (
        <div className="no-results">
          <p>No results found. Try different keywords or filters.</p>
        </div>
      )}
    </div>
  );
};

export default ContentManagement;
