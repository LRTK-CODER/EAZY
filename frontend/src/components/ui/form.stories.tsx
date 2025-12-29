import type { Meta, StoryObj } from "@storybook/react";
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "./button"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "./form"
import { Input } from "./input"
import { toast } from "sonner"
import { Toaster } from "./sonner";

const FormSchema = z.object({
    username: z.string().min(2, {
        message: "Username must be at least 2 characters.",
    }),
})

const meta = {
    title: "UI/Form",
    component: Form,
    tags: ["autodocs"],
} satisfies Meta<typeof Form>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => {
        const form = useForm<z.infer<typeof FormSchema>>({
            resolver: zodResolver(FormSchema),
            defaultValues: {
                username: "",
            },
        })

        function onSubmit(data: z.infer<typeof FormSchema>) {
            toast("You submitted the following values:", {
                description: (
                    <pre className="mt-2 w-[340px] rounded-md bg-slate-950 p-4 code">
                        <code className="text-white">{JSON.stringify(data, null, 2)}</code>
                    </pre>
                ),
            })
        }
        return (
            <div className="space-y-6">
                <Toaster />
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="w-2/3 space-y-6">
                        <FormField
                            control={form.control}
                            name="username"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Username</FormLabel>
                                    <FormControl>
                                        <Input placeholder="shadcn" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        This is your public display name.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <Button type="submit">Submit</Button>
                    </form>
                </Form>
            </div>
        );
    },
};
