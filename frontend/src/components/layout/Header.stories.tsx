import type { Meta, StoryObj } from '@storybook/react';
import { Header } from './Header';
import { MemoryRouter } from 'react-router-dom';

const meta = {
    title: 'Layout/Header',
    component: Header,
    parameters: {
        layout: 'fullscreen',
    },
    decorators: [
        (Story) => (
            <MemoryRouter>
                <Story />
            </MemoryRouter>
        ),
    ],
    tags: ['autodocs'],
} satisfies Meta<typeof Header>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
