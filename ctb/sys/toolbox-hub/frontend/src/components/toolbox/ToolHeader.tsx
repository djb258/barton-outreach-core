import { Database, GitBranch, Hash, FileText } from "lucide-react";
import { ConnectedApps } from "@/components/ConnectedApps";

export const ToolHeader = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            <h1 className="text-xl font-bold tracking-tight">Barton Toolbox</h1>
          </div>
          
          <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              <span className="font-medium">CTB Branch:</span>
              <span>sys</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Hash className="h-4 w-4" />
              <span className="font-medium">Barton ID:</span>
              <span>06.01.00</span>
            </div>
            
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span className="font-medium">Doctrine:</span>
              <span>ORBT / STAMPED</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-xs font-mono text-muted-foreground hidden md:inline">CTB-TOOLBOX-SHELL</span>
          <ConnectedApps />
        </div>
      </div>
    </header>
  );
};
