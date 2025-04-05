import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TestPage = () => {
  const [healthStatus, setHealthStatus] = useState(null);
  const [openaiStatus, setOpenaiStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkHealth = async () => {
    setLoading(true);
    try {
      // Check basic health
      const healthResponse = await axios.get('http://localhost:8000/health');
      setHealthStatus(healthResponse.data);

      // Check OpenAI connection
      const openaiResponse = await axios.get('http://localhost:8000/health/openai');
      setOpenaiStatus(openaiResponse.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="test-page">
      <h1>System Health Check</h1>
      
      {loading && <p>Loading status...</p>}
      
      {error && (
        <div className="error-box">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {healthStatus && (
        <div className="status-box">
          <h3>API Health</h3>
          <p>Status: {healthStatus.status}</p>
          <p>Last Checked: {new Date(healthStatus.timestamp).toLocaleString()}</p>
        </div>
      )}

      {openaiStatus && (
        <div className="status-box">
          <h3>OpenAI Connection</h3>
          <p>Status: {openaiStatus.status}</p>
          <p>Message: {openaiStatus.message}</p>
          <p>Last Checked: {new Date(openaiStatus.timestamp).toLocaleString()}</p>
        </div>
      )}

      <button onClick={checkHealth}>Refresh Status</button>
    </div>
  );
};

export default TestPage; 