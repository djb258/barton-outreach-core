/**
 * Types for Miro-Linear Workflow Integration
 */

// Miro Types
export interface MiroPosition {
  x: number;
  y: number;
}

export interface MiroGeometry {
  width: number;
  height: number;
}

export interface MiroItem {
  id?: string;
  type: 'sticky_note' | 'shape' | 'text' | 'frame' | 'connector';
  content: string;
  position: MiroPosition;
  geometry?: MiroGeometry;
  style?: Record<string, string>;
}

export interface MiroFrame extends MiroItem {
  type: 'frame';
  title: string;
  children: MiroItem[];
}

export interface MiroBoardConfig {
  boardId: string;
  token: string;
}

// Linear Types
export interface LinearIssue {
  id: string;
  identifier: string;
  title: string;
  description?: string;
  state: string;
  priority: number;
  labels: string[];
  url: string;
}

export interface LinearTeam {
  id: string;
  key: string;
  name: string;
}

export interface LinearConfig {
  apiKey: string;
  teamKey: string;
}

// Workflow Types
export interface WorkflowConfig {
  miro: MiroBoardConfig;
  linear: LinearConfig;
  defaultDocsPath: string;
}

export interface ParsedMarkdown {
  title: string;
  sections: MarkdownSection[];
  codeBlocks: CodeBlock[];
  tables: MarkdownTable[];
}

export interface MarkdownSection {
  level: number;
  title: string;
  content: string;
  subsections: MarkdownSection[];
}

export interface CodeBlock {
  language: string;
  content: string;
  lineStart: number;
}

export interface MarkdownTable {
  headers: string[];
  rows: string[][];
}

// Wheel-specific types for BICYCLE_WHEEL_DOCTRINE visualization
export interface WheelStructure {
  hub: WheelHub;
  spokes: WheelSpoke[];
  failureSpokes: WheelSpoke[];
  subWheels: WheelStructure[];
}

export interface WheelHub {
  name: string;
  coreMetric?: string;
  anchorFields: string[];
}

export interface WheelSpoke {
  name: string;
  functions: string[];
  feedsHub: boolean;
}

// CLI Types
export type WorkflowCommand = 
  | 'push'
  | 'linear-sync'
  | 'issues'
  | 'wheel-viz'
  | 'help';

export interface CommandArgs {
  command: WorkflowCommand;
  filePath?: string;
  boardId?: string;
  teamKey?: string;
  issueTitle?: string;
  verbose?: boolean;
}


