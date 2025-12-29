import * as React from "react"
import { cn } from "@/lib/utils"

const Item = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement> & { clickable?: boolean }
>(({ className, clickable, ...props }, ref) => (
    <div
        ref={ref}
        className={cn(
            "flex w-full items-center justify-between rounded-md border border-transparent px-4 py-3 text-sm transition-colors",
            clickable && "cursor-pointer hover:bg-muted/50 hover:text-muted-foreground",
            className
        )}
        {...props}
    />
))
Item.displayName = "Item"

const ItemStart = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex items-center gap-3 text-muted-foreground", className)}
        {...props}
    />
))
ItemStart.displayName = "ItemStart"

const ItemContent = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex flex-1 flex-col gap-1 px-3", className)}
        {...props}
    />
))
ItemContent.displayName = "ItemContent"

const ItemEnd = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex items-center gap-2 text-muted-foreground", className)}
        {...props}
    />
))
ItemEnd.displayName = "ItemEnd"

export { Item, ItemStart, ItemContent, ItemEnd }
