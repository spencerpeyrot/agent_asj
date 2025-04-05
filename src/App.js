import React, { useState, useEffect } from 'react';
import axios from 'axios';

const App = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const initializeSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/session/start');
      const newSessionId = response.data.session_id;
      localStorage.setItem('sessionId', newSessionId);
      setSessionId(newSessionId);
    } catch (err) {
      setError('Failed to initialize session');
      console.error('Session initialization error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initializeSession();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>Initializing your newsletter workspace...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  return (
    <div>
      <h1>Newsletter Builder</h1>
      <button onClick={initializeSession}>New Session</button>
      {/* Rest of your components */}
    </div>
  );
};

export default App; 