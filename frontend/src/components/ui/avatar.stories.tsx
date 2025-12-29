import type { Meta, StoryObj } from "@storybook/react";
import { Avatar, AvatarFallback, AvatarImage } from "./avatar";

const meta = {
    title: "UI/Avatar",
    component: Avatar,
    tags: ["autodocs"],
} satisfies Meta<typeof Avatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <Avatar {...args}>
            <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
            <AvatarFallback>CN</AvatarFallback>
        </Avatar>
    ),
};

export const Fallback: Story = {
    render: (args) => (
        <Avatar {...args}>
            <AvatarFallback>CN</AvatarFallback>
        </Avatar>
    ),
};
