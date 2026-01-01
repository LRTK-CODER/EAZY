import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { useUpdateProject } from '@/hooks/useProjects';
import type { Project } from '@/types/project';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

// Zod validation schema (same as CreateProjectForm)
const formSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(255, 'Name must be at most 255 characters'),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface EditProjectFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: Project;
}

export function EditProjectForm({ open, onOpenChange, project }: EditProjectFormProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
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

  const onSubmit = async (data: FormValues) => {
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
            {/* Name Field */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter project name"
                      {...field}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Description Field */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter project description (optional)"
                      {...field}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

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
