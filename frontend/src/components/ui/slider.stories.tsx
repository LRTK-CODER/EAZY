import type { Meta, StoryObj } from "@storybook/react";
import { Slider } from "./slider";

const meta = {
    title: "UI/Slider",
    component: Slider,
    tags: ["autodocs"],
} satisfies Meta<typeof Slider>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <Slider defaultValue={[50]} max={100} step={1} className="w-[60%]" {...args} />
    ),
};
