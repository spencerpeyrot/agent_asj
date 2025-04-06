import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';
import ChatMessage from './components/ChatMessage';
import Sidebar from './components/Sidebar';
import TestPage from './components/TestPage';
import './styles/Sidebar.css';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showTestPage, setShowTestPage] = useState(false);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        setIsLoading(true);
        // Create initial session if none exists
        const response = await axios.post(`${API_BASE_URL}/session`);
        const newSessionId = response.data.session_id;
        setSessionId(newSessionId);
        
        try {
          // Load existing sessions
          const sessionsResponse = await axios.get(`${API_BASE_URL}/sessions`);
          if (sessionsResponse.data.sessions && sessionsResponse.data.sessions.length > 0) {
            setMessages(sessionsResponse.data.sessions[0].messages || []);
            setSessions(sessionsResponse.data.sessions);
          }
        } catch (sessionsError) {
          console.error('Error loading sessions:', sessionsError);
          // Don't block initialization if sessions can't be loaded
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('Error initializing app:', error);
        setError('Failed to initialize the application. Please refresh the page.');
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    const messageText = inputValue.trim();
    if (!messageText) return;

    try {
      // Add message to UI
      const userMessage = {
        id: Date.now().toString(),
        session_id: sessionId,
        speaker: 'user',
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      setMessages(prevMessages => [...prevMessages, userMessage]);
      
      // Clear the input immediately after sending
      setInputValue('');

      // Show typing indicator
      setIsTyping(true);

      // Send message to backend
      console.log('Sending message to backend:', userMessage);
      const response = await axios.post(`${API_BASE_URL}/message`, {
        session_id: sessionId,
        speaker: 'user',
        content: messageText,
        timestamp: new Date().toISOString(),
        metadata: {}
      });
      
      // Hide typing indicator
      setIsTyping(false);
      
      console.log('Response from backend:', response.data);
      
      // Check if we have a valid response
      if (response.data && response.data.content) {
        // Create AI message from response
        const aiMessage = {
          id: response.data.id || Date.now().toString() + '-ai',
          session_id: sessionId,
          speaker: 'assistant',
          content: response.data.content,
          timestamp: response.data.timestamp || new Date().toISOString(),
        };
        
        console.log('Created AI message:', aiMessage);
        console.log('AI message content length:', aiMessage.content.length);
        
        // Add the AI response to the messages
        setMessages(prevMessages => [...prevMessages, aiMessage]);
      } else {
        console.error('Invalid or empty response from server:', response.data);
        // Add a fallback message
        const errorMessage = {
          id: Date.now().toString() + '-error',
          session_id: sessionId,
          speaker: 'assistant',
          content: 'There was an issue generating a response. Please try again.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prevMessages => [...prevMessages, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError(`Failed to send message: ${error.message}`);
      
      // Add an error message to the chat
      const errorMessage = {
        id: Date.now().toString() + '-error',
        session_id: sessionId,
        speaker: 'assistant',
        content: `Error: ${error.message}. Please try again.`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    }
  };

  const loadSession = async (sessionId) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/session/${sessionId}`);
      setSessionId(sessionId);
      
      // Extract messages from the response and format them properly
      const sessionMessages = response.data.messages || [];
      
      // Format messages to ensure they have all required properties
      const formattedMessages = sessionMessages.map(msg => ({
        session_id: msg.session_id,
        speaker: msg.speaker,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString(),
        metadata: msg.message_metadata || {}
      }));
      
      setMessages(formattedMessages);
      localStorage.setItem('sessionId', sessionId);
      setSidebarOpen(false); // Close sidebar after selection
      
      console.log(`Loaded session ${sessionId} with ${formattedMessages.length} messages`);
    } catch (err) {
      console.error('Error loading session:', err);
      setError('Failed to load selected session');
    } finally {
      setIsLoading(false);
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

  const handleNewSession = async () => {
    try {
      // Create new session
      const response = await axios.post(`${API_BASE_URL}/session`);
      const newSessionId = response.data.session_id;
      
      // Clear current messages
      setMessages([]);
      setInputValue('');
      
      // Update session ID and add to sidebar
      setSessionId(newSessionId);
      localStorage.setItem('sessionId', newSessionId);

      // Update URL to reflect new session
      navigate(`/chat/${newSessionId}`);
    } catch (error) {
      console.error('Error creating new session:', error);
      // Add error handling UI feedback here
    }
  };

  const checkApiStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health/openai`);
      alert(`API Status: ${response.data.status}`);
    } catch (error) {
      console.error('Error checking API status:', error);
      alert('Error checking API status. Please check the console for details.');
    }
  };

  if (isLoading && messages.length === 0) {
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
        checkApiStatus={checkApiStatus}
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
            <button onClick={handleNewSession}>New Session</button>
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
              
              {isTyping && (
                <div className="message assistant-message typing-indicator">
                  <div className="message-content">
                    <span className="typing-dots"><span>.</span><span>.</span><span>.</span></span>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            
            <form className="message-form" onSubmit={sendMessage}>
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type your message..."
                rows="1"
              />
              <button type="submit" disabled={!inputValue.trim()}>
                Send
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default App;