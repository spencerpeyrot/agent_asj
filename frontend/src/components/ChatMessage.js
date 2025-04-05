import React from 'react';
import PropTypes from 'prop-types';

const ChatMessage = ({ message }) => {
  return (
    <div className={`message ${message.speaker}`}>
      <span className="speaker">{message.speaker}</span>
      <p>{message.content}</p>
      <span className="timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
      </span>
    </div>
  );
};

ChatMessage.propTypes = {
  message: PropTypes.shape({
    speaker: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired,
    timestamp: PropTypes.string.isRequired
  }).isRequired
};

export default ChatMessage; 