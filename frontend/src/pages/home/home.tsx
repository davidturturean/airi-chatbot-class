import { SidebarProvider } from "@/context/SidebarContext";
import { Welcome } from "../../components/welcome";
import { ChatProvider } from "@/context/ChatContext";


export function HomePage() {
  return (
    <SidebarProvider>
    <ChatProvider>
      <Welcome />
    </ChatProvider>
    </SidebarProvider>

  );
}
