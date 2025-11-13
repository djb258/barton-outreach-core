import { Button } from '@/components/ui/button';
import { ArrowLeft, BookOpen, FileText, GitBranch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { getToolById } from '@/config/tools.config';

const DocumentationPage = () => {
  const navigate = useNavigate();
  const tool = getToolById('documentation')!;
  const Icon = tool.icon;

  return (
    <div className="min-h-screen bg-background" data-page-id="documentation-page">
      <div className={`border-b bg-${tool.color}/5`} data-block-id="documentation-page-header">
        <div className="container mx-auto px-4 py-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/')}
            className="gap-2 mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Hub
          </Button>
          
          <div className="flex items-center gap-3 mb-2">
            <div className={`p-3 rounded-lg bg-${tool.color} text-${tool.color}-foreground`}>
              <Icon className="h-6 w-6" />
            </div>
            <div>
              <h1 className={`text-3xl font-bold text-${tool.color}`}>{tool.name}</h1>
              <p className="text-muted-foreground">{tool.description}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6" data-block-id="documentation-page-stats">
            <Card className={`p-4 border-${tool.color}/30 bg-card`}>
              <div className="flex items-center gap-3">
                <BookOpen className={`h-5 w-5 text-${tool.color}`} />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Documentation Pages</div>
                  <div className="text-2xl font-bold">42</div>
                </div>
              </div>
            </Card>
            
            <Card className={`p-4 border-${tool.color}/30 bg-card`}>
              <div className="flex items-center gap-3">
                <FileText className={`h-5 w-5 text-${tool.color}`} />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Process Diagrams</div>
                  <div className="text-2xl font-bold">7</div>
                </div>
              </div>
            </Card>
            
            <Card className={`p-4 border-${tool.color}/30 bg-card`}>
              <div className="flex items-center gap-3">
                <GitBranch className={`h-5 w-5 text-${tool.color}`} />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">API Endpoints</div>
                  <div className="text-2xl font-bold">28</div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8" data-block-id="documentation-page-content">
        <p className="text-muted-foreground">
          Documentation tool content coming soon. Backend: {tool.branch}
        </p>
      </div>
    </div>
  );
};

export default DocumentationPage;
