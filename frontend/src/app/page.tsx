'use client';

import Navigation from "@/components/custom/nav";
import NewChatForm from "@/components/custom/new-chat-form";



export default function Home() {

  console.log(`${process.env.NEXT_PUBLIC_BASE_URL}`);
  return (
    <>
      <Navigation />
      <div className="flex flex-col w-full h-full items-center justify-center bg-muted">
        <NewChatForm />
      </div>
    </>
  );
}
