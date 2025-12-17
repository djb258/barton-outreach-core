import { useEditMode } from "@/contexts/EditModeContext";
import { ComponentId } from "@/components/ComponentId";

export const useComponentId = () => {
  const { isEditMode } = useEditMode();
  
  return {
    isEditMode,
    ComponentId,
  };
};
