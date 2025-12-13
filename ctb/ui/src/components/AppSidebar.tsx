import { Activity, BarChart3, MessageSquare, Eye } from "lucide-react";
import { NavLink } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar";

const routes = [
  {
    title: "Control Tower",
    url: "/",
    icon: Activity,
    color: "text-vision",
  },
  {
    title: "Analytics",
    url: "/analytics",
    icon: BarChart3,
    color: "text-doctrine",
  },
  {
    title: "Messaging",
    url: "/messaging",
    icon: MessageSquare,
    color: "text-execution",
  },
  {
    title: "Executive Overview",
    url: "/overview",
    icon: Eye,
    color: "text-purple-500",
  },
];

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="border-b border-border p-4">
        <h1 className="text-sm font-bold text-vision">BARTON OUTREACH</h1>
        <p className="text-xs text-muted-foreground">Control System</p>
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {routes.map((route) => (
                <SidebarMenuItem key={route.url}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={route.url}
                      end
                      className={({ isActive }) =>
                        isActive
                          ? "bg-accent text-accent-foreground"
                          : "hover:bg-accent/50"
                      }
                    >
                      <route.icon className={`w-4 h-4 ${route.color}`} />
                      <span>{route.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
