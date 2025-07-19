import { ChatProvider } from "@/context/ChatContext";
import { FullChat } from "../fullchat/fullchat";
import { SidebarProvider } from "@/context/SidebarContext";

export function MainChatPage() {
  return (
    <SidebarProvider>
        <ChatProvider>
          <FullChat />
        </ChatProvider>
    </SidebarProvider>
  );
}
