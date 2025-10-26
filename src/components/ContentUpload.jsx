/**
 * Content Upload Component
 * Interface for uploading PDFs (file or URL) with tagging
 */

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './ContentUpload.css';

const EXAM_TYPES = ['JEE', 'NEET', 'CAT', 'GATE', 'UPSC', 'SSC', 'Banking', 'Railways', 'State_PSC', 'NDA', 'CDS', 'CLAT', 'AIIMS', 'JIPMER', 'Other'];
const DIFFICULTIES = ['beginner', 'intermediate', 'advanced'];
const CLASSES = ['9th', '10th', '11th', '12th', 'Undergraduate', 'Graduate', 'Other'];
const LANGUAGES = ['English', 'Hindi', 'Tamil', 'Telugu', 'Bengali', 'Marathi', 'Other'];

const ContentUpload = () => {
  const { currentUser } = useAuth();
  const [uploadType, setUploadType] = useState('file'); // 'file' or 'url' or 'bulk'
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [bulkUrls, setBulkUrls] = useState('');
  
  // Tags
  const [selectedExamTypes, setSelectedExamTypes] = useState([]);
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [chapter, setChapter] = useState('');
  const [difficulty, setDifficulty] = useState('intermediate');
  const [classLevel, setClassLevel] = useState('');
  const [language, setLanguage] = useState('English');
  const [description, setDescription] = useState('');
  
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const API_BASE = 'http://localhost:8003';

  const handleExamTypeToggle = (examType) => {
    setSelectedExamTypes(prev =>
      prev.includes(examType)
        ? prev.filter(e => e !== examType)
        : [...prev, examType]
    );
  };

  const validateForm = () => {
    if (selectedExamTypes.length === 0) {
      setError('Please select at least one exam type');
      return false;
    }
    if (!subject.trim()) {
      setError('Please enter a subject');
      return false;
    }
    if (uploadType === 'file' && !file) {
      setError('Please select a file');
      return false;
    }
    if (uploadType === 'url' && !url.trim()) {
      setError('Please enter a URL');
      return false;
    }
    if (uploadType === 'bulk' && !bulkUrls.trim()) {
      setError('Please enter URLs (one per line)');
      return false;
    }
    return true;
  };

  const handleFileUpload = async () => {
    if (!validateForm()) return;

    setUploading(true);
    setError('');
    setProgress(10);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('tags', JSON.stringify({
        exam_type: selectedExamTypes,
        subject: subject.trim(),
        topic: topic.trim() || undefined,
        chapter: chapter.trim() || undefined,
        difficulty,
        class: classLevel || undefined,
        language
      }));
      formData.append('admin_id', currentUser.email);
      formData.append('description', description.trim());

      setProgress(30);

      const response = await fetch(`${API_BASE}/admin/train/upload`, {
        method: 'POST',
        body: formData
      });

      setProgress(80);

      const data = await response.json();

      if (response.ok && data.success) {
        setResult({
          type: 'success',
          message: `✅ Successfully uploaded! Created ${data.chunks_created} content chunks with embeddings.`,
          details: data
        });
        // Reset form
        setFile(null);
        setDescription('');
      } else {
        throw new Error(data.error || 'Upload failed');
      }

      setProgress(100);
    } catch (err) {
      setError(err.message);
      setResult({ type: 'error', message: `❌ ${err.message}` });
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const handleUrlUpload = async () => {
    if (!validateForm()) return;

    setUploading(true);
    setError('');
    setProgress(10);

    try {
      const payload = {
        url: url.trim(),
        tags: {
          exam_type: selectedExamTypes,
          subject: subject.trim(),
          topic: topic.trim() || undefined,
          chapter: chapter.trim() || undefined,
          difficulty,
          class: classLevel || undefined,
          language
        },
        admin_id: currentUser.email,
        description: description.trim()
      };

      setProgress(30);

      const response = await fetch(`${API_BASE}/admin/train/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      setProgress(80);

      const data = await response.json();

      if (response.ok && data.success) {
        setResult({
          type: 'success',
          message: `✅ Successfully processed URL! Created ${data.chunks_created} content chunks with embeddings.`,
          details: data
        });
        setUrl('');
        setDescription('');
      } else {
        throw new Error(data.error || 'Upload failed');
      }

      setProgress(100);
    } catch (err) {
      setError(err.message);
      setResult({ type: 'error', message: `❌ ${err.message}` });
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const handleBulkUpload = async () => {
    if (!validateForm()) return;

    setUploading(true);
    setError('');
    setProgress(10);

    try {
      const urls = bulkUrls.split('\n').map(line => line.trim()).filter(Boolean);
      
      if (urls.length === 0) {
        throw new Error('No valid URLs found');
      }

      const uploads = urls.map(url => ({
        url,
        tags: {
          exam_type: selectedExamTypes,
          subject: subject.trim(),
          topic: topic.trim() || undefined,
          chapter: chapter.trim() || undefined,
          difficulty,
          class: classLevel || undefined,
          language
        },
        description: description.trim()
      }));

      setProgress(20);

      const response = await fetch(`${API_BASE}/admin/train/bulk_urls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uploads,
          admin_id: currentUser.email
        })
      });

      setProgress(90);

      const data = await response.json();

      if (response.ok) {
        setResult({
          type: 'success',
          message: `✅ Bulk upload complete! ${data.successful} successful, ${data.failed} failed out of ${data.total} URLs.`,
          details: data
        });
        setBulkUrls('');
        setDescription('');
      } else {
        throw new Error('Bulk upload failed');
      }

      setProgress(100);
    } catch (err) {
      setError(err.message);
      setResult({ type: 'error', message: `❌ ${err.message}` });
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (uploadType === 'file') {
      handleFileUpload();
    } else if (uploadType === 'url') {
      handleUrlUpload();
    } else if (uploadType === 'bulk') {
      handleBulkUpload();
    }
  };

  return (
    <div className="content-upload">
      <div className="upload-header">
        <h2>📤 Upload Educational Content</h2>
        <p>Upload PDFs with tags for exam preparation. Embeddings will be generated automatically.</p>
      </div>

      {result && (
        <div className={`result-box ${result.type}`}>
          <p>{result.message}</p>
          {result.details && (
            <details>
              <summary>View Details</summary>
              <pre>{JSON.stringify(result.details, null, 2)}</pre>
            </details>
          )}
        </div>
      )}

      {error && (
        <div className="error-box">
          ⚠️ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="upload-form">
        {/* Upload Type Selection */}
        <div className="form-section">
          <label className="section-label">Upload Method</label>
          <div className="upload-type-selector">
            <button
              type="button"
              className={`type-btn ${uploadType === 'file' ? 'active' : ''}`}
              onClick={() => setUploadType('file')}
            >
              📄 File Upload
            </button>
            <button
              type="button"
              className={`type-btn ${uploadType === 'url' ? 'active' : ''}`}
              onClick={() => setUploadType('url')}
            >
              🔗 URL
            </button>
            <button
              type="button"
              className={`type-btn ${uploadType === 'bulk' ? 'active' : ''}`}
              onClick={() => setUploadType('bulk')}
            >
              📦 Bulk URLs
            </button>
          </div>
        </div>

        {/* File/URL Input */}
        <div className="form-section">
          {uploadType === 'file' && (
            <div className="file-upload-area">
              <label className="file-label">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                  disabled={uploading}
                />
                <div className="file-upload-box">
                  {file ? (
                    <>
                      <span className="file-icon">📄</span>
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                    </>
                  ) : (
                    <>
                      <span className="upload-icon">⬆️</span>
                      <span>Click to select PDF file</span>
                    </>
                  )}
                </div>
              </label>
            </div>
          )}

          {uploadType === 'url' && (
            <div className="form-group">
              <label>PDF URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/document.pdf"
                disabled={uploading}
                required
              />
            </div>
          )}

          {uploadType === 'bulk' && (
            <div className="form-group">
              <label>PDF URLs (one per line)</label>
              <textarea
                value={bulkUrls}
                onChange={(e) => setBulkUrls(e.target.value)}
                placeholder="https://example.com/doc1.pdf&#10;https://example.com/doc2.pdf&#10;https://example.com/doc3.pdf"
                rows={6}
                disabled={uploading}
                required
              />
              <small>{bulkUrls.split('\n').filter(Boolean).length} URLs</small>
            </div>
          )}
        </div>

        {/* Tags Section */}
        <div className="form-section">
          <label className="section-label">Content Tags (Required)</label>
          
          {/* Exam Types */}
          <div className="form-group">
            <label>Exam Type(s) *</label>
            <div className="exam-type-grid">
              {EXAM_TYPES.map(exam => (
                <button
                  key={exam}
                  type="button"
                  className={`exam-tag ${selectedExamTypes.includes(exam) ? 'selected' : ''}`}
                  onClick={() => handleExamTypeToggle(exam)}
                  disabled={uploading}
                >
                  {exam}
                </button>
              ))}
            </div>
          </div>

          {/* Subject and Topic */}
          <div className="form-row">
            <div className="form-group">
              <label>Subject *</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g., Physics, Mathematics"
                disabled={uploading}
                required
              />
            </div>
            <div className="form-group">
              <label>Topic</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., Thermodynamics"
                disabled={uploading}
              />
            </div>
          </div>

          {/* Chapter and Difficulty */}
          <div className="form-row">
            <div className="form-group">
              <label>Chapter</label>
              <input
                type="text"
                value={chapter}
                onChange={(e) => setChapter(e.target.value)}
                placeholder="e.g., Heat Transfer"
                disabled={uploading}
              />
            </div>
            <div className="form-group">
              <label>Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                disabled={uploading}
              >
                {DIFFICULTIES.map(d => (
                  <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Class and Language */}
          <div className="form-row">
            <div className="form-group">
              <label>Class/Level</label>
              <select
                value={classLevel}
                onChange={(e) => setClassLevel(e.target.value)}
                disabled={uploading}
              >
                <option value="">Select class...</option>
                {CLASSES.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                disabled={uploading}
              >
                {LANGUAGES.map(l => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the content..."
              rows={3}
              disabled={uploading}
            />
          </div>
        </div>

        {/* Progress Bar */}
        {progress > 0 && (
          <div className="progress-section">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <p className="progress-text">{progress}% - {uploading ? 'Uploading...' : 'Complete'}</p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className="submit-btn"
          disabled={uploading}
        >
          {uploading ? '⏳ Processing...' : `🚀 Upload ${uploadType === 'bulk' ? 'All' : 'Content'}`}
        </button>
      </form>

      {/* Info Box */}
      <div className="info-box">
        <h4>💡 Upload Tips</h4>
        <ul>
          <li><strong>Vector Embeddings:</strong> Embeddings are automatically generated for semantic search</li>
          <li><strong>Tagging:</strong> Accurate tags help students find relevant content quickly</li>
          <li><strong>Bulk Upload:</strong> Use bulk upload for multiple PDFs with same tags</li>
          <li><strong>Duplicates:</strong> System automatically detects and prevents duplicate content</li>
        </ul>
      </div>
    </div>
  );
};

export default ContentUpload;
