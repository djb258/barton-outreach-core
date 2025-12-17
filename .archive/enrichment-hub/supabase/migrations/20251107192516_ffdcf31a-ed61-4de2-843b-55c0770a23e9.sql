-- Enable RLS on all tables
ALTER TABLE public.people_needs_enrichment ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_needs_enrichment ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enrichment_log ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for people_needs_enrichment (admin tool - allow all operations)
CREATE POLICY "Allow all operations on people_needs_enrichment"
ON public.people_needs_enrichment
FOR ALL
USING (true)
WITH CHECK (true);

-- Create permissive policies for company_needs_enrichment
CREATE POLICY "Allow all operations on company_needs_enrichment"
ON public.company_needs_enrichment
FOR ALL
USING (true)
WITH CHECK (true);

-- Create permissive policies for enrichment_log
CREATE POLICY "Allow all operations on enrichment_log"
ON public.enrichment_log
FOR ALL
USING (true)
WITH CHECK (true);

-- Update function search path for security
ALTER FUNCTION public.update_updated_at_column() SET search_path = public;