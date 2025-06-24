import { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import AppSidebar from './AppSidebar';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { useToast } from '@/hooks/use-toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Fullscreen } from 'lucide-react';

interface ChartData {
  charts: any[];
}

const Visualizations = () => {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [fullScreenChart, setFullScreenChart] = useState<any>(null);
  const [fullScreenOpen, setFullScreenOpen] = useState(false);
  const { toast } = useToast();

  const truncateTitle = (title: string, maxLength: number = 35) => {
    if (!title) return '';
    if (title.length <= maxLength) return title;
    return title.substring(0, maxLength) + '...';
  };

  const getChartTitle = (chartOption: any) => {
    if (chartOption.title && chartOption.title.text) {
      return chartOption.title.text;
    }
    return 'Chart';
  };

  const removeChartTitle = (chartOption: any) => {
    const optionCopy = { ...chartOption };
    delete optionCopy.title;
    return optionCopy;
  };

  const openFullScreen = (chartOption: any) => {
    setFullScreenChart(chartOption);
    setFullScreenOpen(true);
  };

  useEffect(() => {
    const fetchChartData = async () => {
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

        const response = await fetch('http://127.0.0.1:8000/visualization', {
          method: 'GET',
          headers: {
            'Authorization': `${tokenType} ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch chart data');
        }

        const data = await response.json();
        console.log('Chart data received:', data);
        setChartData(data);
      } catch (error) {
        console.error('Error fetching chart data:', error);
        toast({
          title: "Error",
          description: "Failed to load chart data. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [toast]);

  if (loading) {
    return (
      <SidebarProvider>
        <div className="min-h-screen flex w-full bg-gray-50">
          <AppSidebar />
          <SidebarInset>
            <main className="flex-1 p-6">
              <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">
                  Data Visualizations
                </h1>
                <div className="flex items-center justify-center h-64">
                  <div className="text-lg text-gray-600">Loading charts...</div>
                </div>
              </div>
            </main>
          </SidebarInset>
        </div>
      </SidebarProvider>
    );
  }

  if (!chartData || !chartData.charts || chartData.charts.length === 0) {
    return (
      <SidebarProvider>
        <div className="min-h-screen flex w-full bg-gray-50">
          <AppSidebar />
          <SidebarInset>
            <main className="flex-1 p-6">
              <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">
                  Data Visualizations
                </h1>
                <div className="flex items-center justify-center h-64">
                  <div className="text-lg text-gray-600">No chart data available</div>
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
              <h1 className="text-3xl font-bold text-gray-900 mb-6">
                Data Visualizations
              </h1>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {chartData.charts.map((chartOption, index) => (
                  <div key={index} className="bg-white rounded-lg shadow-lg p-4 relative group">
                    <div className="flex justify-between items-center mb-2">
                      <h3 className="text-lg font-semibold text-gray-800" title={getChartTitle(chartOption)}>
                        {truncateTitle(getChartTitle(chartOption))}
                      </h3>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openFullScreen(chartOption)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Fullscreen className="h-4 w-4" />
                      </Button>
                    </div>
                    <ReactECharts option={removeChartTitle(chartOption)} style={{ height: '400px', width: '100%' }} />
                  </div>
                ))}
              </div>
            </div>
          </main>
        </SidebarInset>
      </div>

      <Dialog open={fullScreenOpen} onOpenChange={setFullScreenOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] w-full h-full">
          <DialogHeader>
            <DialogTitle>
              {fullScreenChart && getChartTitle(fullScreenChart)}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 min-h-0">
            {fullScreenChart && (
              <ReactECharts 
                option={removeChartTitle(fullScreenChart)} 
                style={{ height: '100%', width: '100%', minHeight: '500px' }} 
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </SidebarProvider>
  );
};

export default Visualizations;
