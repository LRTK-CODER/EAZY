import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useUpdateTarget } from '@/hooks/useTargets';
import type { Target } from '@/types/target';
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

interface EditTargetFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  target: Target;
}

export function EditTargetForm({ open, onOpenChange, target }: EditTargetFormProps) {
  const form = useForm<TargetFormValues>({
    resolver: zodResolver(targetFormSchema),
    defaultValues: {
      name: '',
      url: '',
      description: '',
      scope: 'DOMAIN',
    },
  });

  // Initialize form with target data whenever target changes
  useEffect(() => {
    form.reset({
      name: target.name,
      url: target.url,
      description: target.description || '', // Convert null to empty string
      scope: target.scope,
    });
  }, [target, form]);

  const updateTarget = useUpdateTarget();

  const onSubmit = async (data: TargetFormValues) => {
    try {
      // Prepare data - ensure description is always a string
      const targetData = {
        name: data.name,
        url: data.url,
        description: data.description || '',
        scope: data.scope,
      };

      await updateTarget.mutateAsync({
        projectId: target.project_id,
        targetId: target.id,
        data: targetData,
      });

      toast.success('Target updated successfully');

      // Close dialog
      onOpenChange(false);
    } catch {
      toast.error('Failed to update target');
    }
  };

  const isSubmitting = updateTarget.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Target</DialogTitle>
          <DialogDescription>
            Update the target details below.
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
                Update
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
