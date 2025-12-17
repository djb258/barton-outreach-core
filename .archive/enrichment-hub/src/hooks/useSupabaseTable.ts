import { useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { logEdit } from "@/lib/auditLogger";

interface UseSupabaseTableProps {
  tableName: string;
  pageSize?: number;
  orderBy?: string;
  orderAscending?: boolean;
}

export const useSupabaseTable = ({
  tableName,
  pageSize = 500,
  orderBy = "created_at",
  orderAscending = false,
}: UseSupabaseTableProps) => {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const { toast } = useToast();

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const from = page * pageSize;
      const to = from + pageSize - 1;

      const { data: tableData, error, count } = await supabase
        .from(tableName as any)
        .select("*", { count: "exact" })
        .order(orderBy, { ascending: orderAscending })
        .range(from, to);

      if (error) throw error;

      setData(tableData || []);
      setTotalCount(count || 0);
    } catch (error: any) {
      toast({
        title: "Error fetching data",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Set up realtime subscription
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
          fetchData();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [tableName, page, pageSize, orderBy, orderAscending]);

  const updateCell = async (
    recordId: string,
    fieldName: string,
    newValue: any,
    oldValue: any
  ) => {
    try {
      const { error } = await supabase
        .from(tableName as any)
        .update({ [fieldName]: newValue })
        .eq("id", recordId);

      if (error) throw error;

      // Log the edit
      await logEdit({
        tableName,
        recordId,
        fieldName,
        oldValue,
        newValue,
      });

      toast({
        title: "Saved",
        description: `Updated ${fieldName}`,
      });

      fetchData();
    } catch (error: any) {
      toast({
        title: "Error saving",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  return {
    data,
    isLoading,
    page,
    setPage,
    totalCount,
    pageSize,
    updateCell,
    refresh: fetchData,
  };
};
