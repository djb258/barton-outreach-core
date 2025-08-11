import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, ArrowRight, Users, Activity, Shield } from "lucide-react";
import { Link } from "react-router-dom";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-8">
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <Building2 className="h-16 w-16 text-primary" />
          </div>
          <h1 className="text-4xl font-bold">Barton Outreach Core</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Powered by the HEIR Agent System - Hierarchical Execution Intelligence & Repair
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                HEIR System
              </CardTitle>
              <CardDescription>
                Access the full HEIR agent dashboard to monitor and manage your intelligent agents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to="/heir">
                <Button className="w-full">
                  Open HEIR Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Agent Network
              </CardTitle>
              <CardDescription>
                12 specialized agents ready for deployment across orchestration, management, and specialist roles
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">Ready</div>
              <p className="text-sm text-muted-foreground">All systems operational</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                System Status
              </CardTitle>
              <CardDescription>
                Real-time monitoring of system health and performance metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">Optimal</div>
              <p className="text-sm text-muted-foreground">95% success rate</p>
            </CardContent>
          </Card>
        </div>

        <div className="max-w-4xl mx-auto text-center space-y-4">
          <h2 className="text-2xl font-bold">About HEIR System</h2>
          <p className="text-muted-foreground leading-relaxed">
            The HEIR (Hierarchical Execution Intelligence & Repair) system represents a new paradigm in 
            automated development and operations. Built like a skyscraper with multiple specialized floors, 
            each agent has distinct responsibilities while working together toward common goals. From 
            orchestrators at the top managing strategic decisions, to specialists handling specific 
            technical implementations, HEIR ensures robust, scalable, and intelligent automation.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Index;
