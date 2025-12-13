import { Button } from '@/components/ui/button';
import { ArrowLeft, Route, Activity, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { ValidationForm, SheetsTable, RunsHistory } from '@/components/router';

const RouterPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-tool-router/5">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4 mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/')}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Hub
            </Button>
          </div>
          
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 rounded-lg bg-tool-router text-white">
              <Route className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-tool-router">Router Workbench</h1>
              <p className="text-muted-foreground">
                Validation safety net for your entire data pipeline
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <Card className="p-4 border-tool-router/30 bg-card">
              <div className="flex items-center gap-3">
                <Route className="h-5 w-5 text-tool-router" />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">System Status</div>
                  <div className="text-2xl font-bold text-tool-router">Active</div>
                </div>
              </div>
            </Card>
            
            <Card className="p-4 border-tool-router/30 bg-card">
              <div className="flex items-center gap-3">
                <Activity className="h-5 w-5 text-tool-router" />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Active Recipes</div>
                  <div className="text-2xl font-bold">12</div>
                </div>
              </div>
            </Card>
            
            <Card className="p-4 border-tool-router/30 bg-card">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-tool-router" />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Success Rate</div>
                  <div className="text-2xl font-bold">94%</div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            <ValidationForm />
            <RunsHistory />
          </div>

          {/* Right Column */}
          <div>
            <SheetsTable />
          </div>
        </div>

        {/* Info Section */}
        <Card className="mt-8 p-6 border-tool-router/30 bg-tool-router/5">
          <h2 className="text-lg font-semibold text-tool-router mb-3">How Messyflow Works</h2>
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>
              <strong>1. Invalid Data Detected:</strong> When any tool (enrichment, outreach, mapper, etc.) 
              detects validation failures, it sends the data here.
            </p>
            <p>
              <strong>2. Automatic Routing:</strong> Messyflow selects the appropriate recipe, creates a 
              Google Sheet with error highlights, and tracks everything with HEIR/Process IDs.
            </p>
            <p>
              <strong>3. Manual Review:</strong> Humans open the Google Sheet, fix invalid data, and mark 
              it as "Ready for re-validation".
            </p>
            <p>
              <strong>4. Sync & Return:</strong> Cleaned data syncs back, gets re-validated, and returns 
              to the main pipeline.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default RouterPage;
