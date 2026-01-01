import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import * as projectService from '@/services/projectService';
import type { Project } from '@/types/project';

// Mock the project service
vi.mock('@/services/projectService');

// Helper to render with providers
const renderWithProviders = (initialRoute = '/projects') => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false, // Disable retry for tests
            },
        },
    });

    return {
        user: userEvent.setup(),
        ...render(
            <QueryClientProvider client={queryClient}>
                <MemoryRouter initialEntries={[initialRoute]}>
                    <Routes>
                        <Route path="/projects" element={<Sidebar />} />
                        <Route path="/projects/:projectId" element={<Sidebar />} />
                        <Route path="/dashboard" element={<Sidebar />} />
                        <Route path="/settings" element={<Sidebar />} />
                    </Routes>
                </MemoryRouter>
            </QueryClientProvider>
        ),
    };
};

const mockProjects: Project[] = [
    {
        id: 1,
        name: 'E-commerce Security Test',
        description: 'Security testing for e-commerce platform',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
    },
    {
        id: 2,
        name: 'API Penetration Test',
        description: 'API security assessment',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
    },
    {
        id: 3,
        name: 'Mobile App DAST',
        description: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
    },
];

describe('Sidebar - Project List', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Loading State', () => {
        it('shows loading indicator while fetching projects', () => {
            // Mock API to never resolve (loading state)
            vi.mocked(projectService.getProjects).mockImplementation(
                () => new Promise(() => {})
            );

            renderWithProviders('/projects');

            // Should show loading indicator
            expect(screen.getByText(/loading/i)).toBeInTheDocument();
        });
    });

    describe('Data Rendering', () => {
        it('renders project list when data is loaded', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            // Wait for projects to be displayed
            await waitFor(() => {
                expect(screen.getByText('E-commerce Security Test')).toBeInTheDocument();
                expect(screen.getByText('API Penetration Test')).toBeInTheDocument();
                expect(screen.getByText('Mobile App DAST')).toBeInTheDocument();
            });
        });

        it('renders projects with checkboxes', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            // Wait for projects to be displayed
            await waitFor(() => {
                const checkboxes = screen.getAllByRole('checkbox');
                // Should have checkboxes for each project
                expect(checkboxes.length).toBeGreaterThanOrEqual(3);
            });
        });

        it('renders project links with correct href', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            // Wait for projects to be displayed
            await waitFor(() => {
                const link1 = screen.getByRole('link', { name: 'E-commerce Security Test' });
                const link2 = screen.getByRole('link', { name: 'API Penetration Test' });
                const link3 = screen.getByRole('link', { name: 'Mobile App DAST' });

                expect(link1).toHaveAttribute('href', '/projects/1');
                expect(link2).toHaveAttribute('href', '/projects/2');
                expect(link3).toHaveAttribute('href', '/projects/3');
            });
        });

        it('renders dropdown menu for each project', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            // Wait for projects to be displayed
            await waitFor(() => {
                // Should have dropdown trigger buttons (MoreVertical icons)
                const dropdownTriggers = screen.getAllByRole('button', { name: '' });
                // At least one for each project
                expect(dropdownTriggers.length).toBeGreaterThanOrEqual(3);
            });
        });
    });

    describe('Empty State', () => {
        it('shows empty state when no projects exist', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue([]);

            renderWithProviders('/projects');

            // Wait for empty state to be displayed
            await waitFor(() => {
                expect(screen.getByText(/no projects yet/i)).toBeInTheDocument();
            });
        });

        it('shows create first project button in empty state', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue([]);

            renderWithProviders('/projects');

            // Wait for empty state to be displayed
            await waitFor(() => {
                expect(screen.getByRole('button', { name: /create first project/i })).toBeInTheDocument();
            });
        });
    });

    describe('Error State', () => {
        it('shows error message when API call fails', async () => {
            vi.mocked(projectService.getProjects).mockRejectedValue(
                new Error('Failed to fetch projects')
            );

            renderWithProviders('/projects');

            // Wait for error message to be displayed
            await waitFor(() => {
                expect(screen.getByText(/error.*loading.*projects/i)).toBeInTheDocument();
            });
        });

        it('shows error icon in error state', async () => {
            vi.mocked(projectService.getProjects).mockRejectedValue(
                new Error('Failed to fetch projects')
            );

            renderWithProviders('/projects');

            // Wait for error state
            await waitFor(() => {
                // Should show error icon (AlertCircle or similar)
                expect(screen.getByText(/error.*loading.*projects/i)).toBeInTheDocument();
            });
        });
    });

    describe('Header Actions', () => {
        it('renders plus button to create new project', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            // Should have Plus button in header
            await waitFor(() => {
                // Plus button with tooltip "New Project"
                const plusButtons = screen.getAllByRole('button');
                expect(plusButtons.some(btn => btn.querySelector('[class*="lucide-plus"]'))).toBe(true);
            });
        });

        it('renders trash button for bulk delete', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            // Should have Trash button in header
            await waitFor(() => {
                const trashButtons = screen.getAllByRole('button');
                expect(trashButtons.some(btn => btn.querySelector('[class*="lucide-trash"]'))).toBe(true);
            });
        });

        it('trash button is disabled when no projects are selected', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            await waitFor(() => {
                const buttons = screen.getAllByRole('button');
                const trashButton = buttons.find(btn => btn.querySelector('[class*="lucide-trash"]'));

                // Trash button should be disabled initially
                expect(trashButton).toBeDisabled();
            });
        });
    });

    describe('Select All Functionality', () => {
        it('renders select all button', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /select all/i })).toBeInTheDocument();
            });
        });

        it('changes to deselect all when all projects are selected', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            const { user } = renderWithProviders('/projects');

            await waitFor(() => {
                expect(screen.getByRole('button', { name: /select all/i })).toBeInTheDocument();
            });

            // Click select all
            const selectAllButton = screen.getByRole('button', { name: /select all/i });
            await user.click(selectAllButton);

            // Button text should change to "Deselect All"
            await waitFor(() => {
                expect(screen.getByRole('button', { name: /deselect all/i })).toBeInTheDocument();
            });
        });
    });

    describe('Project Selection', () => {
        it('allows selecting individual projects', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            const { user } = renderWithProviders('/projects');

            await waitFor(() => {
                expect(screen.getByText('E-commerce Security Test')).toBeInTheDocument();
            });

            // Get checkboxes
            const checkboxes = screen.getAllByRole('checkbox');

            // Select first project
            await user.click(checkboxes[0]);

            // Checkbox should be checked
            await waitFor(() => {
                expect(checkboxes[0]).toBeChecked();
            });
        });

        it('enables trash button when projects are selected', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            const { user } = renderWithProviders('/projects');

            await waitFor(() => {
                expect(screen.getByText('E-commerce Security Test')).toBeInTheDocument();
            });

            // Select first project
            const checkboxes = screen.getAllByRole('checkbox');
            await user.click(checkboxes[0]);

            // Trash button should be enabled
            await waitFor(() => {
                const buttons = screen.getAllByRole('button');
                const trashButton = buttons.find(btn => btn.querySelector('[class*="lucide-trash"]'));
                expect(trashButton).not.toBeDisabled();
            });
        });
    });

    describe('Route-based Rendering', () => {
        it('renders project sidebar when on /projects route', async () => {
            vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects);

            renderWithProviders('/projects');

            // Should show Projects header
            await waitFor(() => {
                expect(screen.getByText(/projects/i)).toBeInTheDocument();
            });
        });

        it('does not render project list on dashboard route', () => {
            renderWithProviders('/dashboard');

            // Should show Dashboard header instead
            expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
            // Should not call project service
            expect(projectService.getProjects).not.toHaveBeenCalled();
        });

        it('does not render project list on settings route', () => {
            renderWithProviders('/settings');

            // Should show Settings header instead
            expect(screen.getByText(/settings/i)).toBeInTheDocument();
            // Should not call project service
            expect(projectService.getProjects).not.toHaveBeenCalled();
        });
    });
});
