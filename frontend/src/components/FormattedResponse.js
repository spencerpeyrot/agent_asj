import React from 'react';

const FormattedResponse = ({ content }) => {
  // Process content to format headers and bullet points
  const formatContent = (text) => {
    if (!text) return '';
    
    // Split into lines for processing
    const lines = text.split('\n');
    let result = [];
    let bulletList = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const key = `line-${i}`;
      
      // Format headers (lines starting with # or ##)
      if (line.startsWith('# ')) {
        // Close any open bullet list before adding a heading
        if (bulletList) {
          result.push(<ul key={`list-${i}`} className="bullet-list">{bulletList}</ul>);
          bulletList = null;
        }
        result.push(<h1 key={key} className="response-heading-1">{line.substring(2)}</h1>);
      } 
      else if (line.startsWith('## ')) {
        if (bulletList) {
          result.push(<ul key={`list-${i}`} className="bullet-list">{bulletList}</ul>);
          bulletList = null;
        }
        result.push(<h2 key={key} className="response-heading-2">{line.substring(3)}</h2>);
      } 
      else if (line.startsWith('### ')) {
        if (bulletList) {
          result.push(<ul key={`list-${i}`} className="bullet-list">{bulletList}</ul>);
          bulletList = null;
        }
        result.push(<h3 key={key} className="response-heading-3">{line.substring(4)}</h3>);
      }
      
      // Format bullet points
      else if (line.match(/^\s*[-*]\s/)) {
        const bulletContent = line.replace(/^\s*[-*]\s/, '');
        if (!bulletList) {
          bulletList = [];
        }
        bulletList.push(<li key={key} className="response-bullet">{bulletContent}</li>);
      }
      
      // Regular paragraph or empty line
      else {
        // Close any open bullet list before adding a paragraph
        if (bulletList) {
          result.push(<ul key={`list-${i}`} className="bullet-list">{bulletList}</ul>);
          bulletList = null;
        }
        
        if (line.trim() === '') {
          result.push(<br key={key} />);
        } else {
          result.push(<p key={key} className="response-paragraph">{line}</p>);
        }
      }
    }
    
    // Add any remaining bullet list
    if (bulletList) {
      result.push(<ul key="list-final" className="bullet-list">{bulletList}</ul>);
    }
    
    return result;
  };

  return (
    <div className="formatted-response">
      {formatContent(content)}
    </div>
  );
};

export default FormattedResponse; 