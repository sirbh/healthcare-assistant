import { PlusIcon } from "lucide-react";
import { Button } from "../ui/button";
import { useSidebar } from "../ui/sidebar";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";
import { ModeSelector } from "./mode-selector";
import { SideMenuToggle } from "./side-menu-toggle";
import { ThemeSelector } from "./theme-selector";

export default function Navigation() {

    const { open } = useSidebar();
    

    return (
        <div className="sticky top-0 z-50 w-full border-b bg-background">
            {/* <SidebarTrigger /> */}
            <div className="px-8 py-3 relative flex align-centre justify-between">
                <div className="flex justify-start items-center gap-2">

                    <SideMenuToggle />
                    {!open && (
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="outline"
                                    className="px-2 md:h-fit ml-auto md:ml-0"
                                >
                                    <PlusIcon />
                                    <span className="md:sr-only">New Chat</span>
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>New Chat</TooltipContent>
                        </Tooltip>
                    )}
                    <ModeSelector className="w-full md:w-auto" />
                </div>

                <ThemeSelector className="hidden md:flex" />

            </div>
        </div>
    );
}