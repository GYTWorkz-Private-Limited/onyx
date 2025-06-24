
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Database, BarChart3, Home as HomeIcon, MessageCircle, TrendingUp } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
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
  SidebarFooter,
} from '@/components/ui/sidebar';

const AppSidebar = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleLogout = () => {
    // Clear stored tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    
    toast({
      title: "Logged out",
      description: "You have been successfully logged out.",
    });
    
    // Navigate back to sign in page
    navigate('/signin');
  };

  const menuItems = [
    {
      title: "Home",
      icon: HomeIcon,
      action: () => navigate('/home'),
    },
    {
      title: "Connect Database",
      icon: Database,
      action: () => navigate('/connect-database'),
    },
    {
      title: "AI Assistant",
      icon: MessageCircle,
      action: () => navigate('/chatbot'),
    },
    {
      title: "KPIs",
      icon: TrendingUp,
      action: () => navigate('/kpi'),
    },
    {
      title: "Visualizations",
      icon: BarChart3,
      action: () => navigate('/visualizations'),
    },
  ];

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <div className="flex items-center">
          <div className="bg-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
            <div className="w-4 h-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full"></div>
          </div>
          <div>
            <span className="text-lg font-bold text-sidebar-foreground">onyx</span>
            <div className="text-orange-400 text-sm font-medium">prism</div>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton onClick={item.action}>
                    <item.icon />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={handleLogout} className="text-red-600 hover:text-red-700 hover:bg-red-50">
              <LogOut />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
};

export default AppSidebar;
