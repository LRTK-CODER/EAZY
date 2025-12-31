import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
// @ts-expect-error - CreateProjectForm doesn't exist yet (TDD RED phase)
import { CreateProjectForm } from './CreateProjectForm';
import * as projectService from '@/services/projectService';
import { toast } from 'sonner';

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

describe('CreateProjectForm Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Form Rendering', () => {
        it('renders form fields and submit button', () => {
            renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            // Check for form fields
            expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/description/i)).toBeInTheDocument();

            // Check for submit button
            expect(screen.getByRole('button', { name: /create|submit/i })).toBeInTheDocument();
        });

        it('renders cancel button', () => {
            renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        });

        it('does not render when open is false', () => {
            renderWithProviders(<CreateProjectForm open={false} onOpenChange={vi.fn()} />);

            expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
        });
    });

    describe('Form Validation', () => {
        it('shows validation error when name is empty', async () => {
            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const submitButton = screen.getByRole('button', { name: /create|submit/i });

            // Try to submit without filling name
            await user.click(submitButton);

            // Wait for validation error
            await waitFor(() => {
                expect(screen.getByText(/name.*required/i)).toBeInTheDocument();
            });
        });

        it('shows validation error when name exceeds 255 characters', async () => {
            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i);
            const longName = 'a'.repeat(256); // 256 characters

            // Fill with too long name
            await user.type(nameInput, longName);

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Wait for validation error
            await waitFor(() => {
                expect(screen.getByText(/name.*255.*character/i)).toBeInTheDocument();
            });
        });

        it('accepts valid name (1-255 characters)', async () => {
            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            vi.mocked(projectService.createProject).mockResolvedValue({
                id: 1,
                name: 'Valid Project Name',
                description: null,
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            });

            const nameInput = screen.getByLabelText(/name/i);
            await user.type(nameInput, 'Valid Project Name');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Should not show validation error
            await waitFor(() => {
                expect(screen.queryByText(/name.*required/i)).not.toBeInTheDocument();
                expect(screen.queryByText(/name.*255.*character/i)).not.toBeInTheDocument();
            });
        });

        it('description field is optional', () => {
            renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const descriptionInput = screen.getByLabelText(/description/i);

            // Description should not be required
            expect(descriptionInput).not.toBeRequired();
        });
    });

    describe('Form Submission', () => {
        it('calls createProject API when form is submitted with valid data', async () => {
            const mockCreateProject = vi.mocked(projectService.createProject).mockResolvedValue({
                id: 1,
                name: 'Test Project',
                description: 'Test Description',
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            });

            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i);
            const descriptionInput = screen.getByLabelText(/description/i);

            // Fill form
            await user.type(nameInput, 'Test Project');
            await user.type(descriptionInput, 'Test Description');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Verify API was called with correct data
            await waitFor(() => {
                expect(mockCreateProject).toHaveBeenCalledWith({
                    name: 'Test Project',
                    description: 'Test Description',
                });
            });
        });

        it('calls createProject API without description when description is empty', async () => {
            const mockCreateProject = vi.mocked(projectService.createProject).mockResolvedValue({
                id: 1,
                name: 'Test Project',
                description: null,
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            });

            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i);

            // Fill only name
            await user.type(nameInput, 'Test Project');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Verify API was called with only name
            await waitFor(() => {
                expect(mockCreateProject).toHaveBeenCalledWith({
                    name: 'Test Project',
                    description: '',
                });
            });
        });

        it('shows success message after successful submission', async () => {
            vi.mocked(projectService.createProject).mockResolvedValue({
                id: 1,
                name: 'Test Project',
                description: 'Test Description',
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            });

            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i);
            await user.type(nameInput, 'Test Project');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Wait for toast.success to be called
            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith('Project created successfully');
            });
        });

        it('shows error message when API call fails', async () => {
            vi.mocked(projectService.createProject).mockRejectedValue(
                new Error('Failed to create project')
            );

            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i);
            await user.type(nameInput, 'Test Project');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Wait for toast.error to be called
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to create project');
            });
        });

        it('closes dialog after successful submission', async () => {
            vi.mocked(projectService.createProject).mockResolvedValue({
                id: 1,
                name: 'Test Project',
                description: null,
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            });

            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={onOpenChange} />);

            const nameInput = screen.getByLabelText(/name/i);
            await user.type(nameInput, 'Test Project');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Wait for dialog to close
            await waitFor(() => {
                expect(onOpenChange).toHaveBeenCalledWith(false);
            });
        });

        it('clears form after successful submission', async () => {
            vi.mocked(projectService.createProject).mockResolvedValue({
                id: 1,
                name: 'Test Project',
                description: 'Test Description',
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            });

            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
            const descriptionInput = screen.getByLabelText(/description/i) as HTMLInputElement;

            // Fill form
            await user.type(nameInput, 'Test Project');
            await user.type(descriptionInput, 'Test Description');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Wait for form to clear
            await waitFor(() => {
                expect(nameInput.value).toBe('');
                expect(descriptionInput.value).toBe('');
            });
        });
    });

    describe('Form Interaction', () => {
        it('disables submit button while submitting', async () => {
            // Mock API to delay response
            vi.mocked(projectService.createProject).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i);
            await user.type(nameInput, 'Test Project');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            // Button should be disabled immediately
            expect(submitButton).toBeDisabled();
        });

        it('disables cancel button while submitting', async () => {
            // Mock API to delay response
            vi.mocked(projectService.createProject).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={vi.fn()} />);

            const nameInput = screen.getByLabelText(/name/i);
            await user.type(nameInput, 'Test Project');

            const submitButton = screen.getByRole('button', { name: /create|submit/i });
            await user.click(submitButton);

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            // Cancel button should be disabled
            expect(cancelButton).toBeDisabled();
        });

        it('calls onOpenChange when cancel button is clicked', async () => {
            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(<CreateProjectForm open={true} onOpenChange={onOpenChange} />);

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await user.click(cancelButton);

            expect(onOpenChange).toHaveBeenCalledWith(false);
        });
    });
});
