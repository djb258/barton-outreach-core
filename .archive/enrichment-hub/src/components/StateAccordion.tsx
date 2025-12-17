import { useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { EnrichmentTable } from "./EnrichmentTable";
import { useEnrichmentData } from "@/hooks/useEnrichmentData";
import { Loader2 } from "lucide-react";

interface StateAccordionProps {
  state: string;
  entity: "people" | "companies";
}

export const StateAccordion = ({ state, entity }: StateAccordionProps) => {
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const { data, isLoading, count } = useEnrichmentData(entity, state, page, pageSize);

  return (
    <Accordion type="single" collapsible className="border rounded-lg bg-card">
      <AccordionItem value={state} className="border-none">
        <AccordionTrigger className="px-6 py-4 hover:no-underline">
          <div className="flex items-center justify-between w-full pr-4">
            <span className="text-lg font-semibold">{state}</span>
            <span className="text-sm text-muted-foreground">
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                `${count || 0} unvalidated ${count === 1 ? "record" : "records"}`
              )}
            </span>
          </div>
        </AccordionTrigger>
        <AccordionContent className="px-6 pb-6">
          <EnrichmentTable
            entity={entity}
            state={state}
            data={data || []}
            isLoading={isLoading}
            page={page}
            pageSize={pageSize}
            totalCount={count || 0}
            onPageChange={setPage}
          />
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};
