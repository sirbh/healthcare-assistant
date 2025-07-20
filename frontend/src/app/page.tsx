'use client';

import { useSidebar } from "@/components/ui/sidebar"

import Navigation from '@/components/custom/nav';
import Chat from '@/components/custom/chat';
import SideMenu from "@/components/custom/side-menu";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MessageSquareXIcon } from "lucide-react";
import Messages from "@/components/custom/messages";
import ChatInput from "@/components/custom/chat-input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SelectItem } from "@radix-ui/react-select";
import { Textarea } from "@/components/ui/textarea";
import NewChatForm from "@/components/custom/new-chat-form";



export default function Home() {

  const { open } = useSidebar();
  console.log('open', open);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const age = formData.get('age');
    const gender = formData.get('gender');
    const conditions = formData.get('conditions');
    console.log('New chat started with:', { age, gender, conditions });
    // TODO: trigger chat start logic
    e.currentTarget.reset();
  };



  return (

    <>
      <SideMenu />
      <main className="flex flex-1 h-screen bg-muted font-sans">
        <div className="flex flex-col w-full h-full">
          {/* Fixed top navigation */}
          <Navigation />
          <div className="flex flex-col w-full h-full items-center justify-center bg-muted">



            {/* New Chat Form */}
            <NewChatForm />
           
          </div>

          {/* <Messages /> */}
          {/* <ChatInput setInput={()=>{}} handleSend={()=>{}} input="" /> */}
          {/* Chat area */}
        </div>
      </main>
    </>


  );
}
