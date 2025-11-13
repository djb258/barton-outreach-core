import { useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { getToolById } from "@/config/tools.config";

export const MapperTool = () => {
  const navigate = useNavigate();
  const tool = getToolById('mapper')!;

  return (
    <div className="space-y-4">
      <p className="text-muted-foreground">{tool.description}</p>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-tool-mapper">8</div>
          <div className="text-xs text-muted-foreground">Mapping Recipes</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-mapper">156</div>
          <div className="text-xs text-muted-foreground">Fields Mapped</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-tool-mapper">2,341</div>
          <div className="text-xs text-muted-foreground">Records Transformed</div>
        </div>
      </div>
      
      <Button 
        onClick={() => navigate(tool.route)}
        className="w-full bg-tool-mapper text-tool-mapper-foreground hover:bg-tool-mapper/90"
      >
        Launch {tool.name}
        <ArrowRight className="ml-2 h-4 w-4" />
      </Button>
    </div>
  );
};
