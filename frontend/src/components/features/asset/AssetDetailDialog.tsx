/**
 * AssetDetailDialog Component
 *
 * Displays detailed HTTP packet information for an Asset in a tabbed Dialog.
 * Features three tabs: Request, Response, and Metadata.
 *
 * @component
 */

import { formatDistanceToNow } from 'date-fns';
import type { Asset } from '@/types/asset';
import { parseJsonBody } from '@/utils/http';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

/**
 * Props interface for AssetDetailDialog
 */
interface AssetDetailDialogProps {
  /** Asset to display details for */
  asset: Asset;
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog open state changes */
  onOpenChange: (open: boolean) => void;
}

/**
 * Format HTTP body for display in code block
 * Parses JSON strings and pretty-prints objects
 *
 * @param body - HTTP body content (string, object, or null)
 * @returns Formatted string for display
 */
function formatHttpBody(body: unknown): string {
  const parsed = parseJsonBody(body as string | null);

  if (parsed === null) return '';
  if (typeof parsed === 'string') return parsed;
  return JSON.stringify(parsed, null, 2);
}

/**
 * AssetDetailDialog Component
 *
 * Renders a Dialog with three tabs:
 * - Request: HTTP method badge, request headers table, request body code block
 * - Response: HTTP status badge, response headers table, response body code block
 * - Metadata: Timestamps, type/source/method badges, parameters table
 */
export function AssetDetailDialog({
  asset,
  open,
  onOpenChange,
}: AssetDetailDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Asset Details</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="request" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="request">Request</TabsTrigger>
            <TabsTrigger value="response">Response</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>

          {/* Request Tab */}
          <TabsContent value="request" className="space-y-4">
            {asset.request_spec ? (
              <>
                {/* HTTP Method Badge */}
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Method:</span>
                  <Badge
                    variant={
                      asset.method === 'DELETE'
                        ? 'destructive'
                        : 'default'
                    }
                    className={
                      asset.method === 'POST'
                        ? 'bg-green-500 hover:bg-green-600'
                        : asset.method === 'PUT'
                        ? 'bg-yellow-500 hover:bg-yellow-600'
                        : ''
                    }
                  >
                    {asset.method}
                  </Badge>
                </div>

                {/* Request Headers Table */}
                {asset.request_spec.headers &&
                  typeof asset.request_spec.headers === 'object' && (
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Headers</h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Value</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {Object.entries(
                            asset.request_spec.headers as Record<string, string>
                          ).map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell className="font-medium">{key}</TableCell>
                              <TableCell>{value}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}

                {/* Request Body CodeBlock */}
                {asset.request_spec.body && (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Body</h3>
                    <pre className="bg-muted p-4 rounded-md max-h-96 overflow-auto">
                      <code className="text-sm">
                        {formatHttpBody(asset.request_spec.body)}
                      </code>
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <div className="text-sm text-muted-foreground text-center py-8">
                No request data available
              </div>
            )}
          </TabsContent>

          {/* Response Tab */}
          <TabsContent value="response" className="space-y-4">
            {asset.response_spec ? (
              <>
                {/* HTTP Status Badge */}
                {asset.response_spec.status && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Status:</span>
                    <Badge
                      variant={
                        typeof asset.response_spec.status === 'number' &&
                        asset.response_spec.status >= 500
                          ? 'destructive'
                          : 'default'
                      }
                      className={
                        typeof asset.response_spec.status === 'number' &&
                        asset.response_spec.status >= 200 &&
                        asset.response_spec.status < 300
                          ? 'bg-green-500 hover:bg-green-600'
                          : typeof asset.response_spec.status === 'number' &&
                            asset.response_spec.status >= 400 &&
                            asset.response_spec.status < 500
                          ? 'bg-yellow-500 hover:bg-yellow-600'
                          : ''
                      }
                    >
                      {String(asset.response_spec.status)}
                    </Badge>
                  </div>
                )}

                {/* Response Headers Table */}
                {asset.response_spec.headers &&
                  typeof asset.response_spec.headers === 'object' && (
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Headers</h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Value</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {Object.entries(
                            asset.response_spec.headers as Record<string, string>
                          ).map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell className="font-medium">{key}</TableCell>
                              <TableCell>{value}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}

                {/* Response Body CodeBlock */}
                {asset.response_spec.body && (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Body</h3>
                    <pre className="bg-muted p-4 rounded-md max-h-96 overflow-auto">
                      <code className="text-sm">
                        {formatHttpBody(asset.response_spec.body)}
                      </code>
                    </pre>
                  </div>
                )}
              </>
            ) : (
              <div className="text-sm text-muted-foreground text-center py-8">
                No response data available
              </div>
            )}
          </TabsContent>

          {/* Metadata Tab */}
          <TabsContent value="metadata" className="space-y-4">
            {/* Timestamps */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">First Seen:</span>
                <span className="text-sm text-muted-foreground">
                  {formatDistanceToNow(new Date(asset.first_seen_at), {
                    addSuffix: true,
                  })}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Last Seen:</span>
                <span className="text-sm text-muted-foreground">
                  {formatDistanceToNow(new Date(asset.last_seen_at), {
                    addSuffix: true,
                  })}
                </span>
              </div>
            </div>

            {/* Type, Source, Method Badges */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Type:</span>
                <Badge variant="outline">{asset.type.toUpperCase()}</Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Source:</span>
                <Badge variant="outline">{asset.source.toUpperCase()}</Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Method:</span>
                <Badge variant="outline">{asset.method}</Badge>
              </div>
            </div>

            {/* Parameters Table */}
            {asset.parameters && Object.keys(asset.parameters).length > 0 ? (
              <div>
                <h3 className="text-sm font-semibold mb-2">Parameters</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(asset.parameters).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell className="font-medium">{key}</TableCell>
                        <TableCell>
                          {typeof value === 'string'
                            ? value
                            : JSON.stringify(value)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No parameters</div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
