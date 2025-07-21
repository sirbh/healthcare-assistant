'use client';

import { PlusIcon } from "lucide-react";
import { Button } from "../ui/button";
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarHeader
} from "../ui/sidebar";
import {
    Tooltip,
    TooltipTrigger,
    TooltipContent
} from "../ui/tooltip";
import { useEffect, useState } from "react";
import axios from "axios";
import { usePathname, useRouter } from "next/navigation"; // App Router

export default function SideMenu() {
    const [loading, setLoading] = useState(false);
    const [chats, setChats] = useState<{ chat_id: string, info: { name: string } }[]>([]);
    const pathname = usePathname();
    const router = useRouter();

    const fetchChatHistory = async () => {
        try {
            setLoading(true);
            const res = await axios.get('http://localhost:8000/user-chats', {
                withCredentials: true,
            });
            setChats(res.data.chats);
        } catch (error) {
            console.error("Error fetching chat history:", error);
        } finally {
            setLoading(false);
        }
    };

    // Re-fetch on route change
    useEffect(() => {
        fetchChatHistory();
    }, [pathname]); // Runs when route changes

    return (
        <Sidebar>
            <SidebarHeader className="mb-4">
                <div className="flex flex-row items-center justify-between">
                    <h1 className="text-lg font-semibold">Chat History</h1>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="outline" className="px-2 md:h-fit ml-auto md:ml-0" onClick={() => router.push('/')}>
                                <PlusIcon />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>New Chat</TooltipContent>
                    </Tooltip>
                </div>
            </SidebarHeader>
            <SidebarContent>
                <SidebarGroup className="px-4 overflow-hidden">
                    {loading ? (
                        <div className="animate-pulse space-y-2">
                            <div className="h-4 bg-gray-300 rounded w-3/4" />
                            <div className="h-4 bg-gray-300 rounded w-2/3" />
                        </div>
                    ) : (
                        chats.map((chat) => (
                            <Button
                                key={chat.chat_id}
                                variant="ghost"
                                className="w-full justify-start capitalize"
                            >
                                {`${chat.info.name}`}
                            </Button>
                        ))
                    )}
                </SidebarGroup>
            </SidebarContent>
            <SidebarFooter />
        </Sidebar>
    );
}
