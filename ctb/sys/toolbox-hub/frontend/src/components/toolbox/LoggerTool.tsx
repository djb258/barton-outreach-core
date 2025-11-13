import { useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { getToolById } from "@/config/tools.config";

export const LoggerTool = () => {
  const navigate = useNavigate();
  const tool = getToolById('logger')!;

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground">{tool.description}</p>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-tool-logger">1,847</div>
          <div className="text-xs text-muted-foreground">Audit Entries (24h)</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-logger">12</div>
          <div className="text-xs text-muted-foreground">Active Processes</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-logger">7</div>
          <div className="text-xs text-muted-foreground">Errors (24h)</div>
        </div>
      </div>
      
      <Button 
        onClick={() => navigate(tool.route)}
        className="w-full bg-tool-logger text-tool-logger-foreground hover:bg-tool-logger/90"
      >
        Launch {tool.name}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
};
