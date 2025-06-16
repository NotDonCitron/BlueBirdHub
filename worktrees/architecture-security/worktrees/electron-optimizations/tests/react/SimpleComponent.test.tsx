import React from 'react';
import { render, screen } from '../utils/test-utils';
import '@testing-library/jest-dom';

// Simple test to verify React testing setup works
describe('React Testing Setup', () => {
  test('renders a simple component', () => {
    const TestComponent = () => <div>Hello Test World</div>;
    
    render(<TestComponent />);
    
    expect(screen.getByText('Hello Test World')).toBeInTheDocument();
  });

  test('test utilities provide proper context', () => {
    const TestComponent = () => {
      return (
        <div>
          <h1>Test with Context</h1>
          <p>If this renders, contexts are working</p>
        </div>
      );
    };
    
    render(<TestComponent />);
    
    expect(screen.getByText('Test with Context')).toBeInTheDocument();
    expect(screen.getByText('If this renders, contexts are working')).toBeInTheDocument();
  });
});