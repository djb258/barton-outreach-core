/**
 * Miro Uploader
 * =============
 * Push markdown files to Miro boards as structured diagrams.
 * 
 * Workflow: File → Miro
 * 
 * Features:
 * - Parse markdown files and extract structure
 * - Create frames for documents
 * - Create shapes for headers/hubs
 * - Create sticky notes for sections
 * - Create connectors for relationships
 * - Special handling for Bicycle Wheel Doctrine format
 */

import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';
import type { 
  MiroItem, 
  MiroPosition, 
  ParsedMarkdown, 
  MarkdownSection,
  WheelStructure,
  WheelHub,
  WheelSpoke 
} from './types.js';

// Load environment variables
config({ path: path.resolve(process.cwd(), '.env') });

const MIRO_API_BASE = 'https://api.miro.com/v2';

interface MiroApiConfig {
  token: string;
  boardId: string;
}

// Color palette for different section types
const COLORS = {
  hub: '#4262FF',      // Blue - central hub
  spoke: '#00C875',    // Green - spokes
  failure: '#FF5722',  // Red/Orange - failure spokes
  subWheel: '#9C27B0', // Purple - sub-wheels
  frame: '#F5F5F5',    // Light gray - frames
  text: '#333333',     // Dark gray - text
};

/**
 * Make authenticated request to Miro API
 */
async function miroRequest(
  endpoint: string,
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
  config: MiroApiConfig,
  body?: Record<string, unknown>
): Promise<unknown> {
  const url = `${MIRO_API_BASE}/boards/${config.boardId}${endpoint}`;
  
  const response = await fetch(url, {
    method,
    headers: {
      'Authorization': `Bearer ${config.token}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Miro API error: ${response.status} - ${error}`);
  }

  return response.json();
}

/**
 * Create a frame on the Miro board
 */
async function createFrame(
  config: MiroApiConfig,
  title: string,
  position: MiroPosition,
  width: number,
  height: number
): Promise<string> {
  const result = await miroRequest('/frames', 'POST', config, {
    data: {
      title,
      format: 'custom',
    },
    position: { x: position.x, y: position.y, origin: 'center' },
    geometry: { width, height },
  }) as { id: string };
  
  return result.id;
}

/**
 * Create a shape (rectangle, circle, etc.) on the Miro board
 */
async function createShape(
  config: MiroApiConfig,
  content: string,
  position: MiroPosition,
  shapeType: 'rectangle' | 'circle' | 'diamond' | 'parallelogram' = 'rectangle',
  fillColor: string = COLORS.hub,
  width: number = 200,
  height: number = 100
): Promise<string> {
  const result = await miroRequest('/shapes', 'POST', config, {
    data: {
      shape: shapeType,
      content: `<p>${content}</p>`,
    },
    style: {
      fillColor,
      fontFamily: 'arial',
      fontSize: '14',
      textAlign: 'center',
      textAlignVertical: 'middle',
      borderColor: '#1a1a1a',
      borderWidth: '2',
    },
    position: { x: position.x, y: position.y, origin: 'center' },
    geometry: { width, height },
  }) as { id: string };
  
  return result.id;
}

/**
 * Create a sticky note on the Miro board
 */
async function createStickyNote(
  config: MiroApiConfig,
  content: string,
  position: MiroPosition,
  color: 'yellow' | 'green' | 'blue' | 'red' | 'purple' | 'gray' = 'yellow'
): Promise<string> {
  const result = await miroRequest('/sticky_notes', 'POST', config, {
    data: {
      content,
      shape: 'square',
    },
    style: {
      fillColor: color,
    },
    position: { x: position.x, y: position.y, origin: 'center' },
  }) as { id: string };
  
  return result.id;
}

/**
 * Create a text item on the Miro board
 */
async function createText(
  config: MiroApiConfig,
  content: string,
  position: MiroPosition,
  fontSize: number = 14
): Promise<string> {
  const result = await miroRequest('/texts', 'POST', config, {
    data: {
      content: `<p>${content}</p>`,
    },
    style: {
      fontSize: fontSize.toString(),
      textAlign: 'left',
    },
    position: { x: position.x, y: position.y, origin: 'center' },
  }) as { id: string };
  
  return result.id;
}

/**
 * Create a connector between two items
 */
async function createConnector(
  config: MiroApiConfig,
  startItemId: string,
  endItemId: string,
  strokeColor: string = '#333333'
): Promise<string> {
  const result = await miroRequest('/connectors', 'POST', config, {
    startItem: { id: startItemId },
    endItem: { id: endItemId },
    style: {
      strokeColor,
      strokeWidth: '2',
    },
  }) as { id: string };
  
  return result.id;
}

/**
 * Parse markdown file and extract structure
 */
function parseMarkdown(content: string): ParsedMarkdown {
  const lines = content.split('\n');
  const sections: MarkdownSection[] = [];
  const codeBlocks: { language: string; content: string; lineStart: number }[] = [];
  const tables: { headers: string[]; rows: string[][] }[] = [];
  
  let title = '';
  let currentSection: MarkdownSection | null = null;
  let inCodeBlock = false;
  let currentCodeBlock = { language: '', content: '', lineStart: 0 };
  let inTable = false;
  let currentTable: { headers: string[]; rows: string[][] } = { headers: [], rows: [] };

  lines.forEach((line, idx) => {
    // Handle code blocks
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        codeBlocks.push({ ...currentCodeBlock });
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
        currentCodeBlock = {
          language: line.slice(3).trim(),
          content: '',
          lineStart: idx,
        };
      }
      return;
    }

    if (inCodeBlock) {
      currentCodeBlock.content += line + '\n';
      return;
    }

    // Handle tables
    if (line.startsWith('|') && line.endsWith('|')) {
      if (!inTable) {
        inTable = true;
        currentTable = { headers: [], rows: [] };
        currentTable.headers = line.split('|').filter(c => c.trim()).map(c => c.trim());
      } else if (line.includes('---')) {
        // Header separator, skip
      } else {
        currentTable.rows.push(line.split('|').filter(c => c.trim()).map(c => c.trim()));
      }
      return;
    } else if (inTable) {
      tables.push({ ...currentTable });
      inTable = false;
    }

    // Handle headers
    if (line.startsWith('# ') && !title) {
      title = line.slice(2).trim();
      return;
    }

    if (line.startsWith('## ')) {
      if (currentSection) {
        sections.push(currentSection);
      }
      currentSection = {
        level: 2,
        title: line.slice(3).trim(),
        content: '',
        subsections: [],
      };
      return;
    }

    if (line.startsWith('### ') && currentSection) {
      currentSection.subsections.push({
        level: 3,
        title: line.slice(4).trim(),
        content: '',
        subsections: [],
      });
      return;
    }

    // Add content to current section
    if (currentSection && line.trim()) {
      currentSection.content += line + '\n';
    }
  });

  // Push last section
  if (currentSection) {
    sections.push(currentSection);
  }

  // Push last table if any
  if (inTable) {
    tables.push(currentTable);
  }

  return { title, sections, codeBlocks, tables };
}

