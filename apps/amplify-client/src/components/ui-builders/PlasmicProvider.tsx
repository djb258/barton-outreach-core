import React from 'react';
import { PlasmicRootProvider } from '@plasmicapp/react-web';
import { PLASMIC } from '../../lib/plasmic-init';

interface PlasmicProviderProps {
  children: React.ReactNode;
}

export const PlasmicProvider: React.FC<PlasmicProviderProps> = ({ children }) => {
  return (
    <PlasmicRootProvider loader={PLASMIC} prefetchedData={undefined}>
      {children}
    </PlasmicRootProvider>
  );
};

// Plasmic page component wrapper
export const PlasmicPage: React.FC<{ 
  component: string; 
  componentProps?: Record<string, any> 
}> = ({ component, componentProps = {} }) => {
  const [PlasmicComponent, setPlasmicComponent] = React.useState<React.ComponentType | null>(null);

  React.useEffect(() => {
    const loadComponent = async () => {
      try {
        const { PlasmicComponent: LoadedComponent } = await PLASMIC.maybeFetchComponentData(component);
        setPlasmicComponent(() => LoadedComponent);
      } catch (error) {
        console.error(`Failed to load Plasmic component: ${component}`, error);
      }
    };

    loadComponent();
  }, [component]);

  if (!PlasmicComponent) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="text-sm text-gray-500">Loading Plasmic component...</div>
      </div>
    );
  }

  return <PlasmicComponent {...componentProps} />;
};