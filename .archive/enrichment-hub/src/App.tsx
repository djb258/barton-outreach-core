import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { EditModeProvider } from "@/contexts/EditModeContext";
import { EditModeToggle } from "@/components/EditModeToggle";
import Index from "./pages/Index";
import MonthlyUpdates from "./pages/MonthlyUpdates";
import DataOpsDashboard from "./pages/DataOpsDashboard";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <EditModeProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/monthly-updates" element={<MonthlyUpdates />} />
            <Route path="/dataops" element={<DataOpsDashboard />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
        <EditModeToggle />
      </TooltipProvider>
    </EditModeProvider>
  </QueryClientProvider>
);

export default App;
