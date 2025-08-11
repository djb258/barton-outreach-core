import React from 'react';
import { ApplicationConfig } from '@/lib/template/application-config';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Users, Activity, Shield, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface BartonTemplateProps {
  config: ApplicationConfig;
}

export function BartonTemplate({ config }: BartonTemplateProps) {
  console.log('BartonTemplate rendering with config:', config);
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-8">
        {/* Header - Configurable */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <Building2 className="h-16 w-16 text-primary" />
          </div>
          <h1 className="text-4xl font-bold">{config.application.name}</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            {config.application.description}
          </p>
        </div>

        {/* Feature Cards - Template Structure */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          
          {/* Process Map Card */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Process Map
              </CardTitle>
              <CardDescription>
                View the complete {config.application.domain} process triangle with all branches
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to="/doctrine-map">
                <Button className="w-full">
                  View Process Triangle
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Branch Network Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Process Branches
              </CardTitle>
              <CardDescription>
                {config.branches.length} specialized process branches ready for execution
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">Ready</div>
              <p className="text-sm text-muted-foreground">All systems operational</p>
            </CardContent>
          </Card>

          {/* System Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                System Status
              </CardTitle>
              <CardDescription>
                Real-time monitoring of process health and performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">Optimal</div>
              <p className="text-sm text-muted-foreground">95% success rate</p>
            </CardContent>
          </Card>
        </div>

        {/* Process Branches Quick Links */}
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-6">Process Branches</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {config.branches.map((branch, index) => (
              <Card key={branch.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="bg-primary text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </span>
                    {branch.name}
                  </CardTitle>
                  <CardDescription>{branch.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">
                      <strong>Tools:</strong> {branch.tools.join(', ')}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <strong>Steps:</strong> {branch.processes.length} processes
                    </div>
                    <Link to={branch.route}>
                      <Button variant="outline" className="w-full mt-3">
                        View Details
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* About Section - Configurable */}
        <div className="max-w-4xl mx-auto text-center space-y-4">
          <h2 className="text-2xl font-bold">About {config.application.domain}</h2>
          <p className="text-muted-foreground leading-relaxed">
            This system represents a structured approach to {config.application.domain.toLowerCase()} 
            operations. Built with the Barton Doctrine methodology, each process is organized across 
            multiple altitudes from strategic vision down to tactical execution, ensuring comprehensive 
            coverage and systematic implementation.
          </p>
        </div>
      </div>
    </div>
  );
}