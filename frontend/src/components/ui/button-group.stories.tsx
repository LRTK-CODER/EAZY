import type { Meta, StoryObj } from "@storybook/react"
import { Button } from "./button"
import { ButtonGroup } from "./button-group"
import { ChevronDown } from "lucide-react"

const meta = {
    title: "UI/ButtonGroup",
    component: ButtonGroup,
    tags: ["autodocs"],
    argTypes: {
        orientation: {
            control: "radio",
            options: ["horizontal", "vertical"],
        },
    },
} satisfies Meta<typeof ButtonGroup>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
    render: (args) => (
        <ButtonGroup {...args}>
            <Button variant="outline">One</Button>
            <Button variant="outline">Two</Button>
            <Button variant="outline">Three</Button>
        </ButtonGroup>
    ),
}

export const Vertical: Story = {
    args: {
        orientation: "vertical",
    },
    render: (args) => (
        <ButtonGroup {...args}>
            <Button variant="outline">One</Button>
            <Button variant="outline">Two</Button>
            <Button variant="outline">Three</Button>
        </ButtonGroup>
    ),
}

export const MixedVariants: Story = {
    render: (args) => (
        <ButtonGroup {...args}>
            <Button>Save</Button>
            <Button variant="outline">Cancel</Button>
        </ButtonGroup>
    ),
}

export const WithIcons: Story = {
    render: (args) => (
        <ButtonGroup {...args}>
            <Button variant="outline">Action</Button>
            <Button variant="outline" size="icon">
                <ChevronDown className="h-4 w-4" />
            </Button>
        </ButtonGroup>
    ),
}
