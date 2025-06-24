
import { useState, useEffect } from 'react';
import AppSidebar from './AppSidebar';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { User, Mail, Hash } from 'lucide-react';

interface UserData {
  user_id: string;
  username: string;
  email: string;
}

const Home = () => {
  const [userData, setUserData] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const accessToken = localStorage.getItem('access_token');
        const tokenType = localStorage.getItem('token_type');
        
        if (!accessToken) {
          toast({
            title: "Error",
            description: "No access token found. Please sign in.",
            variant: "destructive"
          });
          return;
        }

        const response = await fetch('http://127.0.0.1:8000/user', {
          method: 'GET',
          headers: {
            'Authorization': `${tokenType} ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }

        const data = await response.json();
        console.log('User data received:', data);
        setUserData(data);
      } catch (error) {
        console.error('Error fetching user data:', error);
        toast({
          title: "Error",
          description: "Failed to load user data. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [toast]);

  if (loading) {
    return (
      <SidebarProvider>
        <div className="min-h-screen flex w-full bg-gray-50">
          <AppSidebar />
          <SidebarInset>
            <main className="flex-1 p-6">
              <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-center h-64">
                  <div className="text-lg text-gray-600">Loading...</div>
                </div>
              </div>
            </main>
          </SidebarInset>
        </div>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-gray-50">
        <AppSidebar />
        <SidebarInset>
          <main className="flex-1 p-6">
            <div className="max-w-7xl mx-auto">
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  Welcome back, {userData?.username || 'User'}!
                </h1>
                <p className="text-gray-600 text-lg">
                  Manage your data insights and analytics with OnyxPrism
                </p>
              </div>
              
              {userData && (
                <div className="mb-8">
                  <Card className="bg-white shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-xl font-semibold text-gray-800 flex items-center">
                        <User className="mr-2" size={24} />
                        Your Profile
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center space-x-3">
                          <User className="text-gray-500" size={20} />
                          <div>
                            <p className="text-sm text-gray-500">Username</p>
                            <p className="font-semibold text-gray-800">{userData.username}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <Mail className="text-gray-500" size={20} />
                          <div>
                            <p className="text-sm text-gray-500">Email</p>
                            <p className="font-semibold text-gray-800">{userData.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <Hash className="text-gray-500" size={20} />
                          <div>
                            <p className="text-sm text-gray-500">User ID</p>
                            <p className="font-semibold text-gray-800 font-mono text-sm">{userData.user_id}</p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg font-semibold text-blue-800">
                      Connect Database
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-blue-700 mb-4">
                      Set up your database connection to start analyzing your data.
                    </p>
                    <button 
                      onClick={() => window.location.href = '/connect-database'}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Get Started
                    </button>
                  </CardContent>
                </Card>
                
                <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg font-semibold text-green-800">
                      AI Assistant
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-green-700 mb-4">
                      Chat with our AI to get insights and answers about your data.
                    </p>
                    <button 
                      onClick={() => window.location.href = '/chatbot'}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                    >
                      Start Chat
                    </button>
                  </CardContent>
                </Card>
                
                <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg font-semibold text-purple-800">
                      View KPIs
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-purple-700 mb-4">
                      Monitor your key performance indicators and metrics.
                    </p>
                    <button 
                      onClick={() => window.location.href = '/kpi'}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      View KPIs
                    </button>
                  </CardContent>
                </Card>
              </div>
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default Home;
