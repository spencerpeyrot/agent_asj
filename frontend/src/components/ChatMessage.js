import React from 'react';
import PropTypes from 'prop-types';
import FormattedResponse from './FormattedResponse';

const ChatMessage = ({ message }) => {
  const { speaker, content } = message;
  
  return (
    <div className={`message ${speaker}`}>
      {speaker === 'assistant' ? (
        <FormattedResponse content={content} />
      ) : (
        <p>{content}</p>
      )}
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