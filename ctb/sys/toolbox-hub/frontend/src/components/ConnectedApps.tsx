import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ExternalLink, Grid3x3, Plus, Trash2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface ConnectedApp {
  id: string;
  name: string;
  url: string;
  description?: string;
}

const PRESET_APPS: ConnectedApp[] = [
  {
    id: "router",
    name: "Router - Messy Logic",
    url: "https://messyflow-workbench.lovable.app",
    description: "Intake router — tags payloads and forwards to correct destination"
  }
];

export const ConnectedApps = () => {
  const [apps, setApps] = useState<ConnectedApp[]>(() => {
    const stored = localStorage.getItem("connected-apps");
    if (stored) {
      const parsedApps = JSON.parse(stored);
      // Auto-initialize preset apps if they don't exist
      const presetIds = PRESET_APPS.map(app => app.id);
      const existingIds = parsedApps.map((app: ConnectedApp) => app.id);
      const missingPresets = PRESET_APPS.filter(preset => !existingIds.includes(preset.id));
      
      if (missingPresets.length > 0) {
        const updatedApps = [...missingPresets, ...parsedApps];
        localStorage.setItem("connected-apps", JSON.stringify(updatedApps));
        return updatedApps;
      }
      return parsedApps;
    }
    // First time initialization
    localStorage.setItem("connected-apps", JSON.stringify(PRESET_APPS));
    return PRESET_APPS;
  });
  const [newApp, setNewApp] = useState({ name: "", url: "", description: "" });
  const [isAddingApp, setIsAddingApp] = useState(false);
  const { toast } = useToast();

  const saveApps = (updatedApps: ConnectedApp[]) => {
    setApps(updatedApps);
    localStorage.setItem("connected-apps", JSON.stringify(updatedApps));
  };

  const addApp = () => {
    if (!newApp.name || !newApp.url) {
      toast({
        title: "Missing information",
        description: "Please provide both name and URL",
        variant: "destructive",
      });
      return;
    }

    const app: ConnectedApp = {
      id: Date.now().toString(),
      ...newApp,
    };

    saveApps([...apps, app]);
    setNewApp({ name: "", url: "", description: "" });
    setIsAddingApp(false);
    toast({
      title: "App connected",
      description: `${app.name} has been added to your hub`,
    });
  };

  const removeApp = (id: string) => {
    // Prevent removal of preset apps
    const isPreset = PRESET_APPS.some(preset => preset.id === id);
    if (isPreset) {
      toast({
        title: "Cannot remove preset app",
        description: "This is a built-in spoke application",
        variant: "destructive",
      });
      return;
    }
    
    saveApps(apps.filter((app) => app.id !== id));
    toast({
      title: "App removed",
      description: "The connected app has been removed",
    });
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Grid3x3 className="h-4 w-4" />
          Connected Apps ({apps.length})
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Connected Applications (Spokes)</SheetTitle>
          <SheetDescription>
            Manage Lovable apps connected to this hub. Open them in new tabs or embed them inline.
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          {!isAddingApp ? (
            <Button onClick={() => setIsAddingApp(true)} className="w-full gap-2">
              <Plus className="h-4 w-4" />
              Add New App
            </Button>
          ) : (
            <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
              <div className="space-y-2">
                <Label htmlFor="app-name">App Name</Label>
                <Input
                  id="app-name"
                  placeholder="e.g., CRM Dashboard"
                  value={newApp.name}
                  onChange={(e) => setNewApp({ ...newApp, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="app-url">Lovable App URL</Label>
                <Input
                  id="app-url"
                  placeholder="https://your-app.lovable.app"
                  value={newApp.url}
                  onChange={(e) => setNewApp({ ...newApp, url: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="app-description">Description (optional)</Label>
                <Input
                  id="app-description"
                  placeholder="Brief description"
                  value={newApp.description}
                  onChange={(e) => setNewApp({ ...newApp, description: e.target.value })}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={addApp} className="flex-1">Add App</Button>
                <Button onClick={() => setIsAddingApp(false)} variant="outline">
                  Cancel
                </Button>
              </div>
            </div>
          )}

          <ScrollArea className="h-[500px] pr-4">
            <div className="space-y-3">
              {apps.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Grid3x3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No connected apps yet</p>
                  <p className="text-sm">Add your first Lovable app to get started</p>
                </div>
              ) : (
                apps.map((app) => (
                  <div
                    key={app.id}
                    className="p-4 border rounded-lg bg-card space-y-3 hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold">{app.name}</h3>
                        {app.description && (
                          <p className="text-sm text-muted-foreground mt-1">{app.description}</p>
                        )}
                        <p className="text-xs text-muted-foreground mt-1 break-all">{app.url}</p>
                      </div>
                      {!PRESET_APPS.some(preset => preset.id === app.id) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeApp(app.id)}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 gap-2"
                        onClick={() => window.open(app.url, "_blank")}
                      >
                        <ExternalLink className="h-3 w-3" />
                        Open in New Tab
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 gap-2"
                        onClick={() => {
                          window.location.href = `/embed/${app.id}`;
                        }}
                      >
                        View Embedded
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </SheetContent>
    </Sheet>
  );
};
