import React from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import '../styles/ChatMessage.css';

const formatTimestamp = (timestamp) => {
  try {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch (error) {
    console.error('Error formatting timestamp:', error);
    return '';
  }
};

const ChatMessage = ({ message }) => {
  // Add debug logging
  console.log('Message received in ChatMessage:', message);

  if (!message) {
    console.error('No message provided to ChatMessage component');
    return null;
  }

  const { content, speaker, timestamp } = message;

  // Add more debug logging
  console.log('Content:', content);
  console.log('Speaker:', speaker);
  console.log('Timestamp:', timestamp);

  return (
    <div className={`message ${speaker}-message`}>
      <div className="message-content">
        {speaker === 'assistant' ? (
          <div className="structured-response">
            {content ? (
              <ReactMarkdown>
                {content}
              </ReactMarkdown>
            ) : (
              <p className="empty-message">No content available</p>
            )}
          </div>
        ) : (
          <p>{content || 'No content available'}</p>
        )}
      </div>
      <div className="message-timestamp">
        {formatTimestamp(timestamp)}
      </div>
    </div>
  );
};

ChatMessage.propTypes = {
  message: PropTypes.shape({
    speaker: PropTypes.string.isRequired,
    content: PropTypes.string,
    timestamp: PropTypes.string
  }).isRequired
};

export default ChatMessage; 