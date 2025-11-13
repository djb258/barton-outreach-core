import { useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { getToolById } from "@/config/tools.config";

export const DocumentationTool = () => {
  const navigate = useNavigate();
  const tool = getToolById('documentation')!;

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground">{tool.description}</p>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-tool-docs">42</div>
          <div className="text-xs text-muted-foreground">Doc Pages</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-docs">7</div>
          <div className="text-xs text-muted-foreground">Process Diagrams</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-docs">28</div>
          <div className="text-xs text-muted-foreground">API Endpoints</div>
        </div>
      </div>
      
      <Button 
        onClick={() => navigate(tool.route)}
        className="w-full bg-tool-docs text-tool-docs-foreground hover:bg-tool-docs/90"
      >
        Launch {tool.name}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
};
