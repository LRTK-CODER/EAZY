import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
// @ts-ignore - Component doesn't exist yet (TDD RED)
import App from './App';

describe('App', () => {
    it('renders EAZY title', () => {
        render(<App />);
        const titleElement = screen.getByText(/EAZY/i);
        expect(titleElement).toBeInTheDocument();
    });
});
