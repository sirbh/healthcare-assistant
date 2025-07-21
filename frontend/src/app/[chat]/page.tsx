'use client';
import ChatInput from '@/components/custom/chat-input';
import ChatMessages, { Message } from '@/components/custom/messages';
import { useParams } from 'next/navigation'
import { useState } from 'react';
export default function Chat() {
    const params = useParams<{ chat: string }>();
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);

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
    console.log('Chat ID:', params.chat);
    return <>
        <ChatMessages messages={messages} />
        <ChatInput handleSend={handleSend} input={input} setInput={setInput} showDefaultOptions={messages.length === 0} />
    </>
}