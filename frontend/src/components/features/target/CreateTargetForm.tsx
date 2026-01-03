import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useCreateTarget } from '@/hooks/useTargets';
import { targetFormSchema, type TargetFormValues } from '@/schemas/targetSchema';
import { TargetFormFields } from './TargetFormFields';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Form } from '@/components/ui/form';
import { Button } from '@/components/ui/button';

interface CreateTargetFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: number;
}

export function CreateTargetForm({ open, onOpenChange, projectId }: CreateTargetFormProps) {
  const form = useForm<TargetFormValues>({
    resolver: zodResolver(targetFormSchema),
    defaultValues: {
      name: '',
      url: '',
      description: '',
      scope: 'DOMAIN',
    },
  });

  const createTarget = useCreateTarget();

  const onSubmit = async (data: TargetFormValues) => {
    try {
      // Prepare data - ensure description is always a string (empty string if not provided)
      const targetData = {
        name: data.name,
        url: data.url,
        description: data.description || '',
        scope: data.scope,
      };

      await createTarget.mutateAsync({ projectId, data: targetData });

      toast.success('Target created successfully');

      // Close dialog
      onOpenChange(false);

      // Clear form
      form.reset({
        name: '',
        url: '',
        description: '',
        scope: 'DOMAIN',
      });
    } catch {
      toast.error('Failed to create target');
    }
  };

  const isSubmitting = createTarget.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Target</DialogTitle>
          <DialogDescription>
            Create a new target for security scanning.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <TargetFormFields form={form} isSubmitting={isSubmitting} />

            {/* Form Actions */}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                Create
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
