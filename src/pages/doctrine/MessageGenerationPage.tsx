import { BranchTemplate } from '@/components/template/BranchTemplate';
import { outreachConfig } from '@/lib/template/application-config';

export default function MessageGenerationPage() {
  const branch = outreachConfig.branches.find(b => b.id === '02')!;
  return <BranchTemplate config={outreachConfig} branch={branch} />;
}