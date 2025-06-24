import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Database, Send, CheckCircle, Circle, Loader2, Plus, Trash2 } from 'lucide-react';
import AppSidebar from './AppSidebar';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';

interface TableSchema {
  [tableName: string]: string[];
}

interface KPI {
  name: string;
  description: string;
  formula: string;
  formula_type: string;
}

const steps = [
  { id: 1, name: 'Connect Database', status: 'pending' },
  { id: 2, name: 'Extract Schemas', status: 'pending' },
  { id: 3, name: 'Semantic Extraction', status: 'pending' },
  { id: 4, name: 'Vector Data Insert', status: 'pending' },
  { id: 5, name: 'KPI', status: 'pending' }
];

const ConnectDatabase = () => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSemanticExtracting, setIsSemanticExtracting] = useState(false);
  const [isVectorInserting, setIsVectorInserting] = useState(false);
  const [isKpiProcessing, setIsKpiProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [isProcessComplete, setIsProcessComplete] = useState(false);
  const [tables, setTables] = useState<TableSchema>({});
  const [selectedTables, setSelectedTables] = useState<TableSchema>({});
  const [showSchemaSelection, setShowSchemaSelection] = useState(false);
  const [showKpiForm, setShowKpiForm] = useState(false);
  const [kpis, setKpis] = useState<KPI[]>([
    {
      name: '',
      description: '',
      formula: '',
      formula_type: 'general'
    }
  ]);
  const [formData, setFormData] = useState({
    db_type: '',
    database: '',
    username: '',
    password: '',
    host: '',
    port: 5432
  });

  const getStepStatus = (stepId: number) => {
    if (stepId < currentStep) return 'completed';
    if (stepId === currentStep && !isProcessComplete) return 'current';
    if (isProcessComplete) return 'completed';
    return 'pending';
  };

  const getProgressPercentage = () => {
    if (isProcessComplete) return 100;
    return ((currentStep - 1) / (steps.length - 1)) * 100;
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTableSelection = (tableName: string, checked: boolean) => {
    if (checked) {
      setSelectedTables(prev => ({
        ...prev,
        [tableName]: tables[tableName]
      }));
    } else {
      setSelectedTables(prev => {
        const newSelected = { ...prev };
        delete newSelected[tableName];
        return newSelected;
      });
    }
  };

  const handleColumnSelection = (tableName: string, columnName: string, checked: boolean) => {
    setSelectedTables(prev => {
      const currentColumns = prev[tableName] || [];
      if (checked) {
        return {
          ...prev,
          [tableName]: [...currentColumns, columnName]
        };
      } else {
        return {
          ...prev,
          [tableName]: currentColumns.filter(col => col !== columnName)
        };
      }
    });
  };

  const handleConnect = async () => {
    // Validate required fields
    if (!formData.db_type || !formData.database || !formData.username || !formData.password || !formData.host) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      // Get stored tokens
      const accessToken = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type');

      if (!accessToken) {
        toast({
          title: "Authentication Error",
          description: "No access token found. Please sign in again.",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/connect-db', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${tokenType} ${accessToken}`,
        },
        body: JSON.stringify({
          db_type: formData.db_type,
          database: formData.database,
          username: formData.username,
          password: formData.password,
          host: formData.host,
          port: Number(formData.port)
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Database connection response:', data);
        
        setTables(data);
        setShowSchemaSelection(true);
        setCurrentStep(2);
        
        toast({
          title: "Success",
          description: "Database connected successfully! Please select tables and columns.",
        });
      } else {
        const errorData = await response.json();
        toast({
          title: "Connection Failed",
          description: errorData.detail || "Failed to connect to database.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Database connection error:', error);
      toast({
        title: "Error",
        description: "An error occurred while connecting to the database.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExtractSchemas = async () => {
    if (Object.keys(selectedTables).length === 0) {
      toast({
        title: "Selection Required",
        description: "Please select at least one table with columns.",
        variant: "destructive",
      });
      return;
    }

    setIsExtracting(true);

    try {
      const accessToken = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type');

      if (!accessToken) {
        toast({
          title: "Authentication Error",
          description: "No access token found. Please sign in again.",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/extract-schemas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${tokenType} ${accessToken}`,
        },
        body: JSON.stringify(selectedTables),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Schema extraction response:', data);
        
        setCurrentStep(3);
        
        toast({
          title: "Success",
          description: "Schemas extracted successfully! Starting semantic extraction...",
        });

        // Automatically trigger semantic extraction
        handleSemanticExtraction();
      } else {
        const errorData = await response.json();
        toast({
          title: "Extraction Failed",
          description: errorData.detail || "Failed to extract schemas.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Schema extraction error:', error);
      toast({
        title: "Error",
        description: "An error occurred while extracting schemas.",
        variant: "destructive",
      });
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSemanticExtraction = async () => {
    setIsSemanticExtracting(true);

    try {
      const accessToken = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type');

      if (!accessToken) {
        toast({
          title: "Authentication Error",
          description: "No access token found. Please sign in again.",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/semantic-extraction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${tokenType} ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Semantic extraction response:', data);
        
        setCurrentStep(4);
        
        toast({
          title: "Success",
          description: "Semantic extraction completed successfully! Starting vector data insert...",
        });

        // Automatically trigger vector data insert
        handleVectorDataInsert();
      } else {
        const errorData = await response.json();
        toast({
          title: "Semantic Extraction Failed",
          description: errorData.detail || "Failed to perform semantic extraction.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Semantic extraction error:', error);
      toast({
        title: "Error",
        description: "An error occurred during semantic extraction.",
        variant: "destructive",
      });
    } finally {
      setIsSemanticExtracting(false);
    }
  };

  const handleVectorDataInsert = async () => {
    setIsVectorInserting(true);

    try {
      const accessToken = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type');

      if (!accessToken) {
        toast({
          title: "Authentication Error",
          description: "No access token found. Please sign in again.",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/vector-data-insert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${tokenType} ${accessToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Vector data insert response:', data);
        
        setCurrentStep(5);
        setShowKpiForm(true);
        
        toast({
          title: "Success",
          description: "Vector data insert completed successfully! Please configure KPIs.",
        });
      } else {
        const errorData = await response.json();
        toast({
          title: "Vector Data Insert Failed",
          description: errorData.detail || "Failed to perform vector data insert.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Vector data insert error:', error);
      toast({
        title: "Error",
        description: "An error occurred during vector data insert.",
        variant: "destructive",
      });
    } finally {
      setIsVectorInserting(false);
    }
  };

  const handleKpiChange = (index: number, field: keyof KPI, value: string) => {
    setKpis(prev => prev.map((kpi, i) => 
      i === index ? { ...kpi, [field]: value } : kpi
    ));
  };

  const addKpi = () => {
    setKpis(prev => [...prev, {
      name: '',
      description: '',
      formula: '',
      formula_type: 'general'
    }]);
  };

  const removeKpi = (index: number) => {
    if (kpis.length > 1) {
      setKpis(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleKpiSubmit = async () => {
    // Validate KPIs
    const validKpis = kpis.filter(kpi => 
      kpi.name.trim() && kpi.description.trim() && kpi.formula.trim()
    );

    if (validKpis.length === 0) {
      toast({
        title: "Validation Error",
        description: "Please fill in at least one complete KPI.",
        variant: "destructive",
      });
      return;
    }

    setIsKpiProcessing(true);

    try {
      const accessToken = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type');

      if (!accessToken) {
        toast({
          title: "Authentication Error",
          description: "No access token found. Please sign in again.",
          variant: "destructive",
        });
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/kpi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${tokenType} ${accessToken}`,
        },
        body: JSON.stringify({ kpis: validKpis }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('KPI response:', data);
        
        // Mark process as complete
        setCurrentStep(6); // Move beyond the last step
        setIsProcessComplete(true);
        setShowKpiForm(false);
        
        toast({
          title: "Success",
          description: "KPIs configured successfully! Database setup is complete.",
        });
      } else {
        const errorData = await response.json();
        toast({
          title: "KPI Configuration Failed",
          description: errorData.detail || "Failed to configure KPIs.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('KPI configuration error:', error);
      toast({
        title: "Error",
        description: "An error occurred while configuring KPIs.",
        variant: "destructive",
      });
    } finally {
      setIsKpiProcessing(false);
    }
  };

  const resetProcess = () => {
    setShowKpiForm(false);
    setShowSchemaSelection(false);
    setTables({});
    setSelectedTables({});
    setCurrentStep(1);
    setIsProcessComplete(false);
    setKpis([{
      name: '',
      description: '',
      formula: '',
      formula_type: 'general'
    }]);
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-gray-50">
        <AppSidebar />
        <SidebarInset>
          <main className="flex-1 p-6">
            <div className="max-w-4xl mx-auto">
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  Connect Database
                </h1>
                <p className="text-gray-600">
                  Configure your database connection and extract schemas
                </p>
              </div>

              {/* Progress Indicator */}
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Progress</CardTitle>
                  <CardDescription>
                    Follow these steps to complete the database connection process
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Progress value={getProgressPercentage()} className="w-full" />
                    <div className="flex justify-between">
                      {steps.map((step) => {
                        const status = getStepStatus(step.id);
                        return (
                          <div key={step.id} className="flex flex-col items-center space-y-2">
                            <div className="flex items-center justify-center">
                              {status === 'completed' ? (
                                <CheckCircle className="h-6 w-6 text-green-500" />
                              ) : status === 'current' ? (
                                isLoading || isExtracting || isSemanticExtracting || isVectorInserting || isKpiProcessing ? (
                                  <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
                                ) : (
                                  <Circle className="h-6 w-6 text-blue-500 fill-blue-500" />
                                )
                              ) : (
                                <Circle className="h-6 w-6 text-gray-300" />
                              )}
                            </div>
                            <span className={`text-xs text-center ${
                              status === 'completed' ? 'text-green-600' :
                              status === 'current' ? 'text-blue-600' :
                              'text-gray-400'
                            }`}>
                              {step.name}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Show completion message when process is complete */}
              {isProcessComplete && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-600">
                      <CheckCircle className="h-5 w-5" />
                      Database Setup Complete
                    </CardTitle>
                    <CardDescription>
                      Your database has been successfully connected and configured.
                    </CardDescription>
                  </CardHeader>
                </Card>
              )}

              {/* Show forms only when process is not complete */}
              {!isProcessComplete && (
                <>
                  {!showSchemaSelection && !showKpiForm ? (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Database className="h-5 w-5" />
                          Database Configuration
                        </CardTitle>
                        <CardDescription>
                          Enter your database connection details below
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="db_type">Database Type *</Label>
                          <Select value={formData.db_type} onValueChange={(value) => handleInputChange('db_type', value)}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select database type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="postgresql">PostgreSQL</SelectItem>
                              <SelectItem value="mysql">MySQL</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="database">Database Name *</Label>
                          <Input
                            id="database"
                            type="text"
                            placeholder="postgres"
                            value={formData.database}
                            onChange={(e) => handleInputChange('database', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="username">Username *</Label>
                          <Input
                            id="username"
                            type="text"
                            placeholder="postgres"
                            value={formData.username}
                            onChange={(e) => handleInputChange('username', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="password">Password *</Label>
                          <Input
                            id="password"
                            type="password"
                            placeholder="Enter password"
                            value={formData.password}
                            onChange={(e) => handleInputChange('password', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="host">Host *</Label>
                          <Input
                            id="host"
                            type="text"
                            placeholder="dev-lawndepot-postgresdb.cd4ecsq627o3.us-east-1.rds.amazonaws.com"
                            value={formData.host}
                            onChange={(e) => handleInputChange('host', e.target.value)}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="port">Port</Label>
                          <Input
                            id="port"
                            type="number"
                            placeholder="5432"
                            value={formData.port}
                            onChange={(e) => handleInputChange('port', parseInt(e.target.value) || 5432)}
                          />
                        </div>

                        <Button 
                          onClick={handleConnect} 
                          disabled={isLoading}
                          className="w-full"
                          size="lg"
                        >
                          {isLoading ? 'Connecting...' : 'Connect Database'}
                        </Button>
                      </CardContent>
                    </Card>
                  ) : showKpiForm ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Configure KPIs</CardTitle>
                        <CardDescription>
                          Define Key Performance Indicators for your data analysis
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        {kpis.map((kpi, index) => (
                          <div key={index} className="border rounded-lg p-4 space-y-4">
                            <div className="flex items-center justify-between">
                              <h3 className="text-lg font-semibold">KPI {index + 1}</h3>
                              {kpis.length > 1 && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => removeKpi(index)}
                                  disabled={isKpiProcessing}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label htmlFor={`kpi-name-${index}`}>Name *</Label>
                                <Input
                                  id={`kpi-name-${index}`}
                                  placeholder="e.g., Average_payment_amount"
                                  value={kpi.name}
                                  onChange={(e) => handleKpiChange(index, 'name', e.target.value)}
                                  disabled={isKpiProcessing}
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label htmlFor={`kpi-formula-type-${index}`}>Formula Type</Label>
                                <Select 
                                  value={kpi.formula_type} 
                                  onValueChange={(value) => handleKpiChange(index, 'formula_type', value)}
                                  disabled={isKpiProcessing}
                                >
                                  <SelectTrigger>
                                    <SelectValue placeholder="Select formula type" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="general">General</SelectItem>
                                    <SelectItem value="aggregation">Aggregation</SelectItem>
                                    <SelectItem value="calculation">Calculation</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                            
                            <div className="space-y-2">
                              <Label htmlFor={`kpi-description-${index}`}>Description *</Label>
                              <Textarea
                                id={`kpi-description-${index}`}
                                placeholder="e.g., the average amount in each payment method"
                                value={kpi.description}
                                onChange={(e) => handleKpiChange(index, 'description', e.target.value)}
                                disabled={isKpiProcessing}
                                rows={2}
                              />
                            </div>
                            
                            <div className="space-y-2">
                              <Label htmlFor={`kpi-formula-${index}`}>Formula *</Label>
                              <Textarea
                                id={`kpi-formula-${index}`}
                                placeholder="e.g., what is the average amount in each payment method"
                                value={kpi.formula}
                                onChange={(e) => handleKpiChange(index, 'formula', e.target.value)}
                                disabled={isKpiProcessing}
                                rows={3}
                              />
                            </div>
                          </div>
                        ))}
                        
                        <div className="flex gap-4">
                          <Button
                            variant="outline"
                            onClick={addKpi}
                            disabled={isKpiProcessing}
                            className="flex items-center gap-2"
                          >
                            <Plus className="h-4 w-4" />
                            Add Another KPI
                          </Button>
                        </div>
                        
                        <div className="flex gap-4 pt-4">
                          <Button 
                            onClick={handleKpiSubmit}
                            disabled={isKpiProcessing}
                            className="flex-1"
                            size="lg"
                          >
                            {isKpiProcessing ? 'Configuring KPIs...' : 'Configure KPIs'}
                          </Button>
                          
                          <Button 
                            variant="outline"
                            onClick={() => {
                              setShowKpiForm(false);
                              setShowSchemaSelection(false);
                              setTables({});
                              setSelectedTables({});
                              setCurrentStep(1);
                              setKpis([{
                                name: '',
                                description: '',
                                formula: '',
                                formula_type: 'general'
                              }]);
                            }}
                            disabled={isKpiProcessing}
                          >
                            Start Over
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-6">
                      <Card>
                        <CardHeader>
                          <CardTitle>Select Tables and Columns</CardTitle>
                          <CardDescription>
                            Choose the tables and columns you want to include in the schema extraction
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-6">
                            {Object.entries(tables).map(([tableName, columns]) => (
                              <div key={tableName} className="border rounded-lg p-4">
                                <div className="flex items-center space-x-2 mb-3">
                                  <Checkbox
                                    id={`table-${tableName}`}
                                    checked={tableName in selectedTables}
                                    onCheckedChange={(checked) => handleTableSelection(tableName, checked as boolean)}
                                    disabled={isExtracting || isSemanticExtracting || isVectorInserting}
                                  />
                                  <Label htmlFor={`table-${tableName}`} className="text-lg font-semibold">
                                    {tableName}
                                  </Label>
                                </div>
                                
                                {tableName in selectedTables && (
                                  <div className="ml-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                                    {columns.map((column) => (
                                      <div key={column} className="flex items-center space-x-2">
                                        <Checkbox
                                          id={`${tableName}-${column}`}
                                          checked={selectedTables[tableName]?.includes(column) || false}
                                          onCheckedChange={(checked) => handleColumnSelection(tableName, column, checked as boolean)}
                                          disabled={isExtracting || isSemanticExtracting || isVectorInserting}
                                        />
                                        <Label htmlFor={`${tableName}-${column}`} className="text-sm">
                                          {column}
                                        </Label>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>

                          <div className="mt-6 flex gap-4">
                            <Button 
                              onClick={handleExtractSchemas} 
                              disabled={isExtracting || isSemanticExtracting || isVectorInserting || Object.keys(selectedTables).length === 0}
                              className="flex-1"
                              size="lg"
                            >
                              <Send className="h-4 w-4 mr-2" />
                              {isExtracting ? 'Extracting Schemas...' : 
                               isSemanticExtracting ? 'Processing Semantic Extraction...' : 
                               isVectorInserting ? 'Processing Vector Data Insert...' :
                               'Extract Selected Schemas'}
                            </Button>
                            
                            <Button 
                              variant="outline"
                              onClick={() => {
                                setShowSchemaSelection(false);
                                setTables({});
                                setSelectedTables({});
                                setCurrentStep(1);
                              }}
                              disabled={isExtracting || isSemanticExtracting || isVectorInserting}
                            >
                              Back to Connection
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </>
              )}
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default ConnectDatabase;
