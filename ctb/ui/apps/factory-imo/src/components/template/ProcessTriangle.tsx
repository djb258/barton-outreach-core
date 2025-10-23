import React from 'react';
import { ApplicationConfig } from '@/lib/template/application-config';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ProcessTriangleProps {
  config: ApplicationConfig;
}

export function ProcessTriangle({ config }: ProcessTriangleProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">{config.application.domain} Process Map</h1>
          <p className="text-xl text-muted-foreground">
            Complete process triangle from strategic vision to tactical execution
          </p>
        </div>

        {/* Christmas Tree Structure */}
        <div className="max-w-6xl mx-auto">
          
          {/* 30,000 ft - TOP (NARROW) */}
          <div className="flex justify-center mb-8">
            <Card className="w-80 border-2 border-blue-500 bg-blue-50/50">
              <CardHeader className="text-center pb-3">
                <Badge variant="default" className="w-fit mx-auto bg-blue-600">
                  30,000 ft - {config.altitudes["30k"].name}
                </Badge>
                <CardTitle className="text-lg">{config.application.domain}</CardTitle>
                <CardDescription>{config.altitudes["30k"].description}</CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <div className="text-sm font-mono bg-muted p-2 rounded">
                  {config.application.id_prefix}.00.30
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Arrow Down */}
          <div className="flex justify-center mb-8">
            <ChevronDown className="h-8 w-8 text-muted-foreground" />
          </div>

          {/* 20,000 ft - EXPANDING (3 BRANCHES) */}
          <div className="flex justify-center mb-8">
            <Card className="w-96 border-2 border-green-500 bg-green-50/50">
              <CardHeader className="text-center pb-3">
                <Badge variant="secondary" className="w-fit mx-auto bg-green-600 text-white">
                  20,000 ft - {config.altitudes["20k"].name}
                </Badge>
                <CardTitle className="text-lg">Process Categories</CardTitle>
                <CardDescription>{config.altitudes["20k"].description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm font-mono bg-muted p-2 rounded text-center mb-4">
                  {config.application.id_prefix}.00.20
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Arrow Down */}
          <div className="flex justify-center mb-8">
            <ChevronDown className="h-8 w-8 text-muted-foreground" />
          </div>

          {/* 10,000 ft - WIDER (SHOW 3 MAIN BRANCHES) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {config.branches.map((branch, index) => (
              <Card 
                key={branch.id} 
                className="border-2 border-orange-500 bg-orange-50/50 hover:shadow-lg transition-shadow"
              >
                <CardHeader className="text-center pb-3">
                  <Badge variant="outline" className="w-fit mx-auto border-orange-600 text-orange-600">
                    10,000 ft - {config.altitudes["10k"].name}
                  </Badge>
                  <CardTitle className="text-lg">{branch.name}</CardTitle>
                  <CardDescription>{branch.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-sm font-mono bg-muted p-2 rounded text-center">
                    {config.application.id_prefix}.{branch.id}.10
                  </div>
                  
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">
                      <strong>Tools:</strong>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {branch.tools.map((tool) => (
                        <Badge key={tool} variant="outline" className="text-xs">
                          {tool}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="text-sm text-muted-foreground">
                    <strong>{branch.processes.length} execution steps</strong>
                  </div>

                  <Link to={branch.route}>
                    <Button className="w-full" variant="outline">
                      View Branch Details
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Arrow Down */}
          <div className="flex justify-center mb-8">
            <ChevronDown className="h-8 w-8 text-muted-foreground" />
          </div>

          {/* 5,000 ft - WIDEST (BASE) */}
          <div className="flex justify-center">
            <Card className="w-full max-w-4xl border-2 border-red-500 bg-red-50/50">
              <CardHeader className="text-center pb-3">
                <Badge variant="destructive" className="w-fit mx-auto">
                  5,000 ft - {config.altitudes["5k"].name}
                </Badge>
                <CardTitle className="text-lg">Tactical Execution Steps</CardTitle>
                <CardDescription>{config.altitudes["5k"].description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm font-mono bg-muted p-2 rounded text-center mb-4">
                  {config.application.id_prefix}.XX.05.XX
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {config.branches.map((branch) => (
                    <div key={branch.id} className="space-y-2">
                      <h4 className="font-medium text-sm">{branch.name}:</h4>
                      <div className="space-y-1">
                        {branch.processes.slice(0, 3).map((process) => (
                          <div key={process.id} className="text-xs bg-white p-2 rounded border">
                            <div className="font-mono text-orange-600">
                              {process.unique_id_template}
                            </div>
                            <div className="text-muted-foreground">
                              {process.name}
                            </div>
                          </div>
                        ))}
                        {branch.processes.length > 3 && (
                          <div className="text-xs text-muted-foreground text-center">
                            +{branch.processes.length - 3} more steps
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-center space-x-4">
          <Link to="/">
            <Button variant="outline">← Back to Dashboard</Button>
          </Link>
          <Link to="/heir">
            <Button variant="outline">HEIR Agent System</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}