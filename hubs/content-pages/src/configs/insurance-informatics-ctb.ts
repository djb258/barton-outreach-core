import type { ContentConfig } from '../types';

// Insurance Informatics — CTB (Content Tree Backbone)
// Route: /insurance-informatics-ctb
//
// Source: fleet/content/INSURANCE-INFORMATICS-CTB.md
// The full architecture of how insurance informatics works, mapped by
// altitude (50K discipline → 5K execution). Source of truth for every
// IR content artifact: Duck video, E-01 to E-05 explainers, emails,
// landing pages, vendor briefings, sales scripts.
//
// No video on this page yet — backbone is a readable architecture doc.
// When a hero/walkthrough video is produced, populate the streamId.
export const contentInsuranceInformaticsCTB: ContentConfig = {
  brand: 'svg',
  title: 'Insurance Informatics — CTB',
  subtitle: 'The Architecture — Every Altitude, From Discipline to Execution',
  description:
    'The full content tree backbone for Insurance Informatics. 50K: the named discipline (Insurance + IT). 40K: two sides — Fixed (Dave aggregates) + Variable (TPA aggregates). 30K: 10+ PEPM vendors one side, TPA+PBM the other. 20K: 90/15 autopilot + 10/85 active management. 10K: triggers, waterfall, service model. Every piece of content in the library slots onto this tree.',

  video: {
    streamId: 'STREAM_ID_PENDING',
    title: 'Insurance Informatics — CTB Walkthrough (pending recording)',
  },
};
