'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { Message } from '@/components/custom/messages';
import { VisibilityType } from '@/components/custom/mode-selector';
import { ChatStateContext } from './chat-state';

export const MessageStateContext = createContext<{
    messages: Message[];
    messageLoading: boolean;
    messagesLoading: boolean;
    updateMessage: (msg: string) => void;
    visibility: VisibilityType;
    isMessagesLoadingError: boolean;
    isMessageLoadingError: boolean;
    setChatId: (id: string | null) => void;
}>({
    messages: [],
    messageLoading: false,
    messagesLoading: false,
    updateMessage: (msg: string) => {
        console.log(`Update user message called with ${msg}`);
    },

    visibility: 'private',
    isMessagesLoadingError: false,
    isMessageLoadingError: false,
    setChatId: (id: string | null) => {
        console.log(`Set chat ID called with ${id}`);
    }
});


export default function MessageStateContextProvider({ children }: { children: React.ReactNode }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [messageLoading, setMessageLoading] = useState(false);
    const [messagesLoading, setMessagesLoading] = useState(true);
    const [isMessageLoadingError, setIsMessageLoadingError] = useState(false);
    const [isMessagesLoadingError, setIsMessagesLoadingError] = useState(false);
    const [visibility, setVisibility] = useState<VisibilityType>('private');
    const { updateChatName } = useContext(ChatStateContext);
    const [chatId, setChatId] = useState<string | null>(null);


    async function getChatHistory() {
        if (!chatId) return;
        setMessagesLoading(true);
        try {
            const res = await axios.get(`/api/chat/${chatId}`, {
                withCredentials: true,
            });
            setIsMessagesLoadingError(false);
            setMessages(res.data.messages)
            setVisibility(res.data.visibility);
            setMessagesLoading(false);
        } catch (error) {
            console.error("Error fetching chat history:", error);
            setIsMessagesLoadingError(true);
            setMessagesLoading(false);
        }
    }

    useEffect(() => {
        getChatHistory();
    }, [chatId]);

    async function updateMessage(msg: string) {

        if (!msg.trim()) return;
        setMessages(prev => [...prev, { role: 'user', content: msg }, { role: 'loading', content: 'loading...' }]);
        setMessageLoading(true);

        try {
            const response = await axios.get('/api/user-id', {
                withCredentials: true,  // Important: send cookies
            });
            const user_id =response.data.user_id;

            const resp = await fetch(process.env.NEXT_PUBLIC_BASE_URL + '/api/chat', {
                method: 'POST',
                body: JSON.stringify({
                    chat_id: chatId,
                    user_id: user_id,
                    message: msg,
                }),
                headers: {
                    'Content-Type': 'application/json',
                },
            });



            if (!resp.body) throw new Error("No response body");

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            let aiBuffer = '';
            let summaryBuffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // hold incomplete line

                for (const line of lines) {
                    if (!line.trim()) continue;

                    try {
                        const data = JSON.parse(line);

                        console.log('Received data:', data);
                        const { type, content } = data;



                        if (type === 'ai') {
                            if (content.trim() === '') {
                                continue;
                            } // skip empty AI messages
                            aiBuffer += content;
                            setMessageLoading(false);
                            setMessages(prev => {
                                const last = prev[prev.length - 1];
                                // if (last?.role === 'ai') {
                                //     return [...prev.slice(0, -1), { role: 'ai', content: aiBuffer }];
                                // } else {
                                //     return [...prev, { role: 'ai', content: aiBuffer }];
                                // }

                                if (last?.role === 'user') {
                                    return [...prev, { role: 'ai', content: aiBuffer }];
                                } else {
                                    return [...prev.slice(0, -1), { role: 'ai', content: aiBuffer }];
                                }
                            });
                        } else if (type === 'summary') {
                            summaryBuffer += content;
                            updateChatName?.(chatId!, summaryBuffer);
                        } else if (type === 'tool') {

                            setMessages(prev => {
                                const last = prev[prev.length - 1];
                                if (last?.role === 'tool') {
                                    return [...prev.slice(0, -1), { role: 'tool', content }];
                                } else {
                                    return [...prev, { role: 'tool', content }];
                                }
                            });
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e);
                        setMessageLoading(false);
                    }
                }
            }

        } catch (err) {
            setMessageLoading(false);
            setIsMessageLoadingError(true);
            console.error('Streaming error:', err);
        }
    };




    return (
        <MessageStateContext value={{ setChatId, isMessageLoadingError, isMessagesLoadingError, messages, updateMessage, visibility, messageLoading, messagesLoading }}>
            {children}
        </MessageStateContext>
    );
}
