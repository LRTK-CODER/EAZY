import type { Meta, StoryObj } from "@storybook/react";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "./tooltip";
import { Button } from "./button";

const meta = {
    title: "UI/Tooltip",
    component: Tooltip,
    tags: ["autodocs"],
} satisfies Meta<typeof Tooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <TooltipProvider>
            <Tooltip {...args}>
                <TooltipTrigger asChild>
                    <Button variant="outline">Hover</Button>
                </TooltipTrigger>
                <TooltipContent>
                    <p>Add to library</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    ),
};
