import React, { useState } from 'react';
import apiService from '../services/apiService';
import './EvaluationPage.css';

function EvaluationPage({ user }) {
  const [file, setFile] = useState(null);
  const [runs, setRuns] = useState(2);
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleStartEvaluation = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await apiService.startEvaluation(file, runs);
      setTaskId(response.task_id);
      setStatus(`✅ Evaluation started! Task ID: ${response.task_id}`);
      setFile(null);
    } catch (err) {
      setError(err.message || 'Failed to start evaluation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="evaluation-page">
      <div className="evaluation-header">
        <h1>📊 Evaluate RAG Pipeline</h1>
        <p>Run comprehensive evaluations on your RAG system</p>
      </div>

      <div className="evaluation-container">
        <form onSubmit={handleStartEvaluation} className="evaluation-form">
          <div className="form-group">
            <label htmlFor="evalFile">Evaluation Dataset (JSON)</label>
            <input
              type="file"
              id="evalFile"
              onChange={handleFileChange}
              accept=".json"
              required
            />
            <small>Upload a JSON file with evaluation questions and ground truth</small>
          </div>

          <div className="form-group">
            <label htmlFor="runs">Number of Evaluation Runs</label>
            <input
              type="number"
              id="runs"
              value={runs}
              onChange={(e) => setRuns(parseInt(e.target.value))}
              min="1"
              max="10"
            />
          </div>

          <button type="submit" disabled={loading || !file} className="btn-primary">
            {loading ? '⏳ Starting...' : '▶️ Start Evaluation'}
          </button>
        </form>

        {status && <div className="success-message">{status}</div>}
        {error && <div className="error-message">{error}</div>}

        {taskId && (
          <div className="task-info">
            <h3>📋 Task Information</h3>
            <p>Task ID: <code>{taskId}</code></p>
            <p>Check the MLflow dashboard for detailed results</p>
          </div>
        )}

        <div className="evaluation-metrics">
          <h3>📈 Metrics Evaluated</h3>
          <ul>
            <li>✅ Precision@K - Fraction of retrieved documents that are relevant</li>
            <li>✅ Recall@K - Fraction of relevant documents that were retrieved</li>
            <li>✅ F1 Score - Harmonic mean of precision and recall</li>
            <li>✅ MRR - How early the first relevant result appears</li>
            <li>✅ Jaccard Stability - Consistency across repeated queries</li>
            <li>✅ Token F1 - Keyword overlap with ground truth answers</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default EvaluationPage;
