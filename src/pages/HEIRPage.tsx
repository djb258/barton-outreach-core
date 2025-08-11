import { HEIRProvider } from '@/components/heir/HEIRContext';
import HEIRDashboard from '@/components/heir/HEIRDashboard';

export default function HEIRPage() {
  return (
    <HEIRProvider>
      <div className="min-h-screen bg-background">
        <div className="container mx-auto p-6">
          <HEIRDashboard />
        </div>
      </div>
    </HEIRProvider>
  );
}