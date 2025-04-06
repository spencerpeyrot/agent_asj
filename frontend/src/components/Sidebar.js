import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import '../styles/Sidebar.css';

const API_BASE_URL = 'http://localhost:8000';

const Sidebar = ({ isOpen, onClose, onSessionSelect, currentSessionId, checkApiStatus }) => {
  const [sessions, setSessions] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [menuOpen, setMenuOpen] = useState(null);

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
      
      if (response.data && Array.isArray(response.data.sessions)) {
        setSessions(response.data.sessions);
      } else {
        console.error('Invalid response format:', response.data);
        setError('Unable to load chat history. Please try again.');
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError(
        err.response?.data?.detail || 
        'Unable to load chat history. Please check your connection and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sessionId, e) => {
    e.stopPropagation(); // Prevent triggering session selection
    if (window.confirm('Are you sure you want to delete this chat?')) {
      try {
        await axios.delete(`${API_BASE_URL}/session/${sessionId}`);
        fetchSessions(); // Refresh the list
      } catch (error) {
        console.error('Error deleting session:', error);
        setError('Failed to delete session');
      }
    }
  };

  const startEditing = (session, e) => {
    e.stopPropagation(); // Prevent triggering session selection
    setEditingId(session.id);
    setNewTitle(session.title || `Chat from ${format(new Date(session.created_at), 'MMM d, yyyy')}`);
  };

  const handleRename = async (sessionId, e) => {
    e.preventDefault();
    try {
      await axios.patch(`${API_BASE_URL}/session/${sessionId}`, {
        title: newTitle
      });
      setEditingId(null);
      fetchSessions(); // Refresh the list
    } catch (error) {
      console.error('Error renaming session:', error);
      setError('Failed to rename session');
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
        {editingId === session.id ? (
          <form onSubmit={(e) => handleRename(session.id, e)}>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              autoFocus
              onBlur={() => setEditingId(null)}
            />
          </form>
        ) : (
          <div className="session-info">
            <span className="session-title">
              {session.title || `Chat from ${format(new Date(session.created_at), 'MMM d, yyyy')}`}
            </span>
            <div className="session-actions">
              <button
                className="kebab-menu"
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpen(menuOpen === session.id ? null : session.id);
                }}
              >
                ⋮
              </button>
              {menuOpen === session.id && (
                <div className="dropdown-menu">
                  <button onClick={(e) => startEditing(session, e)}>
                    Rename
                  </button>
                  <button onClick={(e) => handleDelete(session.id, e)}>
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    ));
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuOpen && !event.target.closest('.session-actions')) {
        setMenuOpen(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [menuOpen]);

  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h2>Chat History</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      {error && <div className="error-message">{error}</div>}
      <div className="sessions-list">
        {renderSessions()}
      </div>
      
      <div className="sidebar-footer">
        <button className="refresh-btn" onClick={fetchSessions}>
          Refresh
        </button>
        <button className="api-status-btn" onClick={checkApiStatus}>
          Check API Status
        </button>
      </div>
    </div>
  );
};

export default Sidebar; 