/**
 * AssetDetailPanel Component
 *
 * Displays detailed HTTP packet information for a selected Asset in a panel.
 * Used as the right panel in the AssetExplorer split view.
 * Features three tabs: Request, Response, and Metadata.
 *
 * @component
 */

import { formatDistanceToNow } from 'date-fns';
import { FileText } from 'lucide-react';
import type { Asset } from '@/types/asset';
import { parseJsonBody } from '@/utils/http';
import { inferType } from '@/utils/parameterType';
import { cn } from '@/lib/utils';
import { CodeBlock } from '@/components/ui/code-block';
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

interface AssetDetailPanelProps {
  asset: Asset | null;
  className?: string;
}

function formatHttpBody(body: unknown): string {
  const parsed = parseJsonBody(body as string | null);
  if (parsed === null) return '';
  if (typeof parsed === 'string') return parsed;
  return JSON.stringify(parsed, null, 2);
}

function getMethodBadgeClass(method: string): string {
  switch (method.toUpperCase()) {
    case 'POST':
      return 'bg-green-500 hover:bg-green-600';
    case 'PUT':
      return 'bg-yellow-500 hover:bg-yellow-600';
    default:
      return '';
  }
}

function getMethodBadgeVariant(method: string): 'default' | 'destructive' {
  return method.toUpperCase() === 'DELETE' ? 'destructive' : 'default';
}

function getStatusBadgeClass(status: number): string {
  if (status >= 200 && status < 300) return 'bg-green-500 hover:bg-green-600';
  if (status >= 400 && status < 500) return 'bg-yellow-500 hover:bg-yellow-600';
  return '';
}

function getStatusBadgeVariant(status: number): 'default' | 'destructive' {
  return status >= 500 ? 'destructive' : 'default';
}

export function AssetDetailPanel({ asset, className }: AssetDetailPanelProps) {
  if (!asset) {
    return (
      <div className={cn('flex flex-col items-center justify-center h-full text-muted-foreground p-8', className)}>
        <FileText className="h-12 w-12 mb-4 opacity-50" data-testid="empty-state-icon" />
        <h3 className="text-lg font-medium mb-1">No asset selected</h3>
        <p className="text-sm text-center">Select an asset from the tree view to see its details</p>
      </div>
    );
  }

  return (
    <div className={cn('h-full flex flex-col overflow-hidden', className)}>
      <div className="flex items-center gap-2 p-4 border-b shrink-0">
        <Badge
          variant={getMethodBadgeVariant(asset.method)}
          className={cn('shrink-0', getMethodBadgeClass(asset.method))}
          data-testid="method-badge-header"
        >
          {asset.method}
        </Badge>
        <span className="text-sm font-mono truncate" title={asset.url}>
          {asset.url}
        </span>
      </div>

      <Tabs defaultValue="request" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="grid w-full grid-cols-3 shrink-0 mx-4 mt-4" style={{ width: 'calc(100% - 2rem)' }}>
          <TabsTrigger value="request">Request</TabsTrigger>
          <TabsTrigger value="response">Response</TabsTrigger>
          <TabsTrigger value="metadata">Metadata</TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-auto p-4">
          <TabsContent value="request" className="mt-0 h-full" data-testid="request-tab-content">
            {asset.request_spec ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Method:</span>
                  <Badge
                    variant={getMethodBadgeVariant(asset.method)}
                    className={getMethodBadgeClass(asset.method)}
                  >
                    {asset.method}
                  </Badge>
                </div>

                {asset.request_spec.headers &&
                  typeof asset.request_spec.headers === 'object' ? (
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
                              <TableCell className="break-all">{value}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : null}

                {asset.request_spec.body ? (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Body</h3>
                    <CodeBlock
                      code={formatHttpBody(asset.request_spec.body)}
                      contentType={
                        asset.request_spec.headers &&
                        typeof asset.request_spec.headers === 'object'
                          ? (asset.request_spec.headers as Record<string, string>)['Content-Type']
                          : undefined
                      }
                      data-testid="request-body"
                    />
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground text-center py-8">
                No request data available
              </div>
            )}
          </TabsContent>

          <TabsContent value="response" className="mt-0 h-full" data-testid="response-tab-content">
            {asset.response_spec ? (
              <div className="space-y-4">
                {asset.response_spec.status !== undefined && asset.response_spec.status !== null && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Status:</span>
                    <Badge
                      variant={getStatusBadgeVariant(Number(asset.response_spec.status))}
                      className={getStatusBadgeClass(Number(asset.response_spec.status))}
                      data-testid="status-badge"
                    >
                      {String(asset.response_spec.status)}
                    </Badge>
                  </div>
                )}

                {asset.response_spec.headers &&
                  typeof asset.response_spec.headers === 'object' ? (
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
                              <TableCell className="break-all">{value}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : null}

                {asset.response_spec.body ? (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Body</h3>
                    <CodeBlock
                      code={formatHttpBody(asset.response_spec.body)}
                      contentType={
                        asset.response_spec.headers &&
                        typeof asset.response_spec.headers === 'object'
                          ? (asset.response_spec.headers as Record<string, string>)['Content-Type']
                          : undefined
                      }
                      data-testid="response-body"
                    />
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground text-center py-8">
                No response data available
              </div>
            )}
          </TabsContent>

          <TabsContent value="metadata" className="mt-0 h-full" data-testid="metadata-tab-content">
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">First Seen:</span>
                  <span className="text-sm text-muted-foreground">
                    {formatDistanceToNow(new Date(asset.first_seen_at), { addSuffix: true })}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Last Seen:</span>
                  <span className="text-sm text-muted-foreground">
                    {formatDistanceToNow(new Date(asset.last_seen_at), { addSuffix: true })}
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Type:</span>
                  <Badge variant="outline" data-testid="type-badge">
                    {asset.type.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Source:</span>
                  <Badge variant="outline" data-testid="source-badge">
                    {asset.source.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Method:</span>
                  <Badge variant="outline">{asset.method}</Badge>
                </div>
              </div>

              {asset.parameters && Object.keys(asset.parameters).length > 0 ? (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Parameters</h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Value</TableHead>
                        <TableHead>Type</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(asset.parameters).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell className="font-medium">{key}</TableCell>
                          <TableCell className="break-all">
                            {typeof value === 'string' ? value : JSON.stringify(value)}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-xs">
                              {inferType(value)}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">No parameters</div>
              )}
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

export default AssetDetailPanel;
