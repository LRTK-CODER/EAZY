import * as React from "react"
import { GripVertical } from "lucide-react"
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from "react-resizable-panels"

import { cn } from "@/lib/utils"

const ResizablePanelGroup = ({
  className,
  ...props
}: React.ComponentProps<typeof PanelGroup>) => (
  <PanelGroup
    className={cn(
      "flex h-full w-full data-[panel-group-direction=vertical]:flex-col",
      className
    )}
    {...props}
  />
)

const ResizablePanel = Panel

/**
 * ResizableHandle - Drag handle between resizable panels
 * Optimized for touch targets (minimum 12px hit area via after pseudo-element)
 */
const ResizableHandle = ({
  withHandle,
  className,
  ...props
}: React.ComponentProps<typeof PanelResizeHandle> & {
  withHandle?: boolean
}) => (
  <PanelResizeHandle
    className={cn(
      // Base styles: w-1 (4px visible), after:w-3 (12px hit area)
      "relative flex w-1 items-center justify-center bg-border",
      // Hover feedback and transitions
      "transition-colors hover:bg-primary/20",
      // Hit area expansion via pseudo-element
      "after:absolute after:inset-y-0 after:left-1/2 after:w-3 after:-translate-x-1/2",
      // Focus styles
      "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-offset-1",
      // Vertical orientation overrides
      "data-[panel-group-direction=vertical]:h-1 data-[panel-group-direction=vertical]:w-full",
      "data-[panel-group-direction=vertical]:after:left-0 data-[panel-group-direction=vertical]:after:h-3",
      "data-[panel-group-direction=vertical]:after:w-full data-[panel-group-direction=vertical]:after:-translate-y-1/2",
      "data-[panel-group-direction=vertical]:after:translate-x-0",
      "[&[data-panel-group-direction=vertical]>div]:rotate-90",
      className
    )}
    {...props}
  >
    {withHandle && (
      // Handle icon: h-6 w-4 (24x16px) for better touch target
      <div className="z-10 flex h-6 w-4 items-center justify-center rounded-sm border bg-border">
        <GripVertical className="h-3 w-3" />
      </div>
    )}
  </PanelResizeHandle>
)

export { ResizablePanelGroup, ResizablePanel, ResizableHandle }
