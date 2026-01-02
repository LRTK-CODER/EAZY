import { z } from 'zod';

/**
 * Project form validation schema
 * Used by CreateProjectForm and EditProjectForm
 */
export const projectFormSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(255, 'Name must be at most 255 characters'),
  description: z.string().optional(),
});

/**
 * Inferred TypeScript type from projectFormSchema
 */
export type ProjectFormValues = z.infer<typeof projectFormSchema>;
