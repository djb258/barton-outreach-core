import { ToolHeader } from "@/components/toolbox/ToolHeader";
import { getEnabledTools } from "@/config/tools.config";
import { ToolAccordionItem } from "@/components/toolbox/ToolAccordionItem";
import { Accordion } from "@/components/ui/accordion";

const Index = () => {
  const tools = getEnabledTools();

  return (
    <div className="min-h-screen bg-background">
      <ToolHeader />
      
      <main className="container py-8 px-6">
        <div className="mb-8">
          <h2 className="text-2xl font-bold tracking-tight mb-2">
            Process Management Tools
          </h2>
          <p className="text-muted-foreground">
            Unified interface for routing, validation, mapping, and monitoring
          </p>
        </div>

        <Accordion type="single" collapsible className="space-y-4">
          {tools.map((tool) => (
            <ToolAccordionItem key={tool.id} tool={tool} />
          ))}
        </Accordion>
      </main>
    </div>
  );
};

export default Index;