/**
 * Extract wheel structure from Bicycle Wheel Doctrine markdown
 */
function extractWheelStructure(parsed: ParsedMarkdown): WheelStructure | null {
  // Look for hub definition
  const hubSection = parsed.sections.find(s => 
    s.title.toLowerCase().includes('hub') || 
    s.title.toLowerCase().includes('core')
  );

  if (!hubSection) return null;

  const hub: WheelHub = {
    name: hubSection.title,
    anchorFields: [],
  };

  // Extract spokes
  const spokes: WheelSpoke[] = [];
  const failureSpokes: WheelSpoke[] = [];

  parsed.sections.forEach(section => {
    if (section.title.toLowerCase().includes('spoke')) {
      const isFailure = section.title.toLowerCase().includes('failure');
      const spoke: WheelSpoke = {
        name: section.title,
        functions: section.subsections.map(s => s.title),
        feedsHub: true,
      };
      
      if (isFailure) {
        failureSpokes.push(spoke);
      } else {
        spokes.push(spoke);
      }
    }
  });

  return {
    hub,
    spokes,
    failureSpokes,
    subWheels: [],
  };
}

/**
 * Create a wheel visualization on Miro
 */
async function createWheelVisualization(
  config: MiroApiConfig,
  wheel: WheelStructure,
  centerX: number,
  centerY: number,
  radius: number = 400
): Promise<void> {
  // Create central hub
  const hubId = await createShape(
    config,
    wheel.hub.name,
    { x: centerX, y: centerY },
    'circle',
    COLORS.hub,
    200,
    200
  );

  // Create spokes in a radial pattern
  const totalSpokes = wheel.spokes.length + wheel.failureSpokes.length;
  const angleStep = (2 * Math.PI) / totalSpokes;

  // Regular spokes
  for (let i = 0; i < wheel.spokes.length; i++) {
    const angle = i * angleStep;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    const spokeId = await createShape(
      config,
      wheel.spokes[i].name,
      { x, y },
      'rectangle',
      COLORS.spoke,
      180,
      80
    );

    // Connect spoke to hub
    await createConnector(config, hubId, spokeId, COLORS.spoke);
  }

  // Failure spokes (smaller, different color)
  for (let i = 0; i < wheel.failureSpokes.length; i++) {
    const angle = (wheel.spokes.length + i) * angleStep;
    const x = centerX + (radius * 0.7) * Math.cos(angle);
    const y = centerY + (radius * 0.7) * Math.sin(angle);

    const failureId = await createShape(
      config,
      wheel.failureSpokes[i].name,
      { x, y },
      'diamond',
      COLORS.failure,
      150,
      70
    );

    // Connect failure spoke to hub
    await createConnector(config, hubId, failureId, COLORS.failure);
  }
}

