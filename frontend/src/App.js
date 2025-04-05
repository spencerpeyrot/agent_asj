import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';
import ChatMessage from './components/ChatMessage';
import Sidebar from './components/Sidebar';
import TestPage from './components/TestPage';
import './styles/Sidebar.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showTestPage, setShowTestPage] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initializeSession();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeSession = async () => {
    setLoading(true);
    setError(null);
    try {
      // Check localStorage first
      const storedId = localStorage.getItem('sessionId');
      if (storedId) {
        // Try to load existing session
        try {
          const response = await axios.get(`${API_BASE_URL}/session/${storedId}`);
          setSessionId(storedId);
          setMessages(response.data.messages || []);
          setLoading(false);
          return;
        } catch (err) {
          // Session not found or error, create new one
          console.error('Failed to load stored session:', err);
          localStorage.removeItem('sessionId');
        }
      }
      
      // Create new session
      const response = await axios.post(`${API_BASE_URL}/session/start`);
      const newSessionId = response.data.session_id;
      localStorage.setItem('sessionId', newSessionId);
      setSessionId(newSessionId);
      setMessages([]);
    } catch (err) {
      setError('Failed to initialize session');
      console.error('Session initialization error:', err);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputValue.trim() || sending) return;
    
    const userMessage = {
      session_id: sessionId,
      speaker: 'user',
      timestamp: new Date().toISOString(),
      content: inputValue.trim(),
      metadata: {}
    };
    
    console.log('Sending message with data:', userMessage);
    
    // Update UI immediately
    setMessages([...messages, userMessage]);
    setInputValue('');
    setSending(true);
    
    try {
      // Send to API
      const response = await axios.post(`${API_BASE_URL}/message`, userMessage);
      
      // Add assistant's response
      setMessages(prev => [...prev, response.data]);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const loadSession = async (sessionId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/session/${sessionId}`);
      setSessionId(sessionId);
      setMessages(response.data.messages || []);
      localStorage.setItem('sessionId', sessionId);
      setSidebarOpen(false); // Close sidebar after selection
    } catch (err) {
      console.error('Error loading session:', err);
      setError('Failed to load selected session');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e);
    } else if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      const cursorPosition = e.target.selectionStart;
      const currentValue = e.target.value;
      const lines = currentValue.substring(0, cursorPosition).split('\n');
      const currentLine = lines[lines.length - 1];
      
      // If the current line starts with a bullet point and is empty, remove it
      if (currentLine.trim() === '• ' || currentLine.trim() === '* ') {
        const newText = [
          ...lines.slice(0, -1),
          currentValue.substring(cursorPosition)
        ].join('\n');
        setInputValue(newText);
      } else {
        // Add a new bullet point if we're in a list, otherwise just add a newline
        const newText = currentValue.substring(0, cursorPosition) +
          '\n' + (currentLine.trimStart().startsWith('• ') || currentLine.trimStart().startsWith('* ') ? '• ' : '') +
          currentValue.substring(cursorPosition);
        setInputValue(newText);
      }
    } else if (e.key === '8' && e.shiftKey) {
      e.preventDefault();
      const cursorPosition = e.target.selectionStart;
      const currentValue = e.target.value;
      const newText = 
        currentValue.substring(0, cursorPosition) + 
        '• ' + 
        currentValue.substring(cursorPosition);
      setInputValue(newText);
      
      // Position cursor after bullet point
      setTimeout(() => {
        e.target.selectionStart = cursorPosition + 2;
        e.target.selectionEnd = cursorPosition + 2;
      }, 0);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    // Convert asterisk to bullet point when followed by a space
    if (value.endsWith('* ')) {
      const newValue = value.slice(0, -2) + '• ';
      setInputValue(newValue);
    } else {
      setInputValue(value);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Initializing your newsletter workspace...</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar overlay for mobile */}
      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`} 
        onClick={() => setSidebarOpen(false)}
      ></div>
      
      {/* Sidebar component */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        onSessionSelect={loadSession}
        currentSessionId={sessionId}
      />
      
      {/* Main content */}
      <div className="main-content">
        <header className="app-header">
          <button 
            className="sidebar-toggle" 
            onClick={() => setSidebarOpen(true)}
          >
            ☰
          </button>
          <h1>Newsletter Builder</h1>
          <div className="header-buttons">
            <button onClick={() => setShowTestPage(!showTestPage)}>
              {showTestPage ? 'Back to Chat' : 'Check API Status'}
            </button>
            <button onClick={initializeSession}>New Session</button>
          </div>
        </header>
        
        {error && <div className="error-message">{error}</div>}
        
        {showTestPage ? (
          <TestPage />
        ) : (
          <>
            <div className="messages-container">
              {messages.length === 0 ? (
                <div className="welcome-message">
                  <h2>Welcome to the Newsletter Builder!</h2>
                  <p>Start by describing the newsletter you want to create.</p>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <ChatMessage key={index} message={msg} />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <form className="message-form" onSubmit={sendMessage}>
              <textarea
                value={inputValue}
                onChange={handleInputChange}
                placeholder="Type your message..."
                disabled={sending}
                rows="1"
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
                }}
                onKeyDown={handleKeyDown}
              />
              <button type="submit" disabled={!inputValue.trim() || sending}>
                {sending ? 'Sending...' : 'Send'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default App;