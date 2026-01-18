import type { VariantProps } from "class-variance-authority";
import { badgeVariants } from "@/components/ui/badge";

export type HttpMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "OPTIONS"
  | "HEAD";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

const HTTP_METHOD_VARIANT_MAP: Record<HttpMethod, BadgeVariant> = {
  GET: "method-get",
  POST: "method-post",
  PUT: "method-put",
  PATCH: "method-patch",
  DELETE: "method-delete",
  OPTIONS: "method-options",
  HEAD: "method-head",
};

/**
 * Returns the Badge variant for a given HTTP method.
 * Falls back to "outline" for unknown methods.
 */
export function getHttpMethodVariant(method?: string): BadgeVariant {
  const upperMethod = method?.toUpperCase() as HttpMethod;
  return HTTP_METHOD_VARIANT_MAP[upperMethod] ?? "outline";
}

/**
 * Checks if a string is a valid HTTP method.
 */
export function isValidHttpMethod(method?: string): method is HttpMethod {
  return (method?.toUpperCase() ?? "") in HTTP_METHOD_VARIANT_MAP;
}

/**
 * List of supported HTTP methods.
 */
export const HTTP_METHODS: HttpMethod[] = [
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "HEAD",
  "OPTIONS",
];
