import { useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { getToolById } from "@/config/tools.config";

export const DocFillerTool = () => {
  const navigate = useNavigate();
  const tool = getToolById('docfiller')!;

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground">{tool.description}</p>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-tool-docfiller">15</div>
          <div className="text-xs text-muted-foreground">Templates</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-docfiller">589</div>
          <div className="text-xs text-muted-foreground">Docs Generated</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-docfiller">1.2s</div>
          <div className="text-xs text-muted-foreground">Avg Time</div>
        </div>
      </div>
      
      <Button 
        onClick={() => navigate(tool.route)}
        className="w-full bg-tool-docfiller text-tool-docfiller-foreground hover:bg-tool-docfiller/90"
      >
        Launch {tool.name}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
};
