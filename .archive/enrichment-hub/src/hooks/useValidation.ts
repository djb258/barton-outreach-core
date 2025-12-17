import { useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

export const useValidation = (entity: "people" | "companies") => {
  const queryClient = useQueryClient();
  const tableName =
    entity === "people" ? "people_needs_enrichment" : "company_needs_enrichment";

  const toggleValidation = useMutation({
    mutationFn: async ({
      uniqueId,
      currentValue,
    }: {
      uniqueId: string;
      currentValue: boolean;
    }) => {
      const { error } = await supabase
        .from(tableName)
        .update({ validated: !currentValue })
        .eq("unique_id", uniqueId);

      if (error) throw error;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [tableName] });
      toast.success(
        variables.currentValue
          ? "Record marked as unvalidated"
          : "Record marked as validated"
      );
    },
    onError: () => {
      toast.error("Failed to update validation status");
    },
  });

  return {
    toggleValidation: (uniqueId: string, currentValue: boolean) =>
      toggleValidation.mutate({ uniqueId, currentValue }),
  };
};
