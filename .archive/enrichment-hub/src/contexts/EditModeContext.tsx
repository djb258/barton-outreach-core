import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface EditModeContextType {
  isEditMode: boolean;
  toggleEditMode: () => void;
}

const EditModeContext = createContext<EditModeContextType | undefined>(undefined);

export const useEditMode = () => {
  const context = useContext(EditModeContext);
  if (!context) {
    throw new Error("useEditMode must be used within EditModeProvider");
  }
  return context;
};

export const EditModeProvider = ({ children }: { children: ReactNode }) => {
  const [isEditMode, setIsEditMode] = useState(() => {
    const stored = localStorage.getItem("editMode");
    return stored === "true";
  });

  useEffect(() => {
    localStorage.setItem("editMode", String(isEditMode));
  }, [isEditMode]);

  const toggleEditMode = () => setIsEditMode((prev) => !prev);

  return (
    <EditModeContext.Provider value={{ isEditMode, toggleEditMode }}>
      {children}
    </EditModeContext.Provider>
  );
};
