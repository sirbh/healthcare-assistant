'use client';
import { MessageStateContext } from "@/context/message-state";
import { Card, CardContent } from "../ui/card";
import MarkdownRenderer from "./markdown-render";
import { useContext, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";





export type Message = {
    role: 'user' | 'ai' | 'tool' | 'loading';
    content: string;
};

export default function Messages() {

    const bottomRef = useRef<HTMLDivElement | null>(null);
    const lastNonHumanMessageRef = useRef<HTMLDivElement | null>(null);
    const router = useRouter();


    const { messageLoading, messagesLoading, messages,isMessageLoadingError,isMessagesLoadingError } = useContext(MessageStateContext);
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);


    if (messagesLoading) {
        return (
            <div className="flex items-center justify-center h-full">
            </div>
        );
    }

    if (isMessagesLoadingError) {
        
        toast.error('Request failed, please try again later');
        router.push('/');

        return (
            <div className="flex items-center justify-center h-full">
                
            </div>
        );
    }

    if (isMessageLoadingError) {
        toast.error('Request Cannot be processed');
    }


    return (
        <>
            <div className="w-full h-full overflow-y-auto">
                <div className="flex-1 w-full max-w-2xl mx-auto flex flex-col gap-4 px-2 pt-8 pb-0 ">

                    {messages.length === 0 && (
                        <div className="text-muted-foreground">
                            <h1 className="text-3xl">Hi! I am your medical assistant </h1>
                            <p className="text-lg">You can share your symptoms with me!</p>
                        </div>
                    )}
                    {messages.map((msg, idx) => (
                        <Card
                            ref={msg.role !== 'user' ? lastNonHumanMessageRef : null}
                            key={idx}
                            className={`${msg.role==='ai'?'':'max-w-[80%]'} p-1 ${msg.role === 'user'
                                ? 'self-end'
                                : 'self-start bg-transparent shadow-none border-none'
                                } `}
                        >
                            <CardContent className={`p-4 text-lg whitespace-pre-wrap ${msg.role === 'tool' ? 'border rounded-full p-3 animate-pulse' : ''}`}>
                                <MarkdownRenderer content={msg.content} />
                            </CardContent>
                        </Card>
                    ))}
 
                    <div ref={bottomRef} className="p-6 h-4 w-full" >
                       {messageLoading && (
           
                           <div className="self-start h-4 w-4 bg-gray-200 rounded-full animate-spin self-center">
                              
                           </div>
  
                       )}
                    </div>
                </div>
            </div>
        </>

    )
}