/**
 * Upload a markdown file to Miro as structured content
 */
export async function uploadMarkdownToMiro(
  filePath: string,
  boardId?: string,
  token?: string
): Promise<{ itemCount: number; frameId?: string }> {
  const miroToken = token || process.env.MIRO_TOKEN;
  const miroBoardId = boardId || process.env.MIRO_BOARD_ID;

  if (!miroToken || !miroBoardId) {
    throw new Error('MIRO_TOKEN and MIRO_BOARD_ID are required');
  }

  const config: MiroApiConfig = { token: miroToken, boardId: miroBoardId };

  // Read and parse file
  const content = fs.readFileSync(filePath, 'utf-8');
  const parsed = parseMarkdown(content);
  const fileName = path.basename(filePath);

  console.log(`📄 Parsing: ${fileName}`);
  console.log(`   Title: ${parsed.title}`);
  console.log(`   Sections: ${parsed.sections.length}`);
  console.log(`   Code blocks: ${parsed.codeBlocks.length}`);
  console.log(`   Tables: ${parsed.tables.length}`);

  let itemCount = 0;

  // Create a frame for the document
  const frameWidth = 1600;
  const frameHeight = Math.max(1200, parsed.sections.length * 300);
  const frameId = await createFrame(
    config,
    `📄 ${parsed.title || fileName}`,
    { x: 0, y: 0 },
    frameWidth,
    frameHeight
  );
  itemCount++;

  // Check if this is a Bicycle Wheel Doctrine file
  const isWheelDoc = content.toLowerCase().includes('bicycle wheel') || 
                     content.toLowerCase().includes('hub-and-spoke');

  if (isWheelDoc) {
    console.log('   🎡 Detected Bicycle Wheel Doctrine format');
    const wheelStructure = extractWheelStructure(parsed);
    
    if (wheelStructure) {
      await createWheelVisualization(config, wheelStructure, 0, 0, 500);
      itemCount += wheelStructure.spokes.length + wheelStructure.failureSpokes.length + 1;
    }
  }

  // Create title
  await createShape(
    config,
    parsed.title || fileName,
    { x: 0, y: -frameHeight / 2 + 100 },
    'rectangle',
    COLORS.hub,
    400,
    80
  );
  itemCount++;

  // Create sections as sticky notes in a grid
  const cols = 3;
  const startX = -frameWidth / 2 + 200;
  const startY = -frameHeight / 2 + 300;
  const spacingX = 350;
  const spacingY = 250;

  for (let i = 0; i < parsed.sections.length; i++) {
    const section = parsed.sections[i];
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = startX + col * spacingX;
    const y = startY + row * spacingY;

    // Section title as shape
    await createShape(
      config,
      section.title,
      { x, y },
      'rectangle',
      COLORS.spoke,
      300,
      60
    );
    itemCount++;

    // Subsections as sticky notes
    for (let j = 0; j < Math.min(section.subsections.length, 3); j++) {
      const subY = y + 80 + j * 70;
      await createStickyNote(
        config,
        section.subsections[j].title,
        { x, y: subY },
        'yellow'
      );
      itemCount++;
    }
  }

  console.log(`✅ Created ${itemCount} items on Miro board`);

  return { itemCount, frameId };
}

// CLI entry point
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('Usage: npx tsx miro-uploader.ts <file-path> [board-id]');
    console.log('Example: npx tsx miro-uploader.ts ../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md');
    process.exit(1);
  }

  const filePath = args[0];
  const boardId = args[1];

  try {
    const result = await uploadMarkdownToMiro(filePath, boardId);
    console.log(`\n🎉 Successfully uploaded to Miro!`);
    console.log(`   Items created: ${result.itemCount}`);
  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

main();


