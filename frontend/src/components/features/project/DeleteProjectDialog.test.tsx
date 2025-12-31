import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
// @ts-expect-error - DeleteProjectDialog doesn't exist yet (TDD RED phase)
import { DeleteProjectDialog } from './DeleteProjectDialog';
import * as projectService from '@/services/projectService';
import { toast } from 'sonner';
// @ts-expect-error - Project type doesn't exist yet (TDD RED phase)
import type { Project } from '@/types/project';

// Mock the project service
vi.mock('@/services/projectService');

// Mock sonner toast
vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
    },
    Toaster: () => null,
}));

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            mutations: {
                retry: false, // Disable retry for tests
            },
        },
    });

    return {
        user: userEvent.setup(),
        ...render(
            <QueryClientProvider client={queryClient}>
                <MemoryRouter>
                    <div id="root">{ui}</div>
                </MemoryRouter>
            </QueryClientProvider>
        ),
    };
};

const mockProject: Project = {
    id: 1,
    name: 'Test Project',
    description: 'Test Description',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
};

describe('DeleteProjectDialog Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Single Project Delete', () => {
        describe('Dialog Rendering', () => {
            it('renders confirmation dialog for single project', () => {
                renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                // Should show confirmation message
                expect(screen.getByText(/are you sure.*delete/i)).toBeInTheDocument();
                expect(screen.getByText(/Test Project/i)).toBeInTheDocument();
            });

            it('renders delete and cancel buttons', () => {
                renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
                expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
            });

            it('does not render when open is false', () => {
                renderWithProviders(
                    <DeleteProjectDialog
                        open={false}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                expect(screen.queryByText(/are you sure.*delete/i)).not.toBeInTheDocument();
            });

            it('shows warning message about permanent deletion', () => {
                renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
            });
        });

        describe('Single Delete Action', () => {
            it('calls deleteProject API with correct project id', async () => {
                const mockDeleteProject = vi.mocked(projectService.deleteProject).mockResolvedValue(undefined);

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(mockDeleteProject).toHaveBeenCalledWith(1);
                });
            });

            it('shows success message after successful deletion', async () => {
                vi.mocked(projectService.deleteProject).mockResolvedValue(undefined);

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(toast.success).toHaveBeenCalledWith('Project deleted successfully');
                });
            });

            it('shows error message when deletion fails', async () => {
                vi.mocked(projectService.deleteProject).mockRejectedValue(
                    new Error('Failed to delete project')
                );

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(toast.error).toHaveBeenCalledWith('Failed to delete project');
                });
            });

            it('closes dialog after successful deletion', async () => {
                vi.mocked(projectService.deleteProject).mockResolvedValue(undefined);

                const onOpenChange = vi.fn();
                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={onOpenChange}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(onOpenChange).toHaveBeenCalledWith(false);
                });
            });

            it('disables buttons while deleting', async () => {
                vi.mocked(projectService.deleteProject).mockImplementation(
                    () => new Promise((resolve) => setTimeout(resolve, 1000))
                );

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1]}
                        projectNames={['Test Project']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                // Both buttons should be disabled
                expect(deleteButton).toBeDisabled();
                expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
            });
        });
    });

    describe('Bulk Delete', () => {
        describe('Dialog Rendering', () => {
            it('renders confirmation dialog for multiple projects', () => {
                renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1, 2, 3]}
                        projectNames={['Project 1', 'Project 2', 'Project 3']}
                    />
                );

                // Should show plural message
                expect(screen.getByText(/3.*projects/i)).toBeInTheDocument();
            });

            it('shows list of project names to be deleted', () => {
                renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1, 2, 3]}
                        projectNames={['Project 1', 'Project 2', 'Project 3']}
                    />
                );

                expect(screen.getByText(/Project 1/i)).toBeInTheDocument();
                expect(screen.getByText(/Project 2/i)).toBeInTheDocument();
                expect(screen.getByText(/Project 3/i)).toBeInTheDocument();
            });
        });

        describe('Bulk Delete Action', () => {
            it('calls deleteProjects API with all project ids', async () => {
                const mockDeleteProjects = vi.mocked(projectService.deleteProjects).mockResolvedValue(undefined);

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1, 2, 3]}
                        projectNames={['Project 1', 'Project 2', 'Project 3']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(mockDeleteProjects).toHaveBeenCalledWith([1, 2, 3]);
                });
            });

            it('shows success message with count after bulk deletion', async () => {
                vi.mocked(projectService.deleteProjects).mockResolvedValue(undefined);

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1, 2, 3]}
                        projectNames={['Project 1', 'Project 2', 'Project 3']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(toast.success).toHaveBeenCalledWith('3 projects deleted successfully');
                });
            });

            it('shows error message when bulk deletion fails', async () => {
                vi.mocked(projectService.deleteProjects).mockRejectedValue(
                    new Error('Failed to delete projects')
                );

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1, 2, 3]}
                        projectNames={['Project 1', 'Project 2', 'Project 3']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(toast.error).toHaveBeenCalledWith('Failed to delete projects');
                });
            });

            it('shows partial success message when some deletions fail', async () => {
                // Mock deleteProjects to fail partially
                vi.mocked(projectService.deleteProjects).mockRejectedValue(
                    new Error('Failed to delete some projects')
                );

                const { user } = renderWithProviders(
                    <DeleteProjectDialog
                        open={true}
                        onOpenChange={vi.fn()}
                        projectIds={[1, 2, 3]}
                        projectNames={['Project 1', 'Project 2', 'Project 3']}
                    />
                );

                const deleteButton = screen.getByRole('button', { name: /delete/i });
                await user.click(deleteButton);

                await waitFor(() => {
                    expect(toast.error).toHaveBeenCalled();
                });
            });
        });
    });

    describe('Dialog Interaction', () => {
        it('closes dialog when cancel button is clicked', async () => {
            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(
                <DeleteProjectDialog
                    open={true}
                    onOpenChange={onOpenChange}
                    projectIds={[1]}
                    projectNames={['Test Project']}
                />
            );

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await user.click(cancelButton);

            expect(onOpenChange).toHaveBeenCalledWith(false);
        });

        it('does not call delete API when cancel is clicked', async () => {
            const mockDeleteProject = vi.mocked(projectService.deleteProject);

            const { user } = renderWithProviders(
                <DeleteProjectDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    projectIds={[1]}
                    projectNames={['Test Project']}
                />
            );

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await user.click(cancelButton);

            expect(mockDeleteProject).not.toHaveBeenCalled();
        });

        it('handles empty projectIds array', () => {
            renderWithProviders(
                <DeleteProjectDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    projectIds={[]}
                    projectNames={[]}
                />
            );

            // Should still render but delete button might be disabled
            expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
        });
    });
});
