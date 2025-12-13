import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink } from "lucide-react";

interface ConnectedApp {
  id: string;
  name: string;
  url: string;
  description?: string;
}

const EmbeddedApp = () => {
  const { appId } = useParams();
  const navigate = useNavigate();
  const [app, setApp] = useState<ConnectedApp | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("connected-apps");
    if (stored) {
      const apps: ConnectedApp[] = JSON.parse(stored);
      const foundApp = apps.find((a) => a.id === appId);
      setApp(foundApp || null);
    }
  }, [appId]);

  if (!app) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold">App not found</h2>
          <Button onClick={() => navigate("/")}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Hub
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b bg-card">
        <div className="container flex items-center justify-between py-3 px-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate("/")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Hub
            </Button>
            <div className="border-l pl-4">
              <h1 className="font-semibold">{app.name}</h1>
              {app.description && (
                <p className="text-sm text-muted-foreground">{app.description}</p>
              )}
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(app.url, "_blank")}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Open in New Tab
          </Button>
        </div>
      </header>

      <div className="flex-1 relative">
        <iframe
          src={app.url}
          className="absolute inset-0 w-full h-full border-0"
          title={app.name}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals"
        />
      </div>
    </div>
  );
};

export default EmbeddedApp;
