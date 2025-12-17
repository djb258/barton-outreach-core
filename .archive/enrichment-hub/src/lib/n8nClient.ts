import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";

// Claude Agent Insert Here: Extend N8NWebhookPayload interface for new payload structures
interface N8NWebhookPayload {
  entity?: string;
  state?: string;
  tool?: string;
  batch_ids?: string[];
  batch_size?: number;
  [key: string]: any;
}

// Claude Agent Insert Here: Add new webhook utility functions below
export async function triggerN8NWebhook(
  webhookUrl: string,
  payload: N8NWebhookPayload,
  options?: { logToSupabase?: boolean }
): Promise<any> {
  if (!webhookUrl) {
    toast.error("Webhook URL not configured");
    throw new Error("Webhook URL not configured");
  }

  const startTime = Date.now();

  try {
    const response = await fetch(webhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`n8n call failed: ${response.statusText}`);
    }

    const result = await response.json();
    const executionTime = Date.now() - startTime;

    // Optional: Log successful webhook calls to Supabase for debugging
    if (options?.logToSupabase) {
      await supabase.from("n8n_call_log").insert({
        webhook_url: webhookUrl,
        payload,
        response: result,
        status: "success",
        execution_time_ms: executionTime,
      });
    }

    return result;
  } catch (error) {
    const executionTime = Date.now() - startTime;

    // Optional: Log failed webhook calls to Supabase for debugging
    if (options?.logToSupabase) {
      await supabase.from("n8n_call_log").insert({
        webhook_url: webhookUrl,
        payload,
        status: "error",
        error_message: error instanceof Error ? error.message : "Unknown error",
        execution_time_ms: executionTime,
      });
    }

    console.error("Error triggering n8n webhook:", error);
    throw error;
  }
}
