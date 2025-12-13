import { lazy, Suspense } from 'react';
import { ToolConfig } from '@/config/tools.config';
import { Skeleton } from '@/components/ui/skeleton';

interface ToolLauncherProps {
  tool: ToolConfig;
}

const toolComponents = {
  router: lazy(() => import('./RouterTool').then(m => ({ default: m.RouterTool }))),
  validator: lazy(() => import('./ValidatorTool').then(m => ({ default: m.ValidatorTool }))),
  mapper: lazy(() => import('./MapperTool').then(m => ({ default: m.MapperTool }))),
  parser: lazy(() => import('./ParserTool').then(m => ({ default: m.ParserTool }))),
  docfiller: lazy(() => import('./DocFillerTool').then(m => ({ default: m.DocFillerTool }))),
  logger: lazy(() => import('./LoggerTool').then(m => ({ default: m.LoggerTool }))),
  documentation: lazy(() => import('./DocumentationTool').then(m => ({ default: m.DocumentationTool }))),
};

export const ToolLauncher = ({ tool }: ToolLauncherProps) => {
  const ToolComponent = toolComponents[tool.id as keyof typeof toolComponents];
  
  if (!ToolComponent) {
    return (
      <div className="text-muted-foreground text-sm">
        Tool component not found for: {tool.id}
      </div>
    );
  }

  return (
    <Suspense fallback={<Skeleton className="h-32 w-full" />}>
      <ToolComponent />
    </Suspense>
  );
};
