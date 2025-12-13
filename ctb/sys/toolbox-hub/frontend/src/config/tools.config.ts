import { LucideIcon } from 'lucide-react';
import { 
  Route, 
  CheckCircle, 
  Map, 
  FileText, 
  FileEdit, 
  Database, 
  BookOpen 
} from 'lucide-react';

export interface ToolConfig {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  color: string;
  apiPrefix: string;
  route: string;
  bartonId: string;
  branch: string;
  enabled: boolean;
}

export const TOOLS: Record<string, ToolConfig> = {
  router: {
    id: 'router',
    name: 'Router (Messy Logic)',
    description: 'Intake router — tags payloads and forwards to correct destination',
    icon: Route,
    color: 'tool-router',
    apiPrefix: '/api/messyflow',
    route: '/router',
    bartonId: '06.01.01',
    branch: 'ctb/messyflow-backend',
    enabled: true,
  },
  validator: {
    id: 'validator',
    name: 'Validator (Neon Agent)',
    description: 'Runs enrichment + validation rules stored in Neon',
    icon: CheckCircle,
    color: 'tool-validator',
    apiPrefix: '/api/validator',
    route: '/validator',
    bartonId: '06.01.02',
    branch: 'ctb/validator-backend',
    enabled: true,
  },
  mapper: {
    id: 'mapper',
    name: 'Mapper',
    description: 'Field mapping tool for CSV/API → STAMPED schema',
    icon: Map,
    color: 'tool-mapper',
    apiPrefix: '/api/mapper',
    route: '/mapper',
    bartonId: '06.01.03',
    branch: 'ctb/mapper-backend',
    enabled: true,
  },
  parser: {
    id: 'parser',
    name: 'Parser',
    description: 'PDF / Doc parser for extracting structured data',
    icon: FileText,
    color: 'tool-parser',
    apiPrefix: '/api/parser',
    route: '/parser',
    bartonId: '06.01.04',
    branch: 'ctb/parser-backend',
    enabled: true,
  },
  docfiller: {
    id: 'docfiller',
    name: 'Doc Filler',
    description: 'Fills templates with mapped data',
    icon: FileEdit,
    color: 'tool-docfiller',
    apiPrefix: '/api/doc-filler',
    route: '/doc-filler',
    bartonId: '06.01.05',
    branch: 'ctb/doc-filler-backend',
    enabled: true,
  },
  logger: {
    id: 'logger',
    name: 'Logger / Monitor',
    description: 'Central dashboard for audit + error tracking',
    icon: Database,
    color: 'tool-logger',
    apiPrefix: '/api/logger',
    route: '/logger',
    bartonId: '06.01.06',
    branch: 'ctb/logger-backend',
    enabled: true,
  },
  documentation: {
    id: 'documentation',
    name: 'Documentation',
    description: 'Self-documenting dashboard explaining how all tools tie together',
    icon: BookOpen,
    color: 'tool-docs',
    apiPrefix: '/api/docs',
    route: '/documentation',
    bartonId: '06.01.07',
    branch: 'ctb/docs-backend',
    enabled: true,
  },
};

export const getEnabledTools = (): ToolConfig[] => {
  return Object.values(TOOLS).filter(tool => tool.enabled);
};

export const getToolById = (id: string): ToolConfig | undefined => {
  return TOOLS[id];
};
