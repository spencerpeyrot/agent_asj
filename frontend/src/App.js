import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import ChatMessage from './components/ChatMessage';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(localStorage.getItem('sessionId') || '');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initializeSession = async () => {
      if (!sessionId) {
        await startNewSession();
      } else {
        await fetchSession(sessionId);
      }
    };
    initializeSession();
  }, []); // Remove sessionId from dependencies

  const startNewSession = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/session/start`);
      const newSessionId = response.data.session_id;
      localStorage.setItem('sessionId', newSessionId);
      setSessionId(newSessionId);
      setMessages([]);
    } catch (error) {
      console.error('Error starting session:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSession = async (id) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/session/${id}`);
      setMessages(response.data.chat_history || []);
    } catch (error) {
      console.error('Error fetching session:', error);
      if (error.response?.status === 404) {
        await startNewSession();
      }
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    setLoading(true);
    try {
      const messageObj = {
        session_id: sessionId,
        speaker: 'user',
        content: inputMessage
      };
      
      setMessages(prev => [
        ...prev, 
        { speaker: 'user', content: inputMessage, timestamp: new Date().toISOString() }
      ]);
      setInputMessage('');
      
      const response = await axios.post(`${API_BASE_URL}/message`, messageObj);
      setMessages(prev => [...prev, response.data]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Newsletter Builder</h1>
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