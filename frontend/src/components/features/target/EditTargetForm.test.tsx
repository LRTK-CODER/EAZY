import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { EditTargetForm } from './EditTargetForm';
import * as targetService from '@/services/targetService';
import { toast } from 'sonner';
import type { Target, TargetScope } from '@/types/target';

// Mock the target service
vi.mock('@/services/targetService');

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

const mockTarget: Target = {
    id: 1,
    project_id: 1,
    name: 'Existing Target',
    url: 'https://example.com',
    description: 'Test description',
    scope: 'DOMAIN' as TargetScope,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
};

describe('EditTargetForm Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Form Rendering', () => {
        it('renders form fields pre-filled with existing target data', () => {
            renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            // Check for form fields
            expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/url/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/scope/i)).toBeInTheDocument();

            // Check for submit button
            expect(screen.getByRole('button', { name: /save|update/i })).toBeInTheDocument();
        });

        it('renders cancel button', () => {
            renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        });

        it('does not render when open is false', () => {
            renderWithProviders(
                <EditTargetForm open={false} onOpenChange={vi.fn()} target={mockTarget} />
            );

            expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
        });
    });

    describe('Form Initialization', () => {
        it('initializes form with target name', () => {
            renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
            expect(nameInput.value).toBe('Existing Target');
        });

        it('initializes form with target url', () => {
            renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const urlInput = screen.getByLabelText(/url/i) as HTMLInputElement;
            expect(urlInput.value).toBe('https://example.com');
        });

        it('initializes form with target description', () => {
            renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;
            expect(descriptionInput.value).toBe('Test description');
        });

        it('initializes form with target scope', () => {
            renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const scopeInput = screen.getByLabelText(/scope/i) as HTMLSelectElement;
            expect(scopeInput.value).toBe('DOMAIN');
        });

        it('handles null description', () => {
            const targetWithNullDesc: Target = {
                ...mockTarget,
                description: null,
            };

            renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={targetWithNullDesc} />
            );

            const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;
            expect(descriptionInput.value).toBe('');
        });

        it('updates form when target prop changes', () => {
            const { rerender } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const newTarget: Target = {
                id: 2,
                project_id: 1,
                name: 'New Target',
                url: 'https://new-example.com',
                description: 'New description',
                scope: 'SUBDOMAIN' as TargetScope,
                created_at: '2026-01-02T00:00:00Z',
                updated_at: '2026-01-02T00:00:00Z',
            };

            rerender(
                <QueryClientProvider client={new QueryClient()}>
                    <MemoryRouter>
                        <div id="root">
                            <EditTargetForm open={true} onOpenChange={vi.fn()} target={newTarget} />
                        </div>
                    </MemoryRouter>
                </QueryClientProvider>
            );

            const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
            expect(nameInput.value).toBe('New Target');
        });
    });

    describe('Form Validation', () => {
        it('shows validation error when name is cleared', async () => {
            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
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

        it('shows validation error when url is cleared', async () => {
            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const urlInput = screen.getByLabelText(/url/i);
            const submitButton = screen.getByRole('button', { name: /save|update/i });

            // Clear the url field
            await user.clear(urlInput);
            await user.click(submitButton);

            // Wait for validation error
            await waitFor(() => {
                expect(screen.getByText(/url.*required/i)).toBeInTheDocument();
            });
        });

        it('shows validation error when url is invalid', async () => {
            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const urlInput = screen.getByLabelText(/url/i);
            const submitButton = screen.getByRole('button', { name: /save|update/i });

            // Change to invalid URL
            await user.clear(urlInput);
            await user.type(urlInput, 'not-a-valid-url');
            await user.click(submitButton);

            // Wait for validation error
            await waitFor(() => {
                expect(screen.getByText(/url.*valid/i)).toBeInTheDocument();
            });
        });

        it('accepts valid modifications', async () => {
            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            vi.mocked(targetService.updateTarget).mockResolvedValue({
                ...mockTarget,
                name: 'Updated Target',
                url: 'https://updated-example.com',
            });

            const nameInput = screen.getByLabelText(/name/i);
            const urlInput = screen.getByLabelText(/url/i);

            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Target');
            await user.clear(urlInput);
            await user.type(urlInput, 'https://updated-example.com');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Should not show validation errors
            await waitFor(() => {
                expect(screen.queryByText(/name.*required/i)).not.toBeInTheDocument();
                expect(screen.queryByText(/url.*required/i)).not.toBeInTheDocument();
                expect(screen.queryByText(/url.*valid/i)).not.toBeInTheDocument();
            });
        });
    });

    describe('Form Submission', () => {
        it('calls useUpdateTarget with target id and modified data', async () => {
            const mockUpdateTarget = vi.mocked(targetService.updateTarget).mockResolvedValue({
                ...mockTarget,
                name: 'Updated Target',
                url: 'https://updated-example.com',
                description: 'Updated description',
                scope: 'SUBDOMAIN' as TargetScope,
                updated_at: '2026-01-01T12:00:00Z',
            });

            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            const urlInput = screen.getByLabelText(/url/i);
            const descriptionInput = screen.getByLabelText(/description/i);

            // Update form
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Target');
            await user.clear(urlInput);
            await user.type(urlInput, 'https://updated-example.com');
            await user.clear(descriptionInput);
            await user.type(descriptionInput, 'Updated description');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Verify API was called with correct data
            await waitFor(() => {
                expect(mockUpdateTarget).toHaveBeenCalledWith(1, {
                    name: 'Updated Target',
                    url: 'https://updated-example.com',
                    description: 'Updated description',
                    scope: 'DOMAIN',
                });
            });
        });

        it('shows success toast after successful update', async () => {
            vi.mocked(targetService.updateTarget).mockResolvedValue({
                ...mockTarget,
                name: 'Updated Target',
            });

            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Target');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Wait for toast.success to be called
            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith('Target updated successfully');
            });
        });

        it('shows error toast when API call fails', async () => {
            vi.mocked(targetService.updateTarget).mockRejectedValue(
                new Error('Failed to update target')
            );

            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Target');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Wait for toast.error to be called
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to update target');
            });
        });

        it('closes dialog after successful update', async () => {
            vi.mocked(targetService.updateTarget).mockResolvedValue({
                ...mockTarget,
                name: 'Updated Target',
            });

            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={onOpenChange} target={mockTarget} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Target');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Wait for dialog to close
            await waitFor(() => {
                expect(onOpenChange).toHaveBeenCalledWith(false);
            });
        });
    });

    describe('Form Interaction', () => {
        it('disables submit button while updating', async () => {
            // Mock API to delay response
            vi.mocked(targetService.updateTarget).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Target');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            // Button should be disabled immediately
            expect(submitButton).toBeDisabled();
        });

        it('disables cancel button while updating', async () => {
            // Mock API to delay response
            vi.mocked(targetService.updateTarget).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={vi.fn()} target={mockTarget} />
            );

            const nameInput = screen.getByLabelText(/name/i);
            await user.clear(nameInput);
            await user.type(nameInput, 'Updated Target');

            const submitButton = screen.getByRole('button', { name: /save|update/i });
            await user.click(submitButton);

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            // Cancel button should be disabled
            expect(cancelButton).toBeDisabled();
        });

        it('calls onOpenChange when cancel button is clicked', async () => {
            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(
                <EditTargetForm open={true} onOpenChange={onOpenChange} target={mockTarget} />
            );

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await user.click(cancelButton);

            expect(onOpenChange).toHaveBeenCalledWith(false);
        });
    });
});
