import { useNavigate } from 'react-router-dom';
import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Edit2, MoreVertical } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ToolConfig } from "@/config/tools.config";
import { ToolLauncher } from "./ToolLauncher";

interface ToolAccordionItemProps {
  tool: ToolConfig;
}

export const ToolAccordionItem = ({ tool }: ToolAccordionItemProps) => {
  const navigate = useNavigate();
  const Icon = tool.icon;
  
  const handleEdit = () => {
    console.log(`Edit ${tool.name} - ID: ${tool.id}-tool`);
  };

  const handleViewBranch = () => {
    window.open(
      `https://github.com/djb258/barton-toolbox-hub/tree/${tool.branch}`,
      '_blank'
    );
  };

  return (
    <AccordionItem
      value={tool.id}
      data-tool-id={`${tool.id}-tool`}
      data-barton-id={tool.bartonId}
      className={`border border-${tool.color}/30 rounded-lg bg-card overflow-hidden`}
    >
      <AccordionTrigger 
        className={`px-6 py-4 hover:no-underline hover:bg-${tool.color}/5`}
      >
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-${tool.color} text-${tool.color}-foreground`}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="text-left">
              <div className="font-semibold">{tool.name}</div>
              <div className="text-sm text-muted-foreground">
                {tool.description}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className={`text-${tool.color} hover:text-${tool.color}/80 hover:bg-${tool.color}/10`}
              onClick={(e) => {
                e.stopPropagation();
                handleEdit();
              }}
            >
              <Edit2 className="h-4 w-4" />
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={handleEdit}>
                  Edit Tool
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleViewBranch}>
                  View Backend Branch
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate(tool.route)}>
                  Open Full Page
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </AccordionTrigger>
      
      <AccordionContent className="px-6 pb-6">
        <ToolLauncher tool={tool} />
      </AccordionContent>
    </AccordionItem>
  );
};
