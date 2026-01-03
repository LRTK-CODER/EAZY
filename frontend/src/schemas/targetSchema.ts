import { z } from 'zod';

/**
 * Target form validation schema
 * Used by CreateTargetForm and EditTargetForm
 */
export const targetFormSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(255, 'Name must be at most 255 characters'),
  url: z
    .string()
    .min(1, 'URL is required')
    .refine(
      (value) => {
        try {
          const url = new URL(value);
          // Ensure protocol is http or https
          return url.protocol === 'http:' || url.protocol === 'https:';
        } catch {
          return false;
        }
      },
      { message: 'URL must be valid' }
    ),
  description: z.string().optional(),
  scope: z.enum(['DOMAIN', 'SUBDOMAIN', 'URL_ONLY']),
});

/**
 * Inferred TypeScript type from targetFormSchema
 */
export type TargetFormValues = z.infer<typeof targetFormSchema>;
