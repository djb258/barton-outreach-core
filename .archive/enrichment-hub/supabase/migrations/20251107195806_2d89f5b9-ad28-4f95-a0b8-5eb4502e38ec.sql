-- Fix search_path security issue for log_edit_trigger function
DROP FUNCTION IF EXISTS public.log_edit_trigger();

CREATE OR REPLACE FUNCTION public.log_edit_trigger()
RETURNS TRIGGER AS $$
BEGIN
  -- This can be extended to automatically log changes if needed
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;