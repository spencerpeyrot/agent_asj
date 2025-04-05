import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
import App from '../../App';
import axios from 'axios';

// Mock axios
jest.mock('axios');

describe('App Component Unit Tests', () => {
  const mockSessionId = 'test-session-id';
  
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
    
    // Mock successful session start
    axios.post.mockResolvedValue({
      data: { session_id: mockSessionId }
    });
    
    // Mock successful session fetch
    axios.get.mockResolvedValue({
      data: {
        session_id: mockSessionId,
        chat_history: [],
        created_at: new Date().toISOString()
      }
    });
  });

  test('renders newsletter builder header', () => {
    render(<App />);
    expect(screen.getByText(/Newsletter Builder/i)).toBeInTheDocument();
  });

  test('renders new session button', () => {
    render(<App />);
    expect(screen.getByText(/New Session/i)).toBeInTheDocument();
  });

  test('starts new session on initial load', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith('http://localhost:8000/session/start');
      expect(localStorage.getItem('sessionId')).toBe(mockSessionId);
    });
  });

  test('fetches existing session from localStorage', async () => {
    localStorage.setItem('sessionId', mockSessionId);
    
    render(<App />);
    
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(`http://localhost:8000/session/${mockSessionId}`);
    });
  });

  test('sends message and displays response', async () => {
    const testMessage = 'Hello, world!';
    const mockResponse = {
      speaker: 'system',
      content: 'Received: Hello, world!',
      timestamp: new Date().toISOString()
    };

    axios.post.mockImplementation((url) => {
      if (url.includes('/message')) {
        return Promise.resolve({ data: mockResponse });
      }
      return Promise.resolve({ data: { session_id: mockSessionId } });
    });

    render(<App />);

    await waitFor(() => {
      expect(localStorage.getItem('sessionId')).toBe(mockSessionId);
    });

    const input = screen.getByPlaceholderText(/Type your message here/i);
    const sendButton = screen.getByText(/Send/i);

    await act(async () => {
      await userEvent.type(input, testMessage);
    });

    await act(async () => {
      fireEvent.click(sendButton);
    });

    await waitFor(() => {
      expect(screen.getByText(testMessage)).toBeInTheDocument();
      expect(screen.getByText('Received: Hello, world!')).toBeInTheDocument();
    });
  });

  test('handles session start error', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    axios.post.mockRejectedValueOnce(new Error('Failed to start session'));

    render(<App />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    consoleErrorSpy.mockRestore();
  });

  test('handles message send error', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    axios.post.mockImplementation((url) => {
      if (url.includes('/message')) {
        return Promise.reject(new Error('Failed to send message'));
      }
      return Promise.resolve({ data: { session_id: mockSessionId } });
    });

    render(<App />);

    await waitFor(() => {
      expect(localStorage.getItem('sessionId')).toBe(mockSessionId);
    });

    const input = screen.getByPlaceholderText(/Type your message here/i);
    const sendButton = screen.getByText(/Send/i);

    await act(async () => {
      await userEvent.type(input, 'Test message');
    });

    await act(async () => {
      fireEvent.click(sendButton);
    });

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    consoleErrorSpy.mockRestore();
  });

  test('clears messages on new session', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('list')).toBeInTheDocument();
    });

    const newSessionButton = screen.getByText(/New Session/i);

    await act(async () => {
      fireEvent.click(newSessionButton);
    });

    const messagesContainer = screen.getByRole('list');
    expect(messagesContainer.children.length).toBe(0);
  });
}); 