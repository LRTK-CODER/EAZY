import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '../App';

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

describe('Layout & Sidebar', () => {
    it('renders sidebar navigation links', () => {
        renderWithProviders(<App />);

        // Sidebar links expected in Phase 2
        const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
        const projectsLink = screen.getByRole('link', { name: /projects/i });

        expect(dashboardLink).toBeInTheDocument();
        expect(projectsLink).toBeInTheDocument();
    });

    it('renders main content area', () => {
        renderWithProviders(<App />);
        const main = screen.getByRole('main');
        expect(main).toBeInTheDocument();
    });
});
