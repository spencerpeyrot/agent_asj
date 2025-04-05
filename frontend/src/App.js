import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import ChatMessage from './components/ChatMessage';
import TestPage from './components/TestPage';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializeSession = async () => {
      try {
        // Try to get sessionId from localStorage
        const storedSessionId = localStorage.getItem('sessionId');
        
        if (storedSessionId) {
          // Verify the session exists
          try {
            await axios.get(`${API_BASE_URL}/session/${storedSessionId}`);
            setSessionId(storedSessionId);
          } catch {
            // Session not found, create new one
            const response = await axios.post(`${API_BASE_URL}/session/start`);
            const newSessionId = response.data.session_id;
            localStorage.setItem('sessionId', newSessionId);
            setSessionId(newSessionId);
          }
        } else {
          // No stored session, create new one
          const response = await axios.post(`${API_BASE_URL}/session/start`);
          const newSessionId = response.data.session_id;
          localStorage.setItem('sessionId', newSessionId);
          setSessionId(newSessionId);
        }
      } catch (err) {
        setError('Failed to initialize session');
        console.error('Session initialization error:', err);
      } finally {
        setLoading(false);
      }
    };

    initializeSession();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Initializing your newsletter workspace...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-message">Error: {error}</div>;
  }

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || !sessionId) return;

    try {
      const messageData = {
        session_id: sessionId,
        speaker: "user",
        timestamp: new Date().toISOString(),
        content: inputMessage.trim(),
        metadata: {}
      };

      console.log('Sending message with data:', messageData);

      const response = await axios.post(`${API_BASE_URL}/message`, messageData);
      
      // Add both user message and AI response to messages
      setMessages(prevMessages => [
        ...prevMessages,
        {
          speaker: "user",
          content: inputMessage.trim(),
          timestamp: messageData.timestamp
        },
        {
          speaker: response.data.speaker,
          content: response.data.content,
          timestamp: response.data.timestamp
        }
      ]);

      // Clear input after sending
      setInputMessage('');

    } catch (error) {
      console.error('Error sending message:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
      }
      setError('Failed to send message');
    }
  };

  const startNewSession = async () => {
    setLoading(true);
    try {
      // Create new session
      const response = await axios.post(`${API_BASE_URL}/session/start`);
      const newSessionId = response.data.session_id;
      
      // Update localStorage and state
      localStorage.setItem('sessionId', newSessionId);
      setSessionId(newSessionId);
      
      // Clear messages for new session
      setMessages([]);
    } catch (err) {
      setError('Failed to start new session');
      console.error('New session error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <TestPage />
      <header className="App-header">
        <h1>Newsletter Builder</h1>
        {sessionId && <p>Session ID: {sessionId}</p>}
        {error && <p className="error">{error}</p>}
        <button onClick={startNewSession} disabled={loading}>New Session</button>
      </header>
      <div className="chat-container">
        <div className="messages-container" role="list" aria-label="messages">
          {messages.map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))}
          {loading && <div className="loading">Loading...</div>}
        </div>
        <form onSubmit={sendMessage} className="input-container">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message here..."
            disabled={loading || !sessionId}
          />
          <button type="submit" disabled={loading || !inputMessage.trim() || !sessionId}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;