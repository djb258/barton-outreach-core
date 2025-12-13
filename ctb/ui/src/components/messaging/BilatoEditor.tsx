import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Save, X } from "lucide-react";
import { z } from "zod";
import { toast } from "sonner";

const templateSchema = z.object({
  title: z.string().trim().min(1, "Title is required").max(100, "Title too long"),
  subject: z.string().trim().min(1, "Subject is required").max(200, "Subject too long"),
  content: z.string().trim().min(1, "Content is required").max(5000, "Content too long"),
});

interface Template {
  id?: string;
  title: string;
  subject: string;
  content: string;
  status?: string;
}

interface BilatoEditorProps {
  template: Template | null;
  onSave: (template: Template) => void;
  onCancel: () => void;
}

export function BilatoEditor({ template, onSave, onCancel }: BilatoEditorProps) {
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [content, setContent] = useState("");
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    if (template) {
      setTitle(template.title);
      setSubject(template.subject);
      setContent(template.content);
    } else {
      setTitle("");
      setSubject("");
      setContent("");
    }
    setErrors({});
  }, [template]);

  const handleSave = () => {
    try {
      const validated = templateSchema.parse({ title, subject, content });
      
      onSave({
        ...template,
        ...validated,
      });
      
      setErrors({});
      toast.success("Template saved successfully");
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: { [key: string]: string } = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            newErrors[err.path[0] as string] = err.message;
          }
        });
        setErrors(newErrors);
        toast.error("Please fix validation errors");
      }
    }
  };

  const insertVariable = (variable: string) => {
    setContent(prev => prev + `{{${variable}}}`);
  };

  return (
    <Card className="p-4 rounded-xl shadow-md border-border/20">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-execution">
          {template?.id ? 'Edit Template' : 'New Template'}
        </h3>
        <Button variant="ghost" size="sm" onClick={onCancel}>
          <X className="w-4 h-4" />
        </Button>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="title" className="text-xs">Template Name</Label>
          <Input
            id="title"
            placeholder="e.g. Welcome Sequence Day 1"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={errors.title ? "border-destructive" : ""}
          />
          {errors.title && (
            <p className="text-xs text-destructive mt-1">{errors.title}</p>
          )}
        </div>

        <div>
          <Label htmlFor="subject" className="text-xs">Email Subject</Label>
          <Input
            id="subject"
            placeholder="Your subject line here"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={errors.subject ? "border-destructive" : ""}
          />
          {errors.subject && (
            <p className="text-xs text-destructive mt-1">{errors.subject}</p>
          )}
        </div>

        <div>
          <Label htmlFor="content" className="text-xs">Message Content</Label>
          <Textarea
            id="content"
            placeholder="Hi {{first_name}},&#10;&#10;Your personalized message here..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={10}
            className={`font-mono text-sm ${errors.content ? "border-destructive" : ""}`}
          />
          {errors.content && (
            <p className="text-xs text-destructive mt-1">{errors.content}</p>
          )}
        </div>

        <div>
          <Label className="text-xs mb-2 block">Quick Variables</Label>
          <div className="flex flex-wrap gap-2">
            {['first_name', 'last_name', 'company', 'title', 'industry'].map((variable) => (
              <Button
                key={variable}
                variant="outline"
                size="sm"
                onClick={() => insertVariable(variable)}
                type="button"
              >
                {`{{${variable}}}`}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            Save Template
          </Button>
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>
    </Card>
  );
}
