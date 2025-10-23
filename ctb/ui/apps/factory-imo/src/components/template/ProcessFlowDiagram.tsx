import React, { useState } from 'react';
import { ApplicationConfig } from '@/lib/template/application-config';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronRight, Database, Settings, ArrowRight, Users, BookOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ProcessFlowDiagramProps {
  config: ApplicationConfig;
}

export function ProcessFlowDiagram({ config }: ProcessFlowDiagramProps) {
  const [expandedBranches, setExpandedBranches] = useState<string[]>(['01', '02', '03']);

  const toggleBranch = (branchId: string) => {
    setExpandedBranches(prev => 
      prev.includes(branchId) 
        ? prev.filter(id => id !== branchId)
        : [...prev, branchId]
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">{config.application.domain} Process Flow</h1>
          <p className="text-xl text-muted-foreground">
            Complete workflow diagram with tools, steps, and process IDs
          </p>
        </div>

        {/* Main Flow Diagram */}
        <div className="max-w-7xl mx-auto">
          
          {/* Branch Headers with Flow Arrows */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {config.branches.map((branch, index) => (
              <div key={branch.id} className="relative">
                {/* Branch Header Card */}
                <Card className="border-2 border-blue-500 bg-blue-50/50 hover:shadow-lg transition-shadow">
                  <CardHeader className="text-center pb-3">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <Badge variant="default" className="bg-blue-600">
                        Branch {branch.id}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleBranch(branch.id)}
                        className="p-1"
                      >
                        <ChevronRight 
                          className={`h-4 w-4 transition-transform ${
                            expandedBranches.includes(branch.id) ? 'rotate-90' : ''
                          }`}
                        />
                      </Button>
                    </div>
                    <CardTitle className="text-lg">{branch.name}</CardTitle>
                    <CardDescription>{branch.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="text-sm font-mono bg-muted p-2 rounded text-center">
                      {config.application.id_prefix}.{branch.id}
                    </div>
                    
                    <div className="flex flex-wrap gap-1 justify-center">
                      {branch.tools.slice(0, 3).map((tool) => (
                        <Badge key={tool} variant="outline" className="text-xs">
                          {tool}
                        </Badge>
                      ))}
                      {branch.tools.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{branch.tools.length - 3}
                        </Badge>
                      )}
                    </div>

                    <div className="text-center text-sm text-muted-foreground">
                      {branch.processes.length} steps
                    </div>

                    <Link to={branch.route}>
                      <Button variant="outline" size="sm" className="w-full">
                        View Details
                      </Button>
                    </Link>
                  </CardContent>
                </Card>

                {/* Flow Arrow (except for last branch) */}
                {index < config.branches.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2 z-10">
                    <div className="bg-white border-2 border-gray-300 rounded-full p-2 shadow-md">
                      <ArrowRight className="h-6 w-6 text-blue-600" />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Detailed Steps Under Each Branch */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {config.branches.map((branch) => (
              <div key={branch.id} className="space-y-4">
                
                {/* Branch Steps Container */}
                {expandedBranches.includes(branch.id) && (
                  <div className="space-y-3">
                    <div className="text-center">
                      <Badge variant="secondary" className="mb-4">
                        {branch.name} - Detailed Steps
                      </Badge>
                    </div>

                    {/* Individual Steps */}
                    {branch.processes.map((process, stepIndex) => (
                      <Card 
                        key={process.id}
                        className="border-l-4 border-l-green-500 bg-green-50/30 hover:shadow-md transition-shadow cursor-pointer"
                      >
                        <CardContent className="p-4">
                          <div className="space-y-3">
                            
                            {/* Step Header */}
                            <div className="flex items-center gap-2">
                              <div className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                                {stepIndex + 1}
                              </div>
                              <div className="font-medium text-sm">{process.name}</div>
                            </div>

                            {/* Process Description */}
                            <div className="text-xs text-muted-foreground pl-8">
                              {process.description}
                            </div>

                            {/* Tool & Table Info */}
                            <div className="pl-8 space-y-2">
                              {process.tool && (
                                <div className="flex items-center gap-2">
                                  <Settings className="h-3 w-3 text-blue-500" />
                                  <Badge variant="outline" className="text-xs">
                                    {process.tool}
                                  </Badge>
                                </div>
                              )}
                              
                              {process.table && (
                                <div className="flex items-center gap-2">
                                  <Database className="h-3 w-3 text-purple-500" />
                                  <span className="text-xs text-muted-foreground font-mono">
                                    {process.table}
                                  </span>
                                </div>
                              )}
                            </div>

                            {/* Process ID */}
                            <div className="pl-8">
                              <div className="bg-gray-100 border border-gray-200 rounded p-2">
                                <div className="text-xs text-muted-foreground mb-1">Process ID:</div>
                                <div className="font-mono text-sm font-bold text-green-600">
                                  {process.unique_id_template}
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {/* Subagents Section */}
                    {branch.subagents && branch.subagents.length > 0 && (
                      <Card className="mt-4 bg-blue-50/50 border-blue-200">
                        <CardHeader className="pb-3">
                          <CardTitle className="flex items-center gap-2 text-sm">
                            <Users className="h-4 w-4 text-blue-600" />
                            Subagents Used (Build Documentation)
                          </CardTitle>
                          <CardDescription className="text-xs">
                            AI agents that constructed this process - no longer needed once built
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-0">
                          <div className="flex flex-wrap gap-2">
                            {branch.subagents.map((agent) => (
                              <Badge key={agent} variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                                {agent}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Doctrines Section */}
                    {branch.doctrines && branch.doctrines.length > 0 && (
                      <Card className="mt-4 bg-purple-50/50 border-purple-200">
                        <CardHeader className="pb-3">
                          <CardTitle className="flex items-center gap-2 text-sm">
                            <BookOpen className="h-4 w-4 text-purple-600" />
                            Governing Doctrines
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Business rules and principles that guide this process
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-0">
                          <div className="flex flex-wrap gap-2">
                            {branch.doctrines.map((doctrine) => (
                              <Badge key={doctrine} variant="outline" className="text-xs border-purple-300 text-purple-700">
                                {doctrine}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Data Flow Indicator */}
                    {branch.id !== '03' && (
                      <div className="flex justify-center py-4">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <div className="h-px bg-gray-300 w-8"></div>
                          <span>Data flows to next branch</span>
                          <ArrowRight className="h-4 w-4" />
                          <div className="h-px bg-gray-300 w-8"></div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Process ID Legend */}
          <Card className="mt-12 bg-slate-50 border-slate-200">
            <CardHeader>
              <CardTitle>Process ID Structure</CardTitle>
              <CardDescription>
                How unique IDs are automatically generated for each step
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="font-mono text-sm bg-white p-3 rounded border">
                  <span className="text-blue-600 font-bold">{config.application.id_prefix}</span>
                  <span className="text-gray-400">.</span>
                  <span className="text-green-600 font-bold">[Branch]</span>
                  <span className="text-gray-400">.</span>
                  <span className="text-orange-600 font-bold">05</span>
                  <span className="text-gray-400">.</span>
                  <span className="text-red-600 font-bold">[Step]</span>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="font-medium text-blue-600">Application</div>
                    <div className="text-muted-foreground">{config.application.id_prefix}</div>
                  </div>
                  <div>
                    <div className="font-medium text-green-600">Branch</div>
                    <div className="text-muted-foreground">01, 02, 03</div>
                  </div>
                  <div>
                    <div className="font-medium text-orange-600">Altitude</div>
                    <div className="text-muted-foreground">05 (5,000 ft)</div>
                  </div>
                  <div>
                    <div className="font-medium text-red-600">Step</div>
                    <div className="text-muted-foreground">Auto-increment</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
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