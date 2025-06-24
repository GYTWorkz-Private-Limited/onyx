import { useState, useEffect } from 'react';
import AppSidebar from './AppSidebar';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface KPIResultItem {
  sum?: number;
  average_amount?: number;
  payment_method?: string;
  product_id?: number;
  revenue_by_product?: number;
  [key: string]: any; // Allow for other dynamic properties
}

interface KPIItem {
  name: string;
  result: KPIResultItem[];
}

interface KPIResponse {
  success: boolean;
  message: string;
  kpis: KPIItem[] | {};
}

const KPI = () => {
  const [kpiData, setKpiData] = useState<KPIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();
  
  // Pagination states for each KPI
  const [paginationStates, setPaginationStates] = useState<{[key: string]: {currentPage: number, pageSize: number}}>({});

  // Function to extract numeric value from result item
  const getNumericValue = (item: KPIResultItem): number => {
    if (item.sum !== undefined) return item.sum;
    if (item.average_amount !== undefined) return item.average_amount;
    if (item.revenue_by_product !== undefined) return item.revenue_by_product;
    
    // Look for any numeric property
    const numericKeys = Object.keys(item).filter(key => 
      typeof item[key] === 'number' && key !== 'product_id'
    );
    
    if (numericKeys.length > 0) {
      return item[numericKeys[0]];
    }
    
    return 0;
  };

  // Function to get the display label for result item
  const getDisplayLabel = (item: KPIResultItem, kpiName: string): string => {
    if (item.payment_method) return item.payment_method;
    if (item.product_id !== undefined) return `Product ${item.product_id}`;
    return kpiName.replace(/_/g, ' ');
  };

  // Function to get all property keys for table headers (excluding common ones)
  const getTableHeaders = (results: KPIResultItem[]): string[] => {
    const allKeys = new Set<string>();
    results.forEach(item => {
      Object.keys(item).forEach(key => allKeys.add(key));
    });
    return Array.from(allKeys).sort();
  };

  // Initialize pagination state for a KPI
  const initializePagination = (kpiName: string) => {
    if (!paginationStates[kpiName]) {
      setPaginationStates(prev => ({
        ...prev,
        [kpiName]: { currentPage: 1, pageSize: 10 }
      }));
    }
  };

  // Update page size for a specific KPI
  const updatePageSize = (kpiName: string, newSize: number) => {
    setPaginationStates(prev => ({
      ...prev,
      [kpiName]: { currentPage: 1, pageSize: newSize }
    }));
  };

  // Update current page for a specific KPI
  const updateCurrentPage = (kpiName: string, newPage: number) => {
    setPaginationStates(prev => ({
      ...prev,
      [kpiName]: { ...prev[kpiName], currentPage: newPage }
    }));
  };

  // Get paginated data for a KPI
  const getPaginatedData = (data: KPIResultItem[], kpiName: string) => {
    const state = paginationStates[kpiName] || { currentPage: 1, pageSize: 10 };
    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = startIndex + state.pageSize;
    return data.slice(startIndex, endIndex);
  };

  // Get total pages for a KPI
  const getTotalPages = (dataLength: number, kpiName: string): number => {
    const state = paginationStates[kpiName] || { currentPage: 1, pageSize: 10 };
    return Math.ceil(dataLength / state.pageSize);
  };

  useEffect(() => {
    const fetchKPIData = async () => {
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

        const response = await fetch('http://127.0.0.1:8000/kpi', {
          method: 'GET',
          headers: {
            'Authorization': `${tokenType} ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch KPI data');
        }

        const data = await response.json();
        console.log('KPI data received:', data);
        setKpiData(data);
      } catch (error) {
        console.error('Error fetching KPI data:', error);
        toast({
          title: "Error",
          description: "Failed to load KPI data. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchKPIData();
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
                  Key Performance Indicators
                </h1>
                <div className="flex items-center justify-center h-64">
                  <div className="text-lg text-gray-600">Loading KPIs...</div>
                </div>
              </div>
            </main>
          </SidebarInset>
        </div>
      </SidebarProvider>
    );
  }

  // Check if kpis is an empty object or if no KPIs exist
  const hasKPIs = kpiData && 
    Array.isArray(kpiData.kpis) && 
    kpiData.kpis.length > 0;

  if (!kpiData || !hasKPIs) {
    return (
      <SidebarProvider>
        <div className="min-h-screen flex w-full bg-gray-50">
          <AppSidebar />
          <SidebarInset>
            <main className="flex-1 p-6">
              <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">
                  Key Performance Indicators
                </h1>
                <div className="flex items-center justify-center h-64">
                  <div className="text-lg text-gray-600">
                    {kpiData?.message || "No KPI data available"}
                  </div>
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
                Key Performance Indicators
              </h1>
              
              <div className="space-y-8">
                {(kpiData.kpis as KPIItem[]).map((kpi, kpiIndex) => {
                  // Initialize pagination for this KPI
                  initializePagination(kpi.name);
                  
                  const currentState = paginationStates[kpi.name] || { currentPage: 1, pageSize: 10 };
                  const paginatedData = getPaginatedData(kpi.result, kpi.name);
                  const totalPages = getTotalPages(kpi.result.length, kpi.name);

                  return (
                    <div key={kpiIndex} className="space-y-4">
                      <h2 className="text-xl font-semibold text-gray-800 capitalize">
                        {kpi.name.replace(/_/g, ' ')}
                      </h2>
                      
                      {kpi.result.length === 1 ? (
                        // Single result - show as card
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          <Card className="bg-white shadow-lg">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-lg font-semibold text-gray-800">
                                {getDisplayLabel(kpi.result[0], kpi.name)}
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="text-2xl font-bold text-blue-600">
                                ${getNumericValue(kpi.result[0]).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      ) : (
                        // Multiple results - show as paginated table
                        <Card className="bg-white shadow-lg">
                          <CardHeader className="pb-3">
                            <div className="flex justify-between items-center">
                              <CardTitle className="text-lg font-semibold text-gray-800">
                                {kpi.name.replace(/_/g, ' ')} Details
                              </CardTitle>
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-600">Items per page:</span>
                                <Select
                                  value={currentState.pageSize.toString()}
                                  onValueChange={(value) => updatePageSize(kpi.name, parseInt(value))}
                                >
                                  <SelectTrigger className="w-20">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="5">5</SelectItem>
                                    <SelectItem value="10">10</SelectItem>
                                    <SelectItem value="20">20</SelectItem>
                                    <SelectItem value="50">50</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  {getTableHeaders(kpi.result).map((header) => (
                                    <TableHead key={header} className="font-semibold">
                                      {header.replace(/_/g, ' ').toUpperCase()}
                                    </TableHead>
                                  ))}
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {paginatedData.map((item, index) => (
                                  <TableRow key={index}>
                                    {getTableHeaders(kpi.result).map((header) => (
                                      <TableCell key={header}>
                                        {typeof item[header] === 'number' ? (
                                          header.toLowerCase().includes('revenue') || 
                                          header.toLowerCase().includes('amount') || 
                                          header.toLowerCase().includes('sum') ? (
                                            `$${item[header].toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                          ) : (
                                            item[header].toString()
                                          )
                                        ) : (
                                          item[header]?.toString() || '-'
                                        )}
                                      </TableCell>
                                    ))}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                            
                            {/* Pagination Controls */}
                            {totalPages > 1 && (
                              <div className="flex items-center justify-between mt-4">
                                <div className="text-sm text-gray-600">
                                  Showing {((currentState.currentPage - 1) * currentState.pageSize) + 1} to {Math.min(currentState.currentPage * currentState.pageSize, kpi.result.length)} of {kpi.result.length} results
                                </div>
                                <div className="flex items-center gap-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => updateCurrentPage(kpi.name, currentState.currentPage - 1)}
                                    disabled={currentState.currentPage === 1}
                                  >
                                    <ChevronLeft className="h-4 w-4" />
                                    Previous
                                  </Button>
                                  
                                  <div className="flex items-center gap-1">
                                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                      let pageNum;
                                      if (totalPages <= 5) {
                                        pageNum = i + 1;
                                      } else {
                                        const start = Math.max(1, currentState.currentPage - 2);
                                        const end = Math.min(totalPages, start + 4);
                                        pageNum = start + i;
                                        if (pageNum > end) return null;
                                      }
                                      
                                      return (
                                        <Button
                                          key={pageNum}
                                          variant={currentState.currentPage === pageNum ? "default" : "outline"}
                                          size="sm"
                                          onClick={() => updateCurrentPage(kpi.name, pageNum)}
                                          className="w-8 h-8 p-0"
                                        >
                                          {pageNum}
                                        </Button>
                                      );
                                    })}
                                  </div>
                                  
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => updateCurrentPage(kpi.name, currentState.currentPage + 1)}
                                    disabled={currentState.currentPage === totalPages}
                                  >
                                    Next
                                    <ChevronRight className="h-4 w-4" />
                                  </Button>
                                </div>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default KPI;
