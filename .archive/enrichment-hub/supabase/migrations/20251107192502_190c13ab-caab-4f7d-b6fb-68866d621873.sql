-- Create people_needs_enrichment table
CREATE TABLE IF NOT EXISTS public.people_needs_enrichment (
  unique_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT,
  last_name TEXT,
  company_name TEXT,
  email TEXT,
  linkedin_url TEXT,
  title TEXT,
  state TEXT NOT NULL,
  validation_source TEXT,
  validated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create company_needs_enrichment table
CREATE TABLE IF NOT EXISTS public.company_needs_enrichment (
  unique_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT,
  website TEXT,
  linkedin_url TEXT,
  industry TEXT,
  hq_city TEXT,
  state TEXT NOT NULL,
  validation_source TEXT,
  validated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create enrichment_log table for cost tracking
CREATE TABLE IF NOT EXISTS public.enrichment_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity TEXT NOT NULL, -- 'people' or 'companies'
  state TEXT NOT NULL,
  tool TEXT NOT NULL,
  cost DECIMAL(10, 2),
  success_count INTEGER DEFAULT 0,
  total_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable realtime for people_needs_enrichment
ALTER TABLE public.people_needs_enrichment REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE public.people_needs_enrichment;

-- Enable realtime for company_needs_enrichment
ALTER TABLE public.company_needs_enrichment REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE public.company_needs_enrichment;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_people_state_validated ON public.people_needs_enrichment(state, validated);
CREATE INDEX IF NOT EXISTS idx_company_state_validated ON public.company_needs_enrichment(state, validated);
CREATE INDEX IF NOT EXISTS idx_people_updated_at ON public.people_needs_enrichment(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_company_updated_at ON public.company_needs_enrichment(updated_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_people_updated_at
  BEFORE UPDATE ON public.people_needs_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_company_updated_at
  BEFORE UPDATE ON public.company_needs_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();