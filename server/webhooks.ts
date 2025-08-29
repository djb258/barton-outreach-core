// REPLACE FILE: server/webhooks.ts
import type { Request, Response, Router } from 'express';
import express from 'express';
import { bootOrchestration, getMasterOrchestrator } from './start-orchestrators';

export function buildWebhookRouter(): Router {
  const r = express.Router();

  r.use(async (_req, _res, next) => { try { await bootOrchestration(); next(); } catch (e) { next(e); } });

  // === External service webhooks ===
  r.post('/apify', async (req: Request, res: Response) => {
    try {
      const { event, payload } = req.body || {};
      const master = getMasterOrchestrator();
      
      // Route to lead branch orchestrator via sendMessage
      await master.sendMessage({
        id: `apify-${Date.now()}`,
        from_branch: 'apify',
        to_branch: 'lead',
        message_type: event ?? 'scrape_done',
        payload: payload ?? {},
        timestamp: new Date(),
        requires_response: false
      });
      
      console.log(`📨 Apify webhook processed: ${event}`);
      res.status(200).json({ ok: true });
    } catch (error) {
      console.error('❌ Apify webhook failed:', error);
      res.status(500).json({ error: 'Webhook processing failed' });
    }
  });

  r.post('/delivery', async (req: Request, res: Response) => {
    try {
      const { event, payload } = req.body || {};
      const master = getMasterOrchestrator();
      
      // Route to delivery branch orchestrator
      await master.sendMessage({
        id: `delivery-${Date.now()}`,
        from_branch: 'delivery_provider',
        to_branch: 'delivery',
        message_type: event ?? 'send_result',
        payload: payload ?? {},
        timestamp: new Date(),
        requires_response: false
      });
      
      console.log(`📨 Delivery webhook processed: ${event}`);
      res.status(200).json({ ok: true });
    } catch (error) {
      console.error('❌ Delivery webhook failed:', error);
      res.status(500).json({ error: 'Webhook processing failed' });
    }
  });

  r.post('/validator', async (req: Request, res: Response) => {
    try {
      const { event, payload } = req.body || {};
      const master = getMasterOrchestrator();
      
      // Route to lead branch for validation processing
      await master.sendMessage({
        id: `validator-${Date.now()}`,
        from_branch: 'validator',
        to_branch: 'lead',
        message_type: event ?? 'validate_result',
        payload: payload ?? {},
        timestamp: new Date(),
        requires_response: false
      });
      
      console.log(`📨 Validator webhook processed: ${event}`);
      res.status(200).json({ ok: true });
    } catch (error) {
      console.error('❌ Validator webhook failed:', error);
      res.status(500).json({ error: 'Webhook processing failed' });
    }
  });

  // === Programmatic triggers (maps to your curl examples) ===
  r.post('/trigger/:type', async (req: Request, res: Response) => {
    try {
      const type = String(req.params.type || 'lead_only'); // 'lead_only' | 'full_pipeline' | 'messaging_only' | 'delivery_only'
      const payload = req.body || {};
      const master = getMasterOrchestrator();
      
      // Validate workflow type
      const validWorkflows = ['full_pipeline', 'lead_only', 'messaging_only', 'custom'];
      if (!validWorkflows.includes(type)) {
        return res.status(400).json({ error: `Invalid workflow: ${type}` });
      }
      
      // Execute workflow asynchronously
      const workflowPromise = master.executeWorkflow(type as any, payload);
      
      // Return immediately, don't wait for completion
      res.status(202).json({ 
        ok: true, 
        triggered: type,
        workflow_id: `${type}-${Date.now()}`,
        started_at: new Date().toISOString()
      });
      
      // Log completion/failure
      workflowPromise
        .then(() => console.log(`✅ Triggered workflow '${type}' completed`))
        .catch(error => console.error(`❌ Triggered workflow '${type}' failed:`, error));
        
    } catch (error) {
      console.error('❌ Workflow trigger failed:', error);
      res.status(500).json({ error: 'Workflow trigger failed' });
    }
  });

  // === Status/health ===
  r.get('/status', async (_req: Request, res: Response) => {
    try {
      const master = getMasterOrchestrator();
      const status = master.getProjectStatus?.() ?? { overall_status: 'unknown' };
      
      res.status(200).json({
        system: 'barton-outreach-core',
        ...status,
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
      });
    } catch (error) {
      console.error('❌ Status check failed:', error);
      res.status(500).json({ error: 'Status check failed' });
    }
  });

  r.get('/health', (_req, res) => res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() }));

  // Error handling
  r.use((error: any, _req: Request, res: Response, _next: any) => {
    console.error('❌ Webhook router error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      timestamp: new Date().toISOString()
    });
  });

  return r;
}