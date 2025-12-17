-- Create edit_audit_log table for tracking all edits
CREATE TABLE IF NOT EXISTS public.edit_audit_log (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID,
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.edit_audit_log ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all authenticated users to read audit logs
CREATE POLICY "Users can view all audit logs"
  ON public.edit_audit_log
  FOR SELECT
  USING (true);

-- Create policy to allow all authenticated users to insert audit logs
CREATE POLICY "Users can insert audit logs"
  ON public.edit_audit_log
  FOR INSERT
  WITH CHECK (true);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_edit_audit_log_table_record 
  ON public.edit_audit_log(table_name, record_id);

CREATE INDEX IF NOT EXISTS idx_edit_audit_log_created_at 
  ON public.edit_audit_log(created_at DESC);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION public.log_edit_trigger()
RETURNS TRIGGER AS $$
BEGIN
  -- This can be extended to automatically log changes if needed
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;