import React from "react";
import { BrowserRouter, Routes as RouterRoutes, Route } from "react-router-dom";
import ScrollToTop from "components/ScrollToTop";
import ErrorBoundary from "components/ErrorBoundary";
import NotFound from "pages/NotFound";
import DataIntakeDashboard from './pages/data-intake-dashboard';
import SystemAdministrationPanel from './pages/system-administration-panel';
import DataValidationConsole from './pages/data-validation-console';
import ValidationAdjusterConsole from './pages/validation-adjuster-console';

const Routes = () => {
  return (
    <BrowserRouter>
      <ErrorBoundary>
      <ScrollToTop />
      <RouterRoutes>
        {/* Define your route here */}
        <Route path="/" element={<DataIntakeDashboard />} />
        <Route path="/data-intake-dashboard" element={<DataIntakeDashboard />} />
        <Route path="/system-administration-panel" element={<SystemAdministrationPanel />} />
        <Route path="/data-validation-console" element={<DataValidationConsole />} />
        <Route path="/validation-adjuster-console" element={<ValidationAdjusterConsole />} />
        <Route path="*" element={<NotFound />} />
      </RouterRoutes>
      </ErrorBoundary>
    </BrowserRouter>
  );
};

export default Routes;