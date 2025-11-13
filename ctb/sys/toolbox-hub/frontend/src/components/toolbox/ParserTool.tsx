import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import { getToolById } from '@/config/tools.config';

export const ParserTool = () => {
  const navigate = useNavigate();
  const tool = getToolById('parser')!;

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground">{tool.description}</p>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-tool-parser">342</div>
          <div className="text-xs text-muted-foreground">Docs Parsed</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-parser">96.5%</div>
          <div className="text-xs text-muted-foreground">Success Rate</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-parser">12</div>
          <div className="text-xs text-muted-foreground">Parse Errors</div>
        </div>
      </div>
      
      <Button 
        onClick={() => navigate(tool.route)}
        className="w-full bg-tool-parser text-tool-parser-foreground hover:bg-tool-parser/90"
      >
        Launch {tool.name}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
};
