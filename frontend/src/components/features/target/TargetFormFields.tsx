import type { UseFormReturn } from 'react-hook-form';
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { type TargetFormValues } from '@/schemas/targetSchema';

interface TargetFormFieldsProps {
  form: UseFormReturn<TargetFormValues>;
  isSubmitting: boolean;
}

export function TargetFormFields({ form, isSubmitting }: TargetFormFieldsProps) {
  return (
    <>
      {/* Name Field */}
      <FormField
        control={form.control}
        name="name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl>
              <Input
                placeholder="Enter target name"
                disabled={isSubmitting}
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* URL Field */}
      <FormField
        control={form.control}
        name="url"
        render={({ field }) => (
          <FormItem>
            <FormLabel>URL</FormLabel>
            <FormControl>
              <Input
                placeholder="https://example.com"
                disabled={isSubmitting}
                {...field}
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
                placeholder="Enter target description (optional)"
                disabled={isSubmitting}
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Scope Field (Select) */}
      <FormField
        control={form.control}
        name="scope"
        render={({ field }) => (
          <FormItem>
            <div className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Scope
            </div>
            <Select
              onValueChange={field.onChange}
              value={field.value}
              disabled={isSubmitting}
            >
              <FormControl>
                <SelectTrigger aria-label="target scan range selector">
                  <SelectValue placeholder="Select scope" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="DOMAIN">Domain</SelectItem>
                <SelectItem value="SUBDOMAIN">Subdomain</SelectItem>
                <SelectItem value="URL_ONLY">URL Only</SelectItem>
              </SelectContent>
            </Select>
            <input type="hidden" aria-label="scope" {...field} />
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );
}
