import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { DeleteTargetDialog } from './DeleteTargetDialog';
import * as targetService from '@/services/targetService';
import { toast } from 'sonner';
import { AxiosError } from 'axios';
import type { Target } from '@/types/target';

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

// Mock target data
const mockTarget: Target = {
    id: 1,
    project_id: 1,
    name: 'Test Target',
    url: 'https://example.com',
    description: 'Test target description',
    scope: 'DOMAIN',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
};

describe('DeleteTargetDialog Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('Dialog Rendering', () => {
        it('renders confirmation dialog when open is true', () => {
            renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            // Should show confirmation message
            expect(screen.getByText(/are you sure.*delete/i)).toBeInTheDocument();
        });

        it('renders delete and cancel buttons', () => {
            renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
        });

        it('does not render when open is false', () => {
            renderWithProviders(
                <DeleteTargetDialog
                    open={false}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            expect(screen.queryByText(/are you sure.*delete/i)).not.toBeInTheDocument();
        });

        it('shows permanent deletion warning message', () => {
            renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
        });
    });

    describe('Delete Action', () => {
        it('calls deleteTarget API with correct project id and target id', async () => {
            const mockDeleteTarget = vi.mocked(targetService.deleteTarget).mockResolvedValue(undefined);

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            await waitFor(() => {
                expect(mockDeleteTarget).toHaveBeenCalledWith(1, 1);
            });
        });

        it('shows success toast after successful deletion', async () => {
            vi.mocked(targetService.deleteTarget).mockResolvedValue(undefined);

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith('Target deleted successfully', {
                    description: 'Related tasks and assets were also removed.',
                });
            });
        });

        it('shows error toast when deletion fails', async () => {
            vi.mocked(targetService.deleteTarget).mockRejectedValue(
                new Error('Failed to delete target')
            );

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to delete target', {
                    description: 'An unexpected error occurred. Please try again.',
                });
            });
        });

        it('closes dialog after successful deletion', async () => {
            vi.mocked(targetService.deleteTarget).mockResolvedValue(undefined);

            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={onOpenChange}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            await waitFor(() => {
                expect(onOpenChange).toHaveBeenCalledWith(false);
            });
        });

        it('disables delete button while deleting', async () => {
            vi.mocked(targetService.deleteTarget).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            // Delete button should be disabled during deletion
            expect(deleteButton).toBeDisabled();
        });

        it('disables cancel button while deleting', async () => {
            vi.mocked(targetService.deleteTarget).mockImplementation(
                () => new Promise((resolve) => setTimeout(resolve, 1000))
            );

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            // Cancel button should also be disabled during deletion
            expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
        });
    });

    describe('Dialog Interaction', () => {
        it('closes dialog when cancel button is clicked', async () => {
            const onOpenChange = vi.fn();
            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={onOpenChange}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await user.click(cancelButton);

            expect(onOpenChange).toHaveBeenCalledWith(false);
        });

        it('does not call delete API when cancel is clicked', async () => {
            const mockDeleteTarget = vi.mocked(targetService.deleteTarget);

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const cancelButton = screen.getByRole('button', { name: /cancel/i });
            await user.click(cancelButton);

            expect(mockDeleteTarget).not.toHaveBeenCalled();
        });

        it('displays target name in dialog', () => {
            renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            expect(screen.getByText(/Test Target/i)).toBeInTheDocument();
        });

        it('handles null target gracefully', () => {
            renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={null}
                    projectId={1}
                />
            );

            // Dialog should still render but delete button might be disabled
            expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
        });
    });

    describe('Error Handling', () => {
        it('shows 404 error message when target not found', async () => {
            const axiosError = new AxiosError(
                'Not Found',
                '404',
                undefined,
                undefined,
                {
                    status: 404,
                    statusText: 'Not Found',
                    data: { detail: 'Target not found' },
                    headers: {},
                    config: {} as any,
                }
            );

            vi.mocked(targetService.deleteTarget).mockRejectedValue(axiosError);

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Target not found', {
                    description: 'The target may have been already deleted.',
                });
            });
        });

        it('shows 500 error message with database error details', async () => {
            const axiosError = new AxiosError(
                'Internal Server Error',
                '500',
                undefined,
                undefined,
                {
                    status: 500,
                    statusText: 'Internal Server Error',
                    data: { detail: 'Database connection failed' },
                    headers: {},
                    config: {} as any,
                }
            );

            vi.mocked(targetService.deleteTarget).mockRejectedValue(axiosError);

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to delete target', {
                    description: 'Database error: Database connection failed',
                });
            });
        });

        it('shows success message with CASCADE information', async () => {
            vi.mocked(targetService.deleteTarget).mockResolvedValue(undefined);

            const { user } = renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            await user.click(deleteButton);

            await waitFor(() => {
                expect(toast.success).toHaveBeenCalledWith('Target deleted successfully', {
                    description: 'Related tasks and assets were also removed.',
                });
            });
        });

        it('shows CASCADE warning in dialog description', () => {
            renderWithProviders(
                <DeleteTargetDialog
                    open={true}
                    onOpenChange={vi.fn()}
                    target={mockTarget}
                    projectId={1}
                />
            );

            expect(
                screen.getByText(/permanently delete the target and all related tasks/i)
            ).toBeInTheDocument();
        });
    });
});
