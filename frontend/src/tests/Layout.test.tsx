import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

describe('Layout & Sidebar', () => {
    it('renders sidebar navigation links', () => {
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );

        // Sidebar links expected in Phase 2
        const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
        const projectsLink = screen.getByRole('link', { name: /projects/i });

        expect(dashboardLink).toBeInTheDocument();
        expect(projectsLink).toBeInTheDocument();
    });

    it('renders main content area', () => {
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        const main = screen.getByRole('main');
        expect(main).toBeInTheDocument();
    });
});
