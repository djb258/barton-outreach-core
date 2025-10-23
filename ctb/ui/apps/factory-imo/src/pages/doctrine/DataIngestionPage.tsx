import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { Upload, FileSpreadsheet, Database, CheckCircle2, AlertCircle, Send, Building2, Users } from 'lucide-react';
import { ProcessFlowDiagram } from '@/components/template/ProcessFlowDiagram';
import { outreachConfig } from '@/lib/template/application-config';

interface ParsedData {
  headers: string[];
  records: Record<string, any>[];
  fileName: string;
  fileSize: number;
}

export default function DataIngestionPage() {
  const [dataType, setDataType] = useState<'companies' | 'people'>('companies');
  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [apiEndpoint, setApiEndpoint] = useState('https://render-marketing-db.onrender.com');
  const { toast } = useToast();

  // Get the ingestion branch config
  const ingestionBranch = outreachConfig.branches.find(b => b.id === '00');

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file type
    const validTypes = ['.csv', '.xlsx', '.xls'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.'));
    
    if (!validTypes.includes(fileExtension)) {
      toast({
        title: 'Invalid File Type',
        description: 'Please upload a CSV or Excel file',
        variant: 'destructive'
      });
      return;
    }

    // Parse file (simplified for demo)
    try {
      const text = await file.text();
      const lines = text.split('\n').filter(line => line.trim());
      const headers = lines[0].split(',').map(h => h.trim());
      const records = lines.slice(1).map(line => {
        const values = line.split(',');
        const record: Record<string, any> = {};
        headers.forEach((header, index) => {
          record[header] = values[index]?.trim() || '';
        });
        return record;
      });

      setParsedData({
        headers,
        records,
        fileName: file.name,
        fileSize: file.size
      });

      toast({
        title: 'File Parsed Successfully',
        description: `Loaded ${records.length} records from ${file.name}`,
      });
    } catch (error) {
      toast({
        title: 'Parsing Error',
        description: 'Failed to parse the file. Please check the format.',
        variant: 'destructive'
      });
    }
  };

  const handleSubmit = async () => {
    if (!parsedData || parsedData.records.length === 0) {
      toast({
        title: 'No Data',
        description: 'Please upload a file first',
        variant: 'destructive'
      });
      return;
    }

    setIsUploading(true);
    setUploadResult(null);

    try {
      const targetTable = dataType === 'companies' 
        ? 'company.marketing_company' 
        : 'people.marketing_people';

      const response = await fetch(`${apiEndpoint}/insert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          records: parsedData.records,
          target_table: targetTable
        })
      });

      const result = await response.json();
      setUploadResult(result);

      if (response.ok) {
        toast({
          title: 'Upload Successful',
          description: `Inserted ${result.inserted || parsedData.records.length} records`,
        });
      } else {
        throw new Error(result.message || 'Upload failed');
      }
    } catch (error) {
      toast({
        title: 'Upload Failed',
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: 'destructive'
      });
      setUploadResult({ error: error instanceof Error ? error.message : 'Unknown error' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Company & People Data Ingestion</h1>
        <p className="text-muted-foreground">
          Upload CSV or Excel files to ingest company and people data into the marketing database
        </p>
      </div>

      {ingestionBranch && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Process Flow</CardTitle>
            <CardDescription>Data ingestion workflow from file upload to database</CardDescription>
          </CardHeader>
          <CardContent>
            <ProcessFlowDiagram branch={ingestionBranch} />
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>1. Select Data Type</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={dataType} onValueChange={(v) => setDataType(v as 'companies' | 'people')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="companies" className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Companies
                </TabsTrigger>
                <TabsTrigger value="people" className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  People
                </TabsTrigger>
              </TabsList>
              <TabsContent value="companies" className="mt-4">
                <Alert>
                  <Building2 className="h-4 w-4" />
                  <AlertDescription>
                    Upload company data with fields like: company_name, domain, industry, employee_count, location
                  </AlertDescription>
                </Alert>
              </TabsContent>
              <TabsContent value="people" className="mt-4">
                <Alert>
                  <Users className="h-4 w-4" />
                  <AlertDescription>
                    Upload people data with fields like: first_name, last_name, email, company, title
                  </AlertDescription>
                </Alert>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>2. Upload File</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="border-2 border-dashed rounded-lg p-8 text-center">
                <FileSpreadsheet className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <Label htmlFor="file-upload" className="cursor-pointer">
                  <Input
                    id="file-upload"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Button variant="outline" asChild>
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      Choose File
                    </span>
                  </Button>
                </Label>
                <p className="text-sm text-muted-foreground mt-2">
                  CSV or Excel files only
                </p>
              </div>
              
              {parsedData && (
                <Alert>
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertDescription>
                    <div className="flex items-center justify-between">
                      <span>{parsedData.fileName}</span>
                      <Badge>{parsedData.records.length} records</Badge>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {parsedData && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>3. Preview Data</CardTitle>
            <CardDescription>First 5 records from your file</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    {parsedData.headers.map((header, idx) => (
                      <th key={idx} className="text-left p-2 font-medium">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {parsedData.records.slice(0, 5).map((record, idx) => (
                    <tr key={idx} className="border-b">
                      {parsedData.headers.map((header, hidx) => (
                        <td key={hidx} className="p-2 text-sm">
                          {record[header] || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {parsedData.records.length > 5 && (
                <p className="text-sm text-muted-foreground mt-2">
                  ... and {parsedData.records.length - 5} more records
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>4. Configure & Submit</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="api-endpoint">API Endpoint</Label>
              <Input
                id="api-endpoint"
                type="url"
                value={apiEndpoint}
                onChange={(e) => setApiEndpoint(e.target.value)}
                placeholder="https://your-api.onrender.com"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{dataType}</Badge>
                <Badge variant={parsedData ? 'default' : 'secondary'}>
                  {parsedData ? `${parsedData.records.length} records` : 'No data'}
                </Badge>
              </div>
              
              <Button 
                onClick={handleSubmit}
                disabled={!parsedData || isUploading}
              >
                {isUploading ? (
                  <>
                    <Database className="h-4 w-4 mr-2 animate-pulse" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Upload to Database
                  </>
                )}
              </Button>
            </div>

            {uploadResult && (
              <Alert variant={uploadResult.error ? 'destructive' : 'default'}>
                {uploadResult.error ? (
                  <AlertCircle className="h-4 w-4" />
                ) : (
                  <CheckCircle2 className="h-4 w-4" />
                )}
                <AlertDescription>
                  {uploadResult.error 
                    ? `Error: ${uploadResult.error}`
                    : `Successfully inserted ${uploadResult.inserted || parsedData?.records.length} records`
                  }
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}