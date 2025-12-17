import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StateAccordion } from "@/components/StateAccordion";
import { CostFooter } from "@/components/CostFooter";
import { NavLink } from "@/components/NavLink";
import { Database } from "lucide-react";
import { ComponentId } from "@/components/ComponentId";

const STATES = ["WV", "PA", "OH", "MD", "VA", "KY"];

const Index = () => {
  const [activeTab, setActiveTab] = useState<"people" | "companies">("people");

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <ComponentId id="index-header" type="header" path="Index > Header">
        <header className="border-b bg-card">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <ComponentId id="index-header-logo" type="logo">
                  <div className="flex items-center gap-3">
                    <Database className="h-8 w-8 text-primary" />
                    <h1 className="text-2xl font-bold text-foreground">Enrichment Workbench</h1>
                  </div>
                </ComponentId>
                <div className="flex gap-4">
                  <ComponentId id="index-nav-enrichment" type="link">
                    <NavLink
                      to="/"
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      activeClassName="text-foreground font-semibold"
                    >
                      Enrichment Queue
                    </NavLink>
                  </ComponentId>
                  <ComponentId id="index-nav-monthly" type="link">
                    <NavLink
                      to="/monthly-updates"
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      activeClassName="text-foreground font-semibold"
                    >
                      Monthly Updates
                    </NavLink>
                  </ComponentId>
                  <ComponentId id="index-nav-dataops" type="link">
                    <NavLink
                      to="/dataops"
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      activeClassName="text-foreground font-semibold"
                    >
                      DataOps Dashboard
                    </NavLink>
                  </ComponentId>
                </div>
              </div>
              <ComponentId id="index-status-badge" type="status">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
                  <span>Connected to Lovable Cloud — Workspace Active</span>
                </div>
              </ComponentId>
            </div>
          </div>
        </header>
      </ComponentId>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <ComponentId id="index-tabs" type="tabs" path="Index > Tabs">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "people" | "companies")}>
            <ComponentId id="index-tabs-list" type="list">
              <TabsList className="w-full max-w-md">
                <ComponentId id="index-tab-people" type="tab-trigger">
                  <TabsTrigger value="people" className="flex-1">
                    People Records
                  </TabsTrigger>
                </ComponentId>
                <ComponentId id="index-tab-companies" type="tab-trigger">
                  <TabsTrigger value="companies" className="flex-1">
                    Company Records
                  </TabsTrigger>
                </ComponentId>
              </TabsList>
            </ComponentId>

          <TabsContent value="people" className="mt-6 space-y-4">
            {STATES.map((state) => (
              <ComponentId key={state} id={`index-people-${state.toLowerCase()}-accordion`} type="accordion">
                <StateAccordion state={state} entity="people" />
              </ComponentId>
            ))}
          </TabsContent>

          <TabsContent value="companies" className="mt-6 space-y-4">
            {STATES.map((state) => (
              <ComponentId key={state} id={`index-companies-${state.toLowerCase()}-accordion`} type="accordion">
                <StateAccordion state={state} entity="companies" />
              </ComponentId>
            ))}
          </TabsContent>
        </Tabs>
        </ComponentId>
      </main>

      {/* Footer */}
      <ComponentId id="index-footer" type="footer">
        <CostFooter />
      </ComponentId>
    </div>
  );
};

export default Index;
