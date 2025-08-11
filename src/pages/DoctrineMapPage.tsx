import { ProcessFlowDiagram } from '@/components/template/ProcessFlowDiagram';
import { outreachConfig } from '@/lib/template/application-config';

export default function DoctrineMapPage() {
  return <ProcessFlowDiagram config={outreachConfig} />;
}