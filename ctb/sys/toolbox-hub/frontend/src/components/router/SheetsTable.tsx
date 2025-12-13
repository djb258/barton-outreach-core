import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, RefreshCw } from 'lucide-react';
import { routerApi } from '@/lib/router/routerApi';
import { formatRelativeTime, getStatusColor } from '@/lib/router/routerUtils';
import { toast } from '@/hooks/use-toast';
import type { SheetRegistry } from '@/types/router';

export const SheetsTable = () => {
  const [sheets, setSheets] = useState<SheetRegistry[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSheets = async () => {
    try {
      setLoading(true);
      const data = await routerApi.getSheets();
      setSheets(data);
    } catch (error) {
      toast({
        title: 'Failed to Load Sheets',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSheets();
  }, []);

  return (
    <Card className="border-tool-router/30">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-tool-router">Connected Sheets</CardTitle>
            <CardDescription>Google Sheets created for validation review</CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={loadSheets}
            disabled={loading}
            className="border-tool-router/30"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {sheets.length === 0 && !loading ? (
          <div className="text-center py-8 text-muted-foreground">
            No sheets created yet. Route invalid data to create your first sheet.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sheet Name</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Records</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>HEIR ID</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sheets.map((sheet) => (
                <TableRow key={sheet.id}>
                  <TableCell className="font-medium">{sheet.sheet_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {sheet.source}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(sheet.status)}>
                      {sheet.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{sheet.record_count}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatRelativeTime(sheet.created_at)}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {sheet.heir_id}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => window.open(sheet.sheet_url, '_blank')}
                      className="text-tool-router hover:text-tool-router/80"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
};
