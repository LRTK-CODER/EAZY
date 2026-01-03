import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { CreateTargetForm } from './CreateTargetForm';
import * as targetService from '@/services/targetService';
import { toast } from 'sonner';

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

describe('CreateTargetForm Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Form Rendering', () => {
    it('renders form fields and submit button', () => {
      renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      // Check for form fields
      expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/url/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/scope/i)).toBeInTheDocument();

      // Check for submit button
      expect(screen.getByRole('button', { name: /create|submit/i })).toBeInTheDocument();
    });

    it('renders cancel button', () => {
      renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('does not render when open is false', () => {
      renderWithProviders(<CreateTargetForm open={false} onOpenChange={vi.fn()} projectId={1} />);

      expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation error when name is empty', async () => {
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const submitButton = screen.getByRole('button', { name: /create|submit/i });

      // Try to submit without filling name
      await user.click(submitButton);

      // Wait for validation error
      await waitFor(() => {
        expect(screen.getByText(/name.*required/i)).toBeInTheDocument();
      });
    });

    it('shows validation error when name exceeds 255 characters', async () => {
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

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

    it('shows validation error when url is empty', async () => {
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const submitButton = screen.getByRole('button', { name: /create|submit/i });

      // Try to submit without filling url
      await user.click(submitButton);

      // Wait for validation error
      await waitFor(() => {
        expect(screen.getByText(/url.*required/i)).toBeInTheDocument();
      });
    });

    it('shows validation error when url is invalid', async () => {
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);

      // Fill with valid name but invalid URL
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'not-a-valid-url');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Wait for validation error
      await waitFor(() => {
        expect(screen.getByText(/url.*valid/i)).toBeInTheDocument();
      });
    });

    it('accepts valid name (1-255 characters)', async () => {
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Valid Target Name',
        url: 'https://example.com',
        description: null,
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Valid Target Name');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Should not show validation error
      await waitFor(() => {
        expect(screen.queryByText(/name.*required/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/name.*255.*character/i)).not.toBeInTheDocument();
      });
    });

    it('accepts valid HTTP URL', async () => {
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Test Target',
        url: 'http://example.com',
        description: null,
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'http://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Should not show validation error
      await waitFor(() => {
        expect(screen.queryByText(/url.*required/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/url.*valid/i)).not.toBeInTheDocument();
      });
    });

    it('accepts valid HTTPS URL', async () => {
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Test Target',
        url: 'https://example.com',
        description: null,
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Should not show validation error
      await waitFor(() => {
        expect(screen.queryByText(/url.*required/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/url.*valid/i)).not.toBeInTheDocument();
      });
    });

    it('description field is optional', () => {
      renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const descriptionInput = screen.getByLabelText(/description/i);

      // Description should not be required
      expect(descriptionInput).not.toBeRequired();
    });

    it('scope field has default value DOMAIN', () => {
      renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      // Check that DOMAIN is selected by default
      const scopeInput = screen.getByLabelText(/scope/i);
      expect(scopeInput).toHaveValue('DOMAIN');
    });
  });

  describe('Form Submission', () => {
    it('calls createTarget API when form is submitted with valid data', async () => {
      const mockCreateTarget = vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Test Target',
        url: 'https://example.com',
        description: 'Test Description',
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      const descriptionInput = screen.getByLabelText(/description/i);

      // Fill form
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');
      await user.type(descriptionInput, 'Test Description');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Verify API was called with correct data
      await waitFor(() => {
        expect(mockCreateTarget).toHaveBeenCalledWith(1, {
          name: 'Test Target',
          url: 'https://example.com',
          description: 'Test Description',
          scope: 'DOMAIN',
        });
      });
    });

    it('calls createTarget API without description when description is empty', async () => {
      const mockCreateTarget = vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Test Target',
        url: 'https://example.com',
        description: null,
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);

      // Fill only required fields
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Verify API was called with only required fields
      await waitFor(() => {
        expect(mockCreateTarget).toHaveBeenCalledWith(1, {
          name: 'Test Target',
          url: 'https://example.com',
          description: '',
          scope: 'DOMAIN',
        });
      });
    });

    it('shows success message after successful submission', async () => {
      vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Test Target',
        url: 'https://example.com',
        description: null,
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Wait for toast.success to be called
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Target created successfully');
      });
    });

    it('shows error message when API call fails', async () => {
      vi.mocked(targetService.createTarget).mockRejectedValue(
        new Error('Failed to create target')
      );

      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Wait for toast.error to be called
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to create target');
      });
    });

    it('closes dialog after successful submission', async () => {
      vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Test Target',
        url: 'https://example.com',
        description: null,
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const onOpenChange = vi.fn();
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={onOpenChange} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Wait for dialog to close
      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it('clears form after successful submission', async () => {
      vi.mocked(targetService.createTarget).mockResolvedValue({
        id: 1,
        project_id: 1,
        name: 'Test Target',
        url: 'https://example.com',
        description: 'Test Description',
        scope: 'DOMAIN',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      });

      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
      const urlInput = screen.getByLabelText(/url/i) as HTMLInputElement;
      const descriptionInput = screen.getByLabelText(/description/i) as HTMLInputElement;

      // Fill form
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');
      await user.type(descriptionInput, 'Test Description');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Wait for form to clear
      await waitFor(() => {
        expect(nameInput.value).toBe('');
        expect(urlInput.value).toBe('');
        expect(descriptionInput.value).toBe('');
      });
    });
  });

  describe('Form Interaction', () => {
    it('disables submit button while submitting', async () => {
      // Mock API to delay response
      vi.mocked(targetService.createTarget).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      // Button should be disabled immediately
      expect(submitButton).toBeDisabled();
    });

    it('disables cancel button while submitting', async () => {
      // Mock API to delay response
      vi.mocked(targetService.createTarget).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={vi.fn()} projectId={1} />);

      const nameInput = screen.getByLabelText(/name/i);
      const urlInput = screen.getByLabelText(/url/i);
      await user.type(nameInput, 'Test Target');
      await user.type(urlInput, 'https://example.com');

      const submitButton = screen.getByRole('button', { name: /create|submit/i });
      await user.click(submitButton);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      // Cancel button should be disabled
      expect(cancelButton).toBeDisabled();
    });

    it('calls onOpenChange when cancel button is clicked', async () => {
      const onOpenChange = vi.fn();
      const { user } = renderWithProviders(<CreateTargetForm open={true} onOpenChange={onOpenChange} projectId={1} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
