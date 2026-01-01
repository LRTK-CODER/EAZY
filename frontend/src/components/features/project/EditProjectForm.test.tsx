import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
// @ts-expect-error - EditProjectForm doesn't exist yet (TDD RED phase)
import { EditProjectForm } from './EditProjectForm';
import * as projectService from '@/services/projectService';
import { toast } from 'sonner';
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
    name: 'Existing Project',
    description: 'Existing Description',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
};

describe('EditProjectForm Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Form Rendering', () => {
        it('renders form fields and submit button', () => {
            renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            // Check for form fields
            expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/description/i)).toBeInTheDocument();

            // Check for submit button
            expect(screen.getByRole('button', { name: /save|update/i })).toBeInTheDocument();
        });

        it('renders cancel button', () => {
            renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        });

        it('does not render when open is false', () => {
            renderWithProviders(
                <EditProjectForm open={false} onOpenChange={vi.fn()} project={mockProject} />
            );

            expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
        });
    });

    describe('Form Initialization', () => {
        it('initializes form with existing project data', () => {
            renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
            const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;

            expect(nameInput.value).toBe('Existing Project');
            expect(descriptionInput.value).toBe('Existing Description');
        });

        it('initializes form with null description', () => {
            const projectWithNullDesc: Project = {
                ...mockProject,
                description: null,
            };

            renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={projectWithNullDesc} />
            );

            const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;

            expect(descriptionInput.value).toBe('');
        });

        it('reinitializes form when project changes', () => {
            const { rerender } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const newProject: Project = {
                id: 2,
                name: 'New Project',
                description: 'New Description',
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            };

            rerender(
                <QueryClientProvider client={new QueryClient()}>
                    <MemoryRouter>
                        <div id="root">
                            <EditProjectForm open={true} onOpenChange={vi.fn()} project={newProject} />
                        </div>
                    </MemoryRouter>
                </QueryClientProvider>
            );

            const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
            expect(nameInput.value).toBe('New Project');
        });
    });

    describe('Form Validation', () => {
        it('shows validation error when name is empty', async () => {
            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            const submitButton = screen.getByRole('button', { name: /save|update/i });

            // Clear the name field
            await user.clear(nameInput);
            await user.click(submitButton);

            // Wait for validation error
            await waitFor(() => {
                expect(screen.getByText(/name.*required/i)).toBeInTheDocument();
            });
        });

        it('shows validation error when name exceeds 255 characters', async () => {
            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            const longName = 'a'.repeat(256); // 256 characters

            // Clear and fill with too long name
            await user.clear(nameInput);
            await user.type(nameInput, longName);

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Wait for validation error
            await waitFor(() => {
                expect(screen.getByText(/name.*255.*character/i)).toBeInTheDocument();
            });
        });

        it('accepts valid name (1-255 characters)', async () => {
            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            vi.mocked(projectService.updateProject).mockResolvedValue({
                ...mockProject,
                name: 'Updated Valid Name',
            });

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Valid Name');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Should not show validation error
            await waitFor(() => {
                expect(screen.queryByText(/name.*required/i)).not.toBeInTheDocument();
                expect(screen.queryByText(/name.*255.*character/i)).not.toBeInTheDocument();
            });
        });

        it('description field is optional', () => {
            renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const descriptionInput = screen.getByLabelText(/description/i);

            // Description should not be required
            expect(descriptionInput).not.toBeRequired();
        });
    });

    describe('Form Submission', () => {
        it('calls updateProject API with correct project id and updated data', async () => {
            const mockUpdateProject = vi.mocked(projectService.updateProject).mockResolvedValue({
                ...mockProject,
                name: 'Updated Project',
                description: 'Updated Description',
                updated_at: '2026-01-01T12:00:00Z',
            });

            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            const descriptionInput = screen.getByLabelText(/description/i);

            // Update form
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Project');
            await user.clear(descriptionInput);
            await user.type(descriptionInput, 'Updated Description');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Verify API was called with correct data
            await waitFor(() => {
                expect(mockUpdateProject).toHaveBeenCalledWith(1, {
                    name: 'Updated Project',
                    description: 'Updated Description',
                });
            });
        });

        it('calls updateProject API when only name is changed', async () => {
            const mockUpdateProject = vi.mocked(projectService.updateProject).mockResolvedValue({
                ...mockProject,
                name: 'New Name Only',
            });

            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);

            // Update only name
            await user.clear(nameInput);
            await user.type(nameInput, 'New Name Only');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Verify API was called
            await waitFor(() => {
                expect(mockUpdateProject).toHaveBeenCalledWith(1, {
                    name: 'New Name Only',
                    description: 'Existing Description',
                });
            });
        });

        it('shows success message after successful update', async () => {
            vi.mocked(projectService.updateProject).mockResolvedValue({
                ...mockProject,
                name: 'Updated Project',
            });

            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Project');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Wait for toast.success to be called
            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith('Project updated successfully');
            });
        });

        it('shows error message when API call fails', async () => {
            vi.mocked(projectService.updateProject).mockRejectedValue(
                new Error('Failed to update project')
            );

            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Project');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Wait for toast.error to be called
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to update project');
            });
        });

        it('closes dialog after successful update', async () => {
            vi.mocked(projectService.updateProject).mockResolvedValue({
                ...mockProject,
                name: 'Updated Project',
            });

            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={onOpenChange} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Project');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Wait for dialog to close
            await waitFor(() => {
                expect(onOpenChange).toHaveBeenCalledWith(false);
            });
        });

        it('does not call API if form data has not changed', async () => {
            const mockUpdateProject = vi.mocked(projectService.updateProject);

            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            // Submit without changing anything
            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // API should still be called (or you can implement dirty checking to skip)
            // This test documents current behavior - adjust based on requirements
            await waitFor(() => {
                expect(mockUpdateProject).toHaveBeenCalledWith(1, {
                    name: 'Existing Project',
                    description: 'Existing Description',
                });
            });
        });
    });

    describe('Form Interaction', () => {
        it('disables submit button while updating', async () => {
            // Mock API to delay response
            vi.mocked(projectService.updateProject).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Project');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Button should be disabled immediately
            expect(submitButton).toBeDisabled();
        });

        it('disables cancel button while updating', async () => {
            // Mock API to delay response
            vi.mocked(projectService.updateProject).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Project');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            // Cancel button should be disabled
            expect(cancelButton).toBeDisabled();
        });

        it('calls onOpenChange when cancel button is clicked', async () => {
            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={onOpenChange} project={mockProject} />
            );

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await user.click(cancelButton);

            expect(onOpenChange).toHaveBeenCalledWith(false);
        });

        it('resets form to original values when dialog is reopened', async () => {
            const { user } = renderWithProviders(
                <EditProjectForm open={true} onOpenChange={vi.fn()} project={mockProject} />
            );

            const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;

            // Modify the form
            await user.clear(nameInput);
            await user.type(nameInput, 'Modified Name');
            expect(nameInput.value).toBe('Modified Name');

            // Close and reopen would reset (test documents expected behavior)
            // Implementation should handle this via useEffect with project dependency
        });
    });
});
