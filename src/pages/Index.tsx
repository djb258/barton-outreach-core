import { BartonTemplate } from '@/components/template/BartonTemplate';
import { outreachConfig } from '@/lib/template/application-config';

const Index = () => {
  console.log('Index component rendering...', outreachConfig);
  return <BartonTemplate config={outreachConfig} />;
};

export default Index;
