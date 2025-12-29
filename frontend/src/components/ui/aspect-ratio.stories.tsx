import type { Meta, StoryObj } from "@storybook/react";
import { AspectRatio } from "./aspect-ratio";

const meta = {
    title: "UI/AspectRatio",
    component: AspectRatio,
    tags: ["autodocs"],
} satisfies Meta<typeof AspectRatio>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <div className="w-[450px]">
            <AspectRatio ratio={16 / 9} className="bg-muted" {...args}>
                <img
                    src="https://images.unsplash.com/photo-1588345921523-c2dcdb7f1dcd?w=800&dpr=2&q=80"
                    alt="Photo by Drew Beamer"
                    className="h-full w-full rounded-md object-cover"
                />
            </AspectRatio>
        </div>
    ),
};
