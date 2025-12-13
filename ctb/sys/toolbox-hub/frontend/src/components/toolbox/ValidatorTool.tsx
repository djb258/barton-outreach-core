import { useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { getToolById } from "@/config/tools.config";

export const ValidatorTool = () => {
  const navigate = useNavigate();
  const tool = getToolById('validator')!;

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground">{tool.description}</p>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-tool-validator">24</div>
          <div className="text-xs text-muted-foreground">Active Rules</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-validator">1,247</div>
          <div className="text-xs text-muted-foreground">Records Validated</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-validator">43</div>
          <div className="text-xs text-muted-foreground">Failures</div>
        </div>
      </div>
      
      <Button 
        onClick={() => navigate(tool.route)}
        className="w-full bg-tool-validator text-tool-validator-foreground hover:bg-tool-validator/90"
      >
        Launch {tool.name}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
};
