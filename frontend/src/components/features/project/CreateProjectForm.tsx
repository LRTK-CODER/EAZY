import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useCreateProject } from '@/hooks/useProjects';
import { projectFormSchema, type ProjectFormValues } from '@/schemas/projectSchema';
import { ProjectFormFields } from './ProjectFormFields';
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

interface CreateProjectFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectForm({ open, onOpenChange }: CreateProjectFormProps) {
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  const createProject = useCreateProject();

  const onSubmit = async (data: ProjectFormValues) => {
    try {
      // Prepare data - ensure description is always a string (empty string if not provided)
      const projectData = {
        name: data.name,
        description: data.description || '',
      };

      await createProject.mutateAsync(projectData);

      toast.success('Project created successfully');

      // Close dialog
      onOpenChange(false);

      // Clear form
      form.reset({
        name: '',
        description: '',
      });
    } catch {
      toast.error('Failed to create project');
    }
  };

  const isSubmitting = createProject.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Project</DialogTitle>
          <DialogDescription>
            Create a new project to organize your security targets.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <ProjectFormFields form={form} isSubmitting={isSubmitting} />

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
