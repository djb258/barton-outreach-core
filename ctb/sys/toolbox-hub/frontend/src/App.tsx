import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";
import { getEnabledTools } from "@/config/tools.config";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import { Skeleton } from "@/components/ui/skeleton";

const queryClient = new QueryClient();

// Lazy load all tool pages
const toolPages = {
  router: lazy(() => import("./pages/RouterPage")),
  validator: lazy(() => import("./pages/ValidatorPage")),
  mapper: lazy(() => import("./pages/MapperPage")),
  parser: lazy(() => import("./pages/ParserPage")),
  docfiller: lazy(() => import("./pages/DocFillerPage")),
  logger: lazy(() => import("./pages/LoggerPage")),
  documentation: lazy(() => import("./pages/DocumentationPage")),
};

const App = () => {
  const tools = getEnabledTools();

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            
            {/* Dynamic tool routes */}
            {tools.map((tool) => {
              const PageComponent = toolPages[tool.id as keyof typeof toolPages];
              return (
                <Route
                  key={tool.id}
                  path={tool.route}
                  element={
                    <Suspense fallback={<Skeleton className="h-screen w-full" />}>
                      <PageComponent />
                    </Suspense>
                  }
                />
              );
            })}
            
            {/* Catch-all */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
