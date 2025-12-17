import { ReactNode } from "react";
import { useEditMode } from "@/contexts/EditModeContext";
import { toast } from "sonner";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface ComponentIdProps {
  id: string;
  children: ReactNode;
  type?: string;
  path?: string;
}

export const ComponentId = ({ id, children, type, path }: ComponentIdProps) => {
  const { isEditMode } = useEditMode();

  const handleCopyId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    toast.success(`ID copied: ${id}`);
  };

  if (!isEditMode) {
    return <>{children}</>;
  }

  return (
    <div className="relative">
      {children}
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={handleCopyId}
            className="absolute top-0 left-0 z-50 px-2 py-1 text-xs font-mono bg-primary/90 text-primary-foreground rounded-br-md backdrop-blur-sm hover:scale-105 transition-transform cursor-pointer"
          >
            {id}
          </button>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-xs space-y-1">
            <div className="font-semibold">Component ID</div>
            <div className="font-mono">{id}</div>
            {type && <div className="text-muted-foreground">Type: {type}</div>}
            {path && <div className="text-muted-foreground">Path: {path}</div>}
            <div className="text-muted-foreground mt-2">Click to copy</div>
          </div>
        </TooltipContent>
      </Tooltip>
    </div>
  );
};
