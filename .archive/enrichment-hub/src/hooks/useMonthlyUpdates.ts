import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { triggerN8NWebhook } from "@/lib/n8nClient";

interface MonthlyUpdate {
  id: string;
  unique_id: string;
  field_changed: string;
  old_value: string | null;
  new_value: string | null;
  source: string;
  approved: boolean;
  created_at: string;
  updated_at: string;
}

export const useMonthlyUpdates = (entity: "people" | "companies") => {
  const [updates, setUpdates] = useState<MonthlyUpdate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const tableName =
    entity === "people" ? "people_monthly_updates" : "company_monthly_updates";

  const fetchUpdates = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from(tableName)
        .select("*")
        .order("created_at", { ascending: false });

      if (error) throw error;
      setUpdates(data || []);
    } catch (error) {
      console.error("Error fetching monthly updates:", error);
      toast.error("Failed to fetch updates");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUpdates();

    // Subscribe to realtime updates
    const channel = supabase
      .channel(`${tableName}_changes`)
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: tableName,
        },
        () => {
          fetchUpdates();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [tableName]);

  const runUpdateCheck = async (
    state: string,
    tool: string,
    batchSize: number
  ) => {
    const webhookUrl = import.meta.env.VITE_N8N_WEBHOOK_RUNMONTHLY || "";

    if (!webhookUrl) {
      toast.error("Monthly update webhook URL not configured");
      return;
    }

    setIsRunning(true);
    toast.info(`Starting monthly update check with ${tool}...`);

    try {
      await triggerN8NWebhook(webhookUrl, {
        entity,
        state,
        tool,
        batch_size: batchSize,
      });

      // Log the run
      await supabase.from("monthly_update_log").insert({
        entity,
        state,
        tool,
        batch_size: batchSize,
      });

      toast.success("Update check started successfully");
      await fetchUpdates();
    } catch (error) {
      toast.error("Failed to start update check");
      console.error(error);
    } finally {
      setIsRunning(false);
    }
  };

  const approveUpdate = async (id: string) => {
    try {
      const { error } = await supabase
        .from(tableName)
        .update({ approved: true })
        .eq("id", id);

      if (error) throw error;
      toast.success("Update approved");
      await fetchUpdates();
    } catch (error) {
      toast.error("Failed to approve update");
      console.error(error);
    }
  };

  const approveAll = async () => {
    try {
      const { error } = await supabase
        .from(tableName)
        .update({ approved: true })
        .eq("approved", false);

      if (error) throw error;
      toast.success("All updates approved");
      await fetchUpdates();
    } catch (error) {
      toast.error("Failed to approve all updates");
      console.error(error);
    }
  };

  const promoteUpdates = async (updateIds: string[]) => {
    const webhookUrl = import.meta.env.VITE_N8N_WEBHOOK_PROMOTEUPDATES || "";

    if (!webhookUrl) {
      toast.error("Promote updates webhook URL not configured");
      return;
    }

    setIsRunning(true);
    toast.info(`Promoting ${updateIds.length} updates to Neon...`);

    try {
      await triggerN8NWebhook(webhookUrl, {
        entity,
        update_ids: updateIds,
      });

      toast.success(`Successfully promoted ${updateIds.length} updates`);
      await fetchUpdates();
    } catch (error) {
      toast.error("Failed to promote updates");
      console.error(error);
    } finally {
      setIsRunning(false);
    }
  };

  return {
    updates,
    isLoading,
    isRunning,
    runUpdateCheck,
    approveUpdate,
    approveAll,
    promoteUpdates,
  };
};
