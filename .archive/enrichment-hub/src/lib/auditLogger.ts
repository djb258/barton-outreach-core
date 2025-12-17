import { supabase } from "@/integrations/supabase/client";

interface AuditLogEntry {
  tableName: string;
  recordId: string;
  fieldName: string;
  oldValue: any;
  newValue: any;
  userId?: string;
}

export const logEdit = async ({
  tableName,
  recordId,
  fieldName,
  oldValue,
  newValue,
  userId,
}: AuditLogEntry): Promise<void> => {
  try {
    const { error } = await supabase.from("edit_audit_log").insert({
      table_name: tableName,
      record_id: recordId,
      field_name: fieldName,
      old_value: oldValue?.toString() || null,
      new_value: newValue?.toString() || null,
      user_id: userId || null,
    });

    if (error) {
      console.error("Failed to log edit:", error);
    }
  } catch (err) {
    console.error("Error logging edit:", err);
  }
};
