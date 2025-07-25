'use client';

import Navigation from "@/components/custom/nav";
import NewChatForm from "@/components/custom/new-chat-form";



export default function Home() {


  return (
    <>
      <Navigation />
      <div className="flex flex-col w-full h-full items-center justify-center bg-muted">
        <NewChatForm />
      </div>
    </>
  );
}
