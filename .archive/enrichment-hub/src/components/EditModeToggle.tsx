import { Button } from "@/components/ui/button";
import { Edit, EyeOff } from "lucide-react";
import { useEditMode } from "@/contexts/EditModeContext";
import { Badge } from "@/components/ui/badge";

export const EditModeToggle = () => {
  const { isEditMode, toggleEditMode } = useEditMode();

  return (
    <Button
      onClick={toggleEditMode}
      className="fixed bottom-6 right-6 z-50 shadow-lg gap-2"
      variant={isEditMode ? "default" : "outline"}
      size="lg"
    >
      {isEditMode ? (
        <>
          <EyeOff className="h-5 w-5" />
          Disable Edit Mode
          <Badge variant="secondary" className="ml-1">ON</Badge>
        </>
      ) : (
        <>
          <Edit className="h-5 w-5" />
          Enable Edit Mode
          <Badge variant="secondary" className="ml-1">OFF</Badge>
        </>
      )}
    </Button>
  );
};
