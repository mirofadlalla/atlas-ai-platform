import React, { useState } from 'react';
import apiService from '../services/apiService';
import './IngestPage.css';

function IngestPage({ user }) {
  const [file, setFile] = useState(null);
  const [source, setSource] = useState('');
  const [author, setAuthor] = useState(user?.email || '');
  const [recursive, setRecursive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file');
      return;
    }
    
    if (!source) {
      setError('Please enter a source name');
      return;
    }

    setLoading(true);
    setError('');
    setStatus('');

    try {
      await apiService.uploadFile(file, source, author, recursive);
      setStatus('✅ File ingestion started successfully!');
      setFile(null);
      setSource('');
    } catch (err) {
      setError(err.message || 'Failed to ingest file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ingest-page">
      <div className="ingest-header">
        <h1>📤 Ingest Documents</h1>
        <p>Upload and process files into your knowledge base</p>
      </div>

      <div className="ingest-container">
        <form onSubmit={handleSubmit} className="ingest-form">
          <div className="form-group">
            <label htmlFor="docFile">Document File (PDF, TXT, MD)</label>
            <input
              type="file"
              id="docFile"
              onChange={handleFileChange}
              accept=".pdf,.txt,.md,.csv,.json"
              required
            />
            <small>Select a document to upload and process</small>
            {file && <div className="file-selected">✅ Selected: {file.name}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="source">Source Name</label>
            <input
              type="text"
              id="source"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="Annual Report 2023"
              required
            />
            <small>Descriptive name for tracking</small>
          </div>

          <div className="form-group">
            <label htmlFor="author">Author</label>
            <input
              type="text"
              id="author"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Your name"
            />
          </div>

          <div className="form-group checkbox">
            <input
              type="checkbox"
              id="recursive"
              checked={recursive}
              onChange={(e) => setRecursive(e.target.checked)}
            />
            <label htmlFor="recursive">Process subdirectories recursively</label>
          </div>

          <button type="submit" disabled={loading || !file} className="btn-primary">
            {loading ? '⏳ Ingesting...' : '📤 Ingest File'}
          </button>
        </form>

        {status && <div className="success-message">{status}</div>}
        {error && <div className="error-message">{error}</div>}

        <div className="ingest-info">
          <h3>ℹ️ Information</h3>
          <ul>
            <li>Supported formats: PDF, TXT, MD</li>
            <li>Files are automatically chunked and embedded</li>
            <li>Duplicate files are skipped to save computation</li>
            <li>Documents are isolated per-tenant</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default IngestPage;
