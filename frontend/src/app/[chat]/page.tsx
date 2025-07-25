'use client';
import ChatInput from '@/components/custom/chat-input';
import ChatMessages, { Message } from '@/components/custom/messages';
import { VisibilityType } from '@/components/custom/mode-selector';
import Navigation from '@/components/custom/nav';
import axios from 'axios';
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
export default function Chat() {


    const params = useParams<{ chat: string }>();
    const [input, setInput] = useState('');
    const [chatVisibility, setChatVisibility] = useState<VisibilityType>('private');
    const [messages, setMessages] = useState<Message[]>([]);
    const [loadingMessages, setLoadingMessages] = useState(true);
    const router = useRouter();




    async function getChatHistory() {
        setLoadingMessages(true);
        try {
            const res = await axios.get(`http://localhost:8000/chat/${params.chat}`, {
                withCredentials: true,
            });
            // setMessages(res.data.messages);
            console.log('Chat history:', res.data);
            setMessages(res.data.messages)
            setChatVisibility(res.data.visibility);
            setLoadingMessages(false);
            toast.success("Chat loaded successfully");
        } catch (error) {
            console.error("Error fetching chat history:", error);
            toast.error("Failed to load chat");
            router.push('/');
        }
    }

    useEffect(() => {
        console.log('Fetching chat history for:', params.chat);
        getChatHistory();
    }, []);

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMessage = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

        try {
            const resp = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                body: JSON.stringify({
                    chat_id: params.chat,
                    message: userMessage,
                }),
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!resp.body) throw new Error("No response body");

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let aiMessage = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                aiMessage += chunk;

                // Optionally update UI as it streams
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last?.role === 'ai') {
                        return [...prev.slice(0, -1), { role: 'ai', content: aiMessage }];
                    } else {
                        return [...prev, { role: 'ai', content: aiMessage }];
                    }
                });
            }

            // Replace temporary ai-stream message with final AI message
            setMessages(prev => [...prev.slice(0, -1), { role: 'ai', content: aiMessage }]);

        } catch (err) {
            console.error('Streaming error:', err);
        }
    };
    return <>
        <Navigation visibility={chatVisibility} />
        <ChatMessages messages={messages} messagesLoading={loadingMessages} messageLoading={false} />
        <ChatInput handleSend={handleSend} input={input} setInput={setInput} showDefaultOptions={messages.length === 0} loading={loadingMessages} />
    </>
}