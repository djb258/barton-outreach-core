import { BranchTemplate } from '@/components/template/BranchTemplate';
import { outreachConfig } from '@/lib/template/application-config';

export default function CampaignExecutionPage() {
  const branch = outreachConfig.branches.find(b => b.id === '03')!;
  return <BranchTemplate config={outreachConfig} branch={branch} />;
}