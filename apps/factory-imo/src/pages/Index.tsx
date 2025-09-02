import { BartonTemplate } from '@/components/template/BartonTemplate';
import { outreachConfig } from '@/lib/template/application-config';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Index = () => {
  console.log('Index component rendering...', outreachConfig);
  const navigate = useNavigate();
  
  return (
    <div>
      <div className="absolute top-4 right-4 z-10">
        <Button
          onClick={() => navigate('/imo-creator')}
          variant="outline"
          className="flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          IMO Creator
        </Button>
      </div>
      <BartonTemplate config={outreachConfig} />
    </div>
  );
};

export default Index;
