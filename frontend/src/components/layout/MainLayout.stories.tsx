import type { Meta, StoryObj } from '@storybook/react';
import { MainLayout } from './MainLayout';
import { MemoryRouter } from 'react-router-dom';

const meta = {
    title: 'Layout/MainLayout',
    component: MainLayout,
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
} satisfies Meta<typeof MainLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        children: (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div className="p-6 bg-card text-card-foreground rounded-xl border shadow-sm">
                        Total Projects: 12
                    </div>
                    <div className="p-6 bg-card text-card-foreground rounded-xl border shadow-sm">
                        Recent Scans: 5
                    </div>
                    <div className="p-6 bg-card text-card-foreground rounded-xl border shadow-sm">
                        Vulnerabilities: 0
                    </div>
                </div>
            </div>
        )
    }
};
