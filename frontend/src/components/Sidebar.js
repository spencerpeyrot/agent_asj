import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import '../styles/Sidebar.css';

const API_BASE_URL = 'http://localhost:8000';

const Sidebar = ({ isOpen, onClose, onSessionSelect, currentSessionId }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Only fetch sessions when the sidebar is open
    if (isOpen) {
      fetchSessions();
    }
  }, [isOpen]);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/sessions`);
      setSessions(response.data.sessions);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError('Failed to load previous sessions');
    } finally {
      setLoading(false);
    }
  };

  const formatSessionDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
      });
    } catch (e) {
      return dateString;
    }
  };

  // Extract first message or use placeholder
  const getSessionPreview = (session) => {
    if (session.messages && session.messages.length > 0) {
      const firstUserMessage = session.messages.find(msg => msg.speaker === 'user');
      if (firstUserMessage) {
        // Truncate message if too long
        return firstUserMessage.content.length > 30 
          ? firstUserMessage.content.substring(0, 30) + '...'
          : firstUserMessage.content;
      }
    }
    return 'No preview available';
  };

  // Check if sessions exists and is an array before mapping
  const renderSessions = () => {
    if (!sessions || !Array.isArray(sessions)) {
      return <p>No sessions available</p>;
    }

    return sessions.map((session) => (
      <div
        key={session.id}
        className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
        onClick={() => onSessionSelect(session.id)}
      >
        <div className="session-info">
          <span className="session-date">
            {format(new Date(session.created_at), 'MMM d, yyyy h:mm a')}
          </span>
          <span className="message-count">
            {session.message_count} messages
          </span>
        </div>
      </div>
    ));
  };

  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h2>Chat History</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      <div className="sessions-list">
        {renderSessions()}
      </div>
      
      <div className="sidebar-footer">
        <button className="refresh-btn" onClick={fetchSessions}>
          Refresh
        </button>
      </div>
    </div>
  );
};

export default Sidebar; 