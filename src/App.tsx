import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import HEIRPage from "./pages/HEIRPage";
import DoctrineMapPage from "./pages/DoctrineMapPage";
import LeadIntakePage from "./pages/doctrine/LeadIntakePage";
import MessageGenerationPage from "./pages/doctrine/MessageGenerationPage";
import CampaignExecutionPage from "./pages/doctrine/CampaignExecutionPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/heir" element={<HEIRPage />} />
          <Route path="/doctrine-map" element={<DoctrineMapPage />} />
          <Route path="/doctrine/lead-intake" element={<LeadIntakePage />} />
          <Route path="/doctrine/message-generation" element={<MessageGenerationPage />} />
          <Route path="/doctrine/campaign-execution" element={<CampaignExecutionPage />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
