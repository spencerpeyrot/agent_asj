import { render, screen } from '@testing-library/react';
import ChatMessage from '../../components/ChatMessage';

describe('ChatMessage Component', () => {
  const mockMessage = {
    speaker: 'user',
    content: 'Test message',
    timestamp: '2024-04-05T12:00:00.000Z'
  };

  test('renders message content', () => {
    render(<ChatMessage message={mockMessage} />);
    expect(screen.getByText(mockMessage.content)).toBeInTheDocument();
  });

  test('displays correct speaker', () => {
    render(<ChatMessage message={mockMessage} />);
    expect(screen.getByText(mockMessage.speaker)).toBeInTheDocument();
  });

  test('shows formatted timestamp', () => {
    render(<ChatMessage message={mockMessage} />);
    const formattedTime = new Date(mockMessage.timestamp).toLocaleTimeString();
    expect(screen.getByText(formattedTime)).toBeInTheDocument();
  });

  test('applies correct CSS classes based on speaker', () => {
    const { container } = render(<ChatMessage message={mockMessage} />);
    expect(container.firstChild).toHaveClass('message', mockMessage.speaker);
  });

  test('handles system messages', () => {
    const systemMessage = {
      ...mockMessage,
      speaker: 'system'
    };
    const { container } = render(<ChatMessage message={systemMessage} />);
    expect(container.firstChild).toHaveClass('message', 'system');
  });

  test('handles long messages', () => {
    const longMessage = {
      ...mockMessage,
      content: 'A'.repeat(1000)
    };
    render(<ChatMessage message={longMessage} />);
    expect(screen.getByText('A'.repeat(1000))).toBeInTheDocument();
  });
}); 