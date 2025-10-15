import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Campaign {
  id: string;
  name: string;
  status: string;
  sent: number;
  opened?: number;
  replied?: number;
  created_at: string;
}

interface CampaignTableProps {
  campaigns: Campaign[];
  title: string;
}

export function CampaignTable({ campaigns, title }: CampaignTableProps) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'running':
        return 'bg-status-online';
      case 'paused':
        return 'bg-status-warning';
      case 'completed':
        return 'bg-doctrine';
      case 'failed':
        return 'bg-status-error';
      default:
        return 'bg-muted';
    }
  };

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-execution">{title}</h3>
        <Badge variant="outline">{campaigns.length} Campaigns</Badge>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Campaign</TableHead>
              <TableHead className="text-xs">Status</TableHead>
              <TableHead className="text-xs text-right">Sent</TableHead>
              {campaigns.some(c => c.opened !== undefined) && (
                <TableHead className="text-xs text-right">Opened</TableHead>
              )}
              {campaigns.some(c => c.replied !== undefined) && (
                <TableHead className="text-xs text-right">Replied</TableHead>
              )}
              <TableHead className="text-xs">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {campaigns.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground text-sm">
                  No campaigns found
                </TableCell>
              </TableRow>
            ) : (
              campaigns.slice(0, 10).map((campaign) => (
                <TableRow key={campaign.id} className="hover:bg-muted/50">
                  <TableCell className="text-xs font-medium">{campaign.name}</TableCell>
                  <TableCell className="text-xs">
                    <Badge variant="secondary" className={getStatusColor(campaign.status)}>
                      {campaign.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-right">{campaign.sent}</TableCell>
                  {campaigns.some(c => c.opened !== undefined) && (
                    <TableCell className="text-xs text-right">{campaign.opened || 0}</TableCell>
                  )}
                  {campaigns.some(c => c.replied !== undefined) && (
                    <TableCell className="text-xs text-right">{campaign.replied || 0}</TableCell>
                  )}
                  <TableCell className="text-xs">
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
