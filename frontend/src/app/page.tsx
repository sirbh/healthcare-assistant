'use client';

import { useSidebar } from "@/components/ui/sidebar"

import Navigation from '@/components/custom/nav';
import Chat from '@/components/custom/chat';
import SideMenu from "@/components/custom/side-menu";


export default function Home() {

  const { open } = useSidebar();

  console.log('open', open);



  return (

    <section className="w-screen h-screen">
      <SideMenu />
      <main className="flex flex-1 min-h-screen bg-muted font-sans">
        <div className="flex flex-col flex-1 w-full">
          {/* Fixed top navigation */}
          <Navigation />

          {/* Chat area */}
          <Chat />

        </div>
      </main>
    </section>


  );
}
