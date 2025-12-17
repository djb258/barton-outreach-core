import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

// Claude Agent Insert Here: Add new tool webhook URLs below
const WEBHOOK_URLS = {
  salesnav: import.meta.env.VITE_N8N_WEBHOOK_SALESNAV || "",
  apollo: import.meta.env.VITE_N8N_WEBHOOK_APOLLO || "",
  clay: import.meta.env.VITE_N8N_WEBHOOK_CLAY || "",
  firecrawl: import.meta.env.VITE_N8N_WEBHOOK_FIRECRAWL || "",
  promote: import.meta.env.VITE_N8N_WEBHOOK_PROMOTE || "",
};

export const useBatchActions = (entity: "people" | "companies", state: string) => {
  const [isRunning, setIsRunning] = useState(false);
  const queryClient = useQueryClient();
  const tableName =
    entity === "people" ? "people_needs_enrichment" : "company_needs_enrichment";

  const exportBatch = (data: any[]) => {
    const csvContent = [
      Object.keys(data[0]).join(","),
      ...data.map((row) =>
        Object.values(row)
          .map((val) => `"${val}"`)
          .join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${entity}-${state}-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    toast.success("Batch exported successfully");
  };

  const runWithTool = async (tool: string, batchIds: string[]) => {
    const webhookUrl = WEBHOOK_URLS[tool as keyof typeof WEBHOOK_URLS];

    if (!webhookUrl) {
      toast.error(`Webhook URL for ${tool} not configured`);
      return;
    }

    // Enforce max batch size of 50
    if (batchIds.length > 50) {
      toast.error("Maximum batch size is 50 records");
      return;
    }

    setIsRunning(true);
    toast.info(`Starting enrichment run with ${tool}...`);

    const startTime = new Date().toISOString();

    try {
      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          entity,
          state,
          tool,
          batch_ids: batchIds,
        }),
      });

      if (!response.ok) throw new Error("Webhook call failed");

      const result = await response.json();
      const endTime = new Date().toISOString();

      // Enhanced logging with timing and status
      await supabase.from("enrichment_log").insert({
        entity,
        state,
        tool,
        total_count: batchIds.length,
        success_count: result.success_count || batchIds.length,
        cost: result.cost_usd || null,
      });

      // Optional: Log to n8n_call_log for debugging
      await supabase.from("n8n_call_log").insert({
        webhook_url: webhookUrl,
        payload: { entity, state, tool, batch_ids: batchIds },
        response: result,
        status: "success",
        execution_time_ms: new Date(endTime).getTime() - new Date(startTime).getTime(),
      });

      toast.success(`Successfully triggered ${tool} for ${batchIds.length} records`);
      queryClient.invalidateQueries({ queryKey: [tableName] });
    } catch (error) {
      const endTime = new Date().toISOString();
      
      // Log failed attempt
      await supabase.from("n8n_call_log").insert({
        webhook_url: webhookUrl,
        payload: { entity, state, tool, batch_ids: batchIds },
        status: "error",
        error_message: error instanceof Error ? error.message : "Unknown error",
        execution_time_ms: new Date(endTime).getTime() - new Date(startTime).getTime(),
      });

      toast.error(`Failed to run with ${tool}`);
      console.error(error);
    } finally {
      setIsRunning(false);
    }
  };

  const promoteValidated = async (batchIds: string[]) => {
    const webhookUrl = WEBHOOK_URLS.promote;

    if (!webhookUrl) {
      toast.error("Promote webhook URL not configured");
      return;
    }

    setIsRunning(true);
    toast.info(`Promoting ${batchIds.length} validated records...`);

    try {
      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          entity,
          state,
          batch_ids: batchIds,
        }),
      });

      if (!response.ok) throw new Error("Webhook call failed");

      // Mark as validated
      await supabase
        .from(tableName)
        .update({ validated: true })
        .in("unique_id", batchIds);

      toast.success(`Successfully promoted ${batchIds.length} records`);
      queryClient.invalidateQueries({ queryKey: [tableName] });
    } catch (error) {
      toast.error("Failed to promote records");
      console.error(error);
    } finally {
      setIsRunning(false);
    }
  };

  return {
    exportBatch,
    runWithTool,
    promoteValidated,
    isRunning,
  };
};
