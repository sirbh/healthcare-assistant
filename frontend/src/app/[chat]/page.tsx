'use client';
import ChatInput from '@/components/custom/chat-input';
import ChatMessages from '@/components/custom/messages';
import Navigation from '@/components/custom/nav';
import { MessageStateContext } from '@/context/message-state';
import { useParams } from 'next/navigation';
import { useContext, useEffect } from 'react';

export default function Chat() {
   
    const params = useParams<{ chat: string }>();
    const chatId = params.chat;
    const { setChatId } = useContext(MessageStateContext);

    useEffect(() => {
        setChatId(chatId);
    }, []);

    return <>
        <Navigation />
        <ChatMessages />
        <ChatInput />
    </>
}