import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonGroupProps extends React.HTMLAttributes<HTMLDivElement> {
    orientation?: "horizontal" | "vertical"
}

const ButtonGroup = React.forwardRef<HTMLDivElement, ButtonGroupProps>(
    ({ className, orientation = "horizontal", children, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={cn(
                    "inline-flex",
                    orientation === "horizontal" ? "flex-row" : "flex-col",
                    className
                )}
                {...props}
            >
                {React.Children.map(children, (child) => {
                    if (!React.isValidElement(child)) return null

                    return React.cloneElement(child as React.ReactElement<any>, {
                        className: cn(
                            // Common styles
                            "rounded-none first:rounded-l-md last:rounded-r-md focus:z-10",
                            // Horizontal specific
                            orientation === "horizontal" && [
                                "border-l-0 first:border-l",
                                "first:rounded-l-md last:rounded-r-md",
                                // Reset vertical radius if mixed
                                "first:rounded-t-none first:rounded-b-none last:rounded-t-none last:rounded-b-none",
                                // Restore logic: simplified approach for horizontal radius
                                "first:rounded-l-md last:rounded-r-md rounded-none"
                            ],
                            // Vertical specific
                            orientation === "vertical" && [
                                "border-t-0 first:border-t",
                                "first:rounded-t-md last:rounded-b-md",
                                "first:rounded-l-none first:rounded-r-none last:rounded-l-none last:rounded-r-none",
                                "rounded-none"
                            ],
                            (child.props as any).className
                        ),
                    })
                })}
            </div>
        )
    }
)
ButtonGroup.displayName = "ButtonGroup"

export { ButtonGroup }
