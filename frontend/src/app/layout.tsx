import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/custom/theme-provider";
import { SidebarProvider } from "@/components/ui/sidebar";
import SideMenu from "@/components/custom/side-menu";
import { Toaster } from "@/components/ui/sonner"
import ChatStateContextProvider from "@/context/chat-state";
import MessageStateContextProvider from "@/context/message-state";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HEALTH-CARE-AI",
  description: "A healthcare AI assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <ChatStateContextProvider>
            <MessageStateContextProvider>
              <SidebarProvider defaultOpen={false}>
                <SideMenu />
                <main className="flex flex-1 h-screen bg-muted font-sans">
                  <div className="flex flex-col w-full h-full">
                    {children}
                  </div>
                </main>
                <Toaster position="top-center" />
              </SidebarProvider>
            </MessageStateContextProvider>
          </ChatStateContextProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
