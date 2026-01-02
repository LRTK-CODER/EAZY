import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useUpdateProject } from '@/hooks/useProjects';
import type { Project } from '@/types/project';
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

interface EditProjectFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: Project;
}

export function EditProjectForm({ open, onOpenChange, project }: EditProjectFormProps) {
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  // Initialize form with project data whenever project changes
  useEffect(() => {
    form.reset({
      name: project.name,
      description: project.description || '', // Convert null to empty string
    });
  }, [project, form]);

  const updateProject = useUpdateProject();

  const onSubmit = async (data: ProjectFormValues) => {
    try {
      // Prepare data - ensure description is always a string
      const projectData = {
        name: data.name,
        description: data.description || '',
      };

      await updateProject.mutateAsync({
        id: project.id,
        data: projectData,
      });

      toast.success('Project updated successfully');

      // Close dialog
      onOpenChange(false);
    } catch {
      toast.error('Failed to update project');
    }
  };

  const isSubmitting = updateProject.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Project</DialogTitle>
          <DialogDescription>
            Update the project details below.
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
                Update
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
