import { BranchTemplate } from '@/components/template/BranchTemplate';
import { outreachConfig } from '@/lib/template/application-config';

export default function LeadIntakePage() {
  const branch = outreachConfig.branches.find(b => b.id === '01')!;
  return <BranchTemplate config={outreachConfig} branch={branch} />;
}