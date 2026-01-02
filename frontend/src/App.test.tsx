import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';

const renderWithProviders = (ui: React.ReactElement) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    });
    return render(
        <QueryClientProvider client={queryClient}>
            {ui}
        </QueryClientProvider>
    );
};

describe('App', () => {
    it('renders EAZY title', () => {
        renderWithProviders(<App />);
        // Check for EAZY in the app (may appear in multiple places)
        const titleElements = screen.getAllByText(/EAZY/i);
        expect(titleElements.length).toBeGreaterThan(0);
    });
});
