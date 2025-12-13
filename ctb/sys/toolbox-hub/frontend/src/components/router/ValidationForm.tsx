import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/hooks/use-toast';
import { routerApi } from '@/lib/router/routerApi';
import { generateHeirId, generateProcessId } from '@/lib/router/routerUtils';
import { Send, Loader2 } from 'lucide-react';
import type { ValidationPayload } from '@/types/router';

const SOURCE_OPTIONS = [
  'enrichment',
  'outreach',
  'mapper',
  'validator',
  'parser',
  'doc-filler',
  'manual',
];

export const ValidationForm = () => {
  const [source, setSource] = useState('');
  const [jsonData, setJsonData] = useState('');
  const [errors, setErrors] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!source || !jsonData || !errors) {
      toast({
        title: 'Missing Fields',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      setLoading(true);
      
      // Parse JSON inputs
      const data = JSON.parse(jsonData);
      const validationErrors = JSON.parse(errors);
      
      // Generate tracking IDs
      const heir_id = generateHeirId(source);
      const process_id = generateProcessId(source);
      
      const payload: ValidationPayload = {
        source,
        data,
        validation_errors: validationErrors,
        heir_id,
        process_id,
      };
      
      const result = await routerApi.validateData(payload);
      
      toast({
        title: 'Data Routed Successfully',
        description: (
          <div className="space-y-1">
            <p>HEIR ID: {result.heir_id}</p>
            <p>Process ID: {result.process_id}</p>
            {result.sheetUrl && (
              <a 
                href={result.sheetUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-tool-router underline"
              >
                View Google Sheet →
              </a>
            )}
          </div>
        ),
      });
      
      // Clear form
      setSource('');
      setJsonData('');
      setErrors('');
      
    } catch (error) {
      toast({
        title: 'Routing Failed',
        description: error instanceof Error ? error.message : 'Failed to route data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-tool-router/30">
      <CardHeader>
        <CardTitle className="text-tool-router">Route Invalid Data</CardTitle>
        <CardDescription>
          Send validation failures to Messyflow for human review
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="source">Source Tool</Label>
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger id="source">
                <SelectValue placeholder="Select source tool" />
              </SelectTrigger>
              <SelectContent>
                {SOURCE_OPTIONS.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {opt.charAt(0).toUpperCase() + opt.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="data">Invalid Data (JSON)</Label>
            <Textarea
              id="data"
              placeholder='{"email": "bad@", "phone": "123"}'
              value={jsonData}
              onChange={(e) => setJsonData(e.target.value)}
              rows={6}
              className="font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="errors">Validation Errors (JSON Array)</Label>
            <Textarea
              id="errors"
              placeholder='[{"field": "email", "error": "Invalid format", "value": "bad@", "severity": "error"}]'
              value={errors}
              onChange={(e) => setErrors(e.target.value)}
              rows={6}
              className="font-mono text-sm"
            />
          </div>

          <Button 
            type="submit" 
            disabled={loading}
            className="w-full bg-tool-router hover:bg-tool-router/90"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Routing...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Route to Messyflow
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
