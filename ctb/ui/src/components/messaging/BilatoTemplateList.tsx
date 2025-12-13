import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit2, Eye, Send } from "lucide-react";

interface Template {
  id: string;
  title: string;
  subject: string;
  status: 'active' | 'draft' | 'archived';
  content: string;
}

interface BilatoTemplateListProps {
  templates: Template[];
  onEdit: (template: Template) => void;
  onPreview: (template: Template) => void;
  onSendTest: (templateId: string) => void;
}

export function BilatoTemplateList({ 
  templates, 
  onEdit, 
  onPreview, 
  onSendTest 
}: BilatoTemplateListProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-status-online';
      case 'draft': return 'bg-status-warning';
      case 'archived': return 'bg-status-offline';
      default: return 'bg-muted';
    }
  };

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-execution">Template Library</h3>
        <Badge variant="outline">{templates.length} Templates</Badge>
      </div>

      <div className="space-y-2">
        {templates.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">
            No templates found. Create your first template.
          </div>
        ) : (
          templates.map((template) => (
            <div
              key={template.id}
              className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-sm font-medium truncate">{template.title}</h4>
                  <Badge 
                    variant="secondary" 
                    className={`${getStatusColor(template.status)} text-xs`}
                  >
                    {template.status}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground truncate">{template.subject}</p>
              </div>

              <div className="flex gap-1 ml-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onEdit(template)}
                  title="Edit"
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onPreview(template)}
                  title="Preview"
                >
                  <Eye className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onSendTest(template.id)}
                  title="Send Test"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
