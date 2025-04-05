import { render, screen } from '@testing-library/react';
import App from './App';

test('renders newsletter builder header', () => {
  render(<App />);
  const headerElement = screen.getByText(/Newsletter Builder/i);
  expect(headerElement).toBeInTheDocument();
});

test('renders new session button', () => {
  render(<App />);
  const buttonElement = screen.getByText(/New Session/i);
  expect(buttonElement).toBeInTheDocument();
});