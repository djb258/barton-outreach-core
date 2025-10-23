import React from 'react';
import { ApplicationBranch, ApplicationConfig } from '@/lib/template/application-config';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Database, Settings, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

interface BranchTemplateProps {
  config: ApplicationConfig;
  branch: ApplicationBranch;
}

export function BranchTemplate({ config, branch }: BranchTemplateProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-8">
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <Link to="/" className="hover:text-foreground">Home</Link>
          <span>→</span>
          <Link to="/doctrine-map" className="hover:text-foreground">Process Map</Link>
          <span>→</span>
          <span className="font-medium text-foreground">{branch.name}</span>
        </div>

        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <Link to="/doctrine-map">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Process Map
              </Button>
            </Link>
          </div>
          
          <div className="space-y-2">
            <h1 className="text-4xl font-bold">{branch.name}</h1>
            <p className="text-xl text-muted-foreground">{branch.description}</p>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono">
                {config.application.id_prefix}.{branch.id}
              </Badge>
              <Badge variant="secondary">
                {branch.processes.length} processes
              </Badge>
            </div>
          </div>
        </div>

        {/* Tools Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Tools & Integrations
            </CardTitle>
            <CardDescription>
              Technologies and services required for this branch
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {branch.tools.map((tool) => (
                <Badge key={tool} variant="default" className="px-3 py-1">
                  {tool}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Complete Process Flow */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Complete Process Flow</h2>
          
          <div className="grid gap-6">
            {branch.processes.map((process, index) => (
              <Card 
                key={process.id} 
                className="border-l-4 border-l-blue-500 hover:shadow-md transition-shadow"
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">
                          {index + 1}
                        </div>
                        <CardTitle className="text-lg">{process.name}</CardTitle>
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      </div>
                      <CardDescription>{process.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    
                    {/* Unique ID */}
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-muted-foreground">Unique ID</div>
                      <div className="font-mono text-sm bg-muted p-2 rounded">
                        {process.unique_id_template}
                      </div>
                    </div>

                    {/* Process ID */}
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-muted-foreground">Process ID</div>
                      <div className="font-medium text-sm bg-blue-50 p-2 rounded">
                        {process.name}
                      </div>
                    </div>

                    {/* Tool & Table */}
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-muted-foreground">Implementation</div>
                      <div className="space-y-1">
                        {process.tool && (
                          <Badge variant="outline" className="text-xs">
                            Tool: {process.tool}
                          </Badge>
                        )}
                        {process.table && (
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Database className="h-3 w-3" />
                            {process.table}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* ID Building Explanation */}
        <Card className="bg-slate-50 border-slate-200">
          <CardHeader>
            <CardTitle>ID Structure Explanation</CardTitle>
            <CardDescription>
              How unique IDs are constructed for this branch
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="font-mono text-sm bg-white p-3 rounded border">
                <span className="text-blue-600 font-bold">{config.application.id_prefix}</span>
                <span className="text-gray-400">.</span>
                <span className="text-green-600 font-bold">{branch.id}</span>
                <span className="text-gray-400">.</span>
                <span className="text-orange-600 font-bold">05</span>
                <span className="text-gray-400">.</span>
                <span className="text-red-600 font-bold">XX</span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="font-medium text-blue-600">Database</div>
                  <div className="text-muted-foreground">{config.application.id_prefix}</div>
                </div>
                <div>
                  <div className="font-medium text-green-600">Branch</div>
                  <div className="text-muted-foreground">{branch.id} ({branch.name})</div>
                </div>
                <div>
                  <div className="font-medium text-orange-600">Altitude</div>
                  <div className="text-muted-foreground">05 (5,000 ft)</div>
                </div>
                <div>
                  <div className="font-medium text-red-600">Step</div>
                  <div className="text-muted-foreground">01-{branch.processes.length.toString().padStart(2, '0')}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-center space-x-4">
          <Link to="/doctrine-map">
            <Button variant="outline">← Back to Process Map</Button>
          </Link>
          <Link to="/heir">
            <Button variant="outline">HEIR Agent System</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}