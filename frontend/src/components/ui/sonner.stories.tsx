import type { Meta, StoryObj } from "@storybook/react";
import { Toaster } from "./sonner";
import { toast } from "sonner";
import { Button } from "./button";

const meta = {
    title: "UI/Sonner",
    component: Toaster,
    tags: ["autodocs"],
} satisfies Meta<typeof Toaster>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <div>
            <Toaster {...args} />
            <Button
                variant="outline"
                onClick={() =>
                    toast("Event has been created", {
                        description: "Sunday, December 03, 2023 at 9:00 AM",
                        action: {
                            label: "Undo",
                            onClick: () => console.log("Undo"),
                        },
                    })
                }
            >
                Show Toast
            </Button>
        </div>
    ),
};
