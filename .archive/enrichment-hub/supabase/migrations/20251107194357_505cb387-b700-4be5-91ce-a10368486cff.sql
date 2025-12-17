-- Create monthly update staging tables
CREATE TABLE public.people_monthly_updates (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  unique_id uuid NOT NULL,
  field_changed text NOT NULL,
  old_value text,
  new_value text,
  source text NOT NULL,
  approved boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE public.company_monthly_updates (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  unique_id uuid NOT NULL,
  field_changed text NOT NULL,
  old_value text,
  new_value text,
  source text NOT NULL,
  approved boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE public.monthly_update_log (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  run_id uuid NOT NULL DEFAULT gen_random_uuid(),
  entity text NOT NULL,
  state text NOT NULL,
  tool text NOT NULL,
  batch_size integer NOT NULL,
  runtime_sec numeric,
  cost_usd numeric,
  records_checked integer DEFAULT 0,
  changes_found integer DEFAULT 0,
  promoted integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.people_monthly_updates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_monthly_updates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.monthly_update_log ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all operations for now)
CREATE POLICY "Allow all operations on people_monthly_updates"
  ON public.people_monthly_updates
  FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on company_monthly_updates"
  ON public.company_monthly_updates
  FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all operations on monthly_update_log"
  ON public.monthly_update_log
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Add triggers for updated_at
CREATE TRIGGER update_people_monthly_updates_updated_at
  BEFORE UPDATE ON public.people_monthly_updates
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_company_monthly_updates_updated_at
  BEFORE UPDATE ON public.company_monthly_updates
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();