import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { getToolById } from "@/config/tools.config";

export const RouterTool = () => {
  const navigate = useNavigate();
  const tool = getToolById('router')!;

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground">{tool.description}</p>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-tool-router">12</div>
          <div className="text-xs text-muted-foreground">Active Routes</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-router">347</div>
          <div className="text-xs text-muted-foreground">Today's Activity</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-router">98.2%</div>
          <div className="text-xs text-muted-foreground">Success Rate</div>
        </div>
      </div>
      
      <Button 
        onClick={() => navigate(tool.route)}
        className="w-full bg-tool-router text-tool-router-foreground hover:bg-tool-router/90"
      >
        Launch {tool.name}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
};
