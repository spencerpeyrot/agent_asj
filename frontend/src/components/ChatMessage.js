import React from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ message }) => {
  const isUser = message.speaker === 'user';
  
  console.log("Rendering message:", message);
  
  return (
    <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-content">
        {isUser ? (
          <div>{message.content}</div>
        ) : (
          <div>
            <ReactMarkdown>{message.content || ""}</ReactMarkdown>
          </div>
        )}
      </div>
      <div className="message-timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
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