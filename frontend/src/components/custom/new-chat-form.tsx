import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Button } from "@/components/ui/button"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Textarea } from "../ui/textarea"
import axios from "axios"
import { useRouter } from "next/navigation"
import { useContext } from "react"
import { ChatStateContext } from "@/context/chat-state"


const formSchema = z.object({
    age: z
        .string()
        .min(1, "Age is required")
        .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
            message: "Age must be a positive number",
        }),
    gender: z.enum(["male", "female", "other"], {
        required_error: "Gender is required",
    }),
    conditions: z
        .string()
        .optional()
});




export default function NewChatForm() {

    const router = useRouter()
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            age: "",
            conditions: "",
            gender: "female"

        },
    })

    const { addChat } = useContext(ChatStateContext);

    async function onSubmit(values: z.infer<typeof formSchema>) {

        const resp = await axios.post('/api/new-chat', {}, {
            withCredentials: true,
        })

        console.log('Form values:', values);

        addChat?.({
            chat_id: resp.data.chatId,
            info: { name: resp.data.info.name }
        });
        
        router.push(`/${resp.data.chatId}`)

    }
    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="h-fit flex flex-col gap-4 w-sm p-4 bg-card shadow-sm rounded-lg">
                <FormField
                    control={form.control}
                    name="age"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Age</FormLabel>
                            <FormControl>
                                <Input placeholder="Enter Age" {...field} />
                            </FormControl>
                            <FormDescription>
                                enter age in years
                            </FormDescription>

                            <FormMessage className="min-h-4" />
                        </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="gender"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Gender</FormLabel>
                            <FormControl>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                    <SelectTrigger className="w-full">
                                        <SelectValue placeholder="Select gender" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="male">Male</SelectItem>
                                        <SelectItem value="female">Female</SelectItem>
                                        <SelectItem value="other">Other</SelectItem>
                                    </SelectContent>
                                </Select>
                            </FormControl>
                            <FormDescription>
                                Select Gender
                            </FormDescription>
                            <FormMessage className="min-h-4" />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="conditions"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Known Conditions</FormLabel>
                            <FormControl>
                                <Textarea placeholder="e.g., diabetes, hypertension" {...field} />
                            </FormControl>
                            <FormDescription>
                                Enter any known medical conditions
                            </FormDescription>
                            <FormMessage className="min-h-4" />
                        </FormItem>
                    )}
                />
                <Button type="submit" className="w-full">Start New Chat</Button>
            </form>
        </Form>
    )
}