// Inline SVG diagrams — crawlable by Google, no image files needed

export const hubSpokeDiagram = `
<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Insurance Informatics hub-and-spoke architecture: Dave as the hub connecting all vendors to the client">
  <style>
    .hub { fill: #1a365d; } .spoke { fill: #2d3748; } .rim { fill: #2b6cb0; }
    .label { font-family: system-ui, sans-serif; fill: white; font-size: 12px; text-anchor: middle; }
    .label-dark { font-family: system-ui, sans-serif; fill: #1a202c; font-size: 11px; text-anchor: middle; }
    .connector { stroke: #4a5568; stroke-width: 2; fill: none; }
    .connector-bold { stroke: #2b6cb0; stroke-width: 3; fill: none; }
  </style>
  <!-- Hub -->
  <circle cx="300" cy="200" r="55" class="hub"/>
  <text x="300" y="195" class="label" font-weight="bold" font-size="14">DAVE</text>
  <text x="300" y="212" class="label" font-size="10">The Hub</text>
  <!-- Client (top) -->
  <rect x="240" y="10" width="120" height="45" rx="8" class="rim"/>
  <text x="300" y="37" class="label" font-weight="bold">CLIENT (CFO)</text>
  <line x1="300" y1="55" x2="300" y2="145" class="connector-bold"/>
  <!-- Spokes -->
  <rect x="30" y="100" width="100" height="35" rx="6" class="spoke"/>
  <text x="80" y="122" class="label">Stop Loss</text>
  <line x1="130" y1="117" x2="245" y2="185" class="connector"/>

  <rect x="30" y="165" width="100" height="35" rx="6" class="spoke"/>
  <text x="80" y="187" class="label">TPA</text>
  <line x1="130" y1="182" x2="245" y2="195" class="connector"/>

  <rect x="30" y="230" width="100" height="35" rx="6" class="spoke"/>
  <text x="80" y="252" class="label">PBM</text>
  <line x1="130" y1="247" x2="245" y2="210" class="connector"/>

  <rect x="30" y="295" width="100" height="35" rx="6" class="spoke"/>
  <text x="80" y="317" class="label">Dental</text>
  <line x1="130" y1="312" x2="260" y2="240" class="connector"/>

  <rect x="470" y="100" width="100" height="35" rx="6" class="spoke"/>
  <text x="520" y="122" class="label">Vision</text>
  <line x1="470" y1="117" x2="355" y2="185" class="connector"/>

  <rect x="470" y="165" width="100" height="35" rx="6" class="spoke"/>
  <text x="520" y="187" class="label">Life / STD</text>
  <line x1="470" y1="182" x2="355" y2="195" class="connector"/>

  <rect x="470" y="230" width="100" height="35" rx="6" class="spoke"/>
  <text x="520" y="252" class="label">EAP</text>
  <line x1="470" y1="247" x2="355" y2="210" class="connector"/>

  <rect x="470" y="295" width="100" height="35" rx="6" class="spoke"/>
  <text x="520" y="317" class="label">FSA / HRA</text>
  <line x1="470" y1="312" x2="340" y2="240" class="connector"/>

  <!-- Output arrows -->
  <text x="180" y="75" class="label-dark" font-size="10">ONE fixed bill</text>
  <text x="420" y="75" class="label-dark" font-size="10">ONE claims bill</text>
  <text x="300" y="385" class="label-dark" font-size="13" font-weight="bold">CFO sees two numbers. That's it.</text>
</svg>`;

export const ruleOfTwosDiagram = `
<svg viewBox="0 0 600 350" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rule of Twos: 90% of employees cause 15% of cost (autopilot), 10% cause 85% of cost (managed)">
  <style>
    .box-auto { fill: #276749; } .box-managed { fill: #9b2c2c; }
    .lbl { font-family: system-ui, sans-serif; fill: white; text-anchor: middle; }
    .lbl-dark { font-family: system-ui, sans-serif; fill: #1a202c; text-anchor: middle; }
  </style>
  <text x="300" y="30" class="lbl-dark" font-size="18" font-weight="bold">The Rule of Twos</text>
  <!-- 90/15 -->
  <rect x="30" y="55" width="250" height="120" rx="12" class="box-auto"/>
  <text x="155" y="90" class="lbl" font-size="36" font-weight="bold">90%</text>
  <text x="155" y="115" class="lbl" font-size="14">of employees</text>
  <text x="155" y="140" class="lbl" font-size="14">cause 15% of claims cost</text>
  <text x="155" y="160" class="lbl" font-size="11" opacity="0.8">AUTOPILOT</text>
  <!-- 10/85 -->
  <rect x="320" y="55" width="250" height="120" rx="12" class="box-managed"/>
  <text x="445" y="90" class="lbl" font-size="36" font-weight="bold">10%</text>
  <text x="445" y="115" class="lbl" font-size="14">of employees</text>
  <text x="445" y="140" class="lbl" font-size="14">cause 85% of claims cost</text>
  <text x="445" y="160" class="lbl" font-size="11" opacity="0.8">ACTIVELY MANAGED</text>
  <!-- Details -->
  <rect x="30" y="195" width="250" height="80" rx="8" fill="#e6fffa" stroke="#276749" stroke-width="2"/>
  <text x="155" y="220" class="lbl-dark" font-size="13" font-weight="bold">Copay plan. Pick a network.</text>
  <text x="155" y="240" class="lbl-dark" font-size="12">Ticket system routes to vendor.</text>
  <text x="155" y="258" class="lbl-dark" font-size="12">Dave's team is NOT involved.</text>

  <rect x="320" y="195" width="250" height="80" rx="8" fill="#fff5f5" stroke="#9b2c2c" stroke-width="2"/>
  <text x="445" y="220" class="lbl-dark" font-size="13" font-weight="bold">Orchestrator + Service Rep</text>
  <text x="445" y="240" class="lbl-dark" font-size="12">Hospital waterfall. Drug waterfall.</text>
  <text x="445" y="258" class="lbl-dark" font-size="12">Every dollar actively managed.</text>

  <text x="300" y="320" class="lbl-dark" font-size="14" font-weight="bold">Same employee pool. Two completely different systems.</text>
</svg>`;

export const duckDiagram = `
<svg viewBox="0 0 600 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Duck: smooth on top (what the client sees), paddling like hell underneath (what Dave manages)">
  <style>
    .lbl { font-family: system-ui, sans-serif; text-anchor: middle; }
  </style>
  <text x="300" y="30" class="lbl" fill="#1a202c" font-size="18" font-weight="bold">The Duck</text>
  <text x="300" y="50" class="lbl" fill="#4a5568" font-size="13">Smooth on top. Paddling like hell underneath.</text>
  <!-- Water line -->
  <path d="M 0 180 Q 100 170 200 180 Q 300 190 400 180 Q 500 170 600 180" fill="none" stroke="#2b6cb0" stroke-width="3" opacity="0.6"/>
  <rect x="0" y="180" width="600" height="200" fill="#ebf8ff" opacity="0.3"/>
  <!-- Above water -->
  <text x="300" y="85" class="lbl" fill="#276749" font-size="14" font-weight="bold">WHAT THE CLIENT SEES</text>
  <text x="150" y="115" class="lbl" fill="#2d3748" font-size="13">Two bills</text>
  <text x="300" y="115" class="lbl" fill="#2d3748" font-size="13">One dashboard</text>
  <text x="450" y="115" class="lbl" fill="#2d3748" font-size="13">One phone number</text>
  <text x="300" y="145" class="lbl" fill="#2d3748" font-size="13">Employees are happy</text>
  <!-- Below water -->
  <text x="300" y="215" class="lbl" fill="#9b2c2c" font-size="14" font-weight="bold">WHAT'S ACTUALLY HAPPENING</text>
  <text x="110" y="245" class="lbl" fill="#4a5568" font-size="11">10+ vendors managed</text>
  <text x="300" y="245" class="lbl" fill="#4a5568" font-size="11">Two claim pipes running</text>
  <text x="490" y="245" class="lbl" fill="#4a5568" font-size="11">Two waterfalls routing</text>
  <text x="110" y="270" class="lbl" fill="#4a5568" font-size="11">Enrollment feeds flowing</text>
  <text x="300" y="270" class="lbl" fill="#4a5568" font-size="11">HR-branded comms</text>
  <text x="490" y="270" class="lbl" fill="#4a5568" font-size="11">Drug flags monitoring</text>
  <text x="110" y="295" class="lbl" fill="#4a5568" font-size="11">Pre-certs intercepting</text>
  <text x="300" y="295" class="lbl" fill="#4a5568" font-size="11">Bills audited vs Medicare</text>
  <text x="490" y="295" class="lbl" fill="#4a5568" font-size="11">Data warehouse updating</text>
  <text x="300" y="340" class="lbl" fill="#1a202c" font-size="14" font-weight="bold">Dave's job: keep the duck calm on top. The process does the paddling.</text>
</svg>`;

export const hospitalWaterfallDiagram = `
<svg viewBox="0 0 600 350" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hospital claim waterfall: Audit first (cut 30%), then PPO or RBP or 501R">
  <style>
    .lbl { font-family: system-ui, sans-serif; text-anchor: middle; }
    .step { rx: 8; }
  </style>
  <text x="300" y="30" class="lbl" fill="#1a202c" font-size="18" font-weight="bold">Hospital Claim Waterfall</text>
  <text x="300" y="50" class="lbl" fill="#4a5568" font-size="13">Two bites at the apple. Shrink the bill, then shrink what's left.</text>
  <!-- Step 1: Audit -->
  <rect x="150" y="70" width="300" height="60" class="step" fill="#2b6cb0"/>
  <text x="300" y="97" class="lbl" fill="white" font-size="15" font-weight="bold">STEP 1: Bill Audit</text>
  <text x="300" y="117" class="lbl" fill="white" font-size="12">Audit every line vs Medicare rates. Cut ~30%.</text>
  <line x1="300" y1="130" x2="300" y2="155" stroke="#4a5568" stroke-width="2" marker-end="url(#arrow)"/>
  <!-- Waterfall -->
  <rect x="50" y="160" width="150" height="50" class="step" fill="#276749"/>
  <text x="125" y="183" class="lbl" fill="white" font-size="13" font-weight="bold">1. PPO Network</text>
  <text x="125" y="200" class="lbl" fill="white" font-size="10">Negotiated rate</text>

  <rect x="225" y="160" width="150" height="50" class="step" fill="#d69e2e"/>
  <text x="300" y="183" class="lbl" fill="white" font-size="13" font-weight="bold">2. RBP</text>
  <text x="300" y="200" class="lbl" fill="white" font-size="10">% of Medicare</text>

  <rect x="400" y="160" width="150" height="50" class="step" fill="#9b2c2c"/>
  <text x="475" y="183" class="lbl" fill="white" font-size="13" font-weight="bold">3. 501R</text>
  <text x="475" y="200" class="lbl" fill="white" font-size="10">Nonprofit = $0</text>

  <!-- Example -->
  <rect x="100" y="240" width="400" height="80" rx="8" fill="#f7fafc" stroke="#e2e8f0" stroke-width="2"/>
  <text x="300" y="265" class="lbl" fill="#1a202c" font-size="14" font-weight="bold">Example</text>
  <text x="300" y="285" class="lbl" fill="#4a5568" font-size="13">$100K bill → Audit catches 30% → $70K → 501R → $0</text>
  <text x="300" y="305" class="lbl" fill="#276749" font-size="12">Even without 501R: audit + RBP can take $100K to $15-20K</text>
  <defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#4a5568"/></marker></defs>
</svg>`;

export const drugWaterfallDiagram = `
<svg viewBox="0 0 500 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Drug claim waterfall: MAP/PAP first, then international pharmacy, then 340B">
  <style>
    .lbl { font-family: system-ui, sans-serif; text-anchor: middle; fill: white; }
  </style>
  <text x="250" y="25" font-family="system-ui" fill="#1a202c" font-size="16" font-weight="bold" text-anchor="middle">Drug Waterfall</text>
  <rect x="20" y="45" width="140" height="50" rx="8" fill="#2b6cb0"/>
  <text x="90" y="68" class="lbl" font-size="13" font-weight="bold">1. MAP/PAP</text>
  <text x="90" y="85" class="lbl" font-size="10">Manufacturer assist</text>

  <rect x="180" y="45" width="140" height="50" rx="8" fill="#276749"/>
  <text x="250" y="68" class="lbl" font-size="13" font-weight="bold">2. International</text>
  <text x="250" y="85" class="lbl" font-size="10">Same drug, lower cost</text>

  <rect x="340" y="45" width="140" height="50" rx="8" fill="#d69e2e"/>
  <text x="410" y="68" class="lbl" font-size="13" font-weight="bold">3. 340B</text>
  <text x="410" y="85" class="lbl" font-size="10">Federal discount</text>

  <line x1="160" y1="70" x2="180" y2="70" stroke="#4a5568" stroke-width="2"/>
  <line x1="320" y1="70" x2="340" y2="70" stroke="#4a5568" stroke-width="2"/>
  <text x="250" y="135" font-family="system-ui" fill="#4a5568" font-size="12" text-anchor="middle">Ordered by cost reduction. Try #1 first.</text>
  <text x="250" y="160" font-family="system-ui" fill="#1a202c" font-size="13" text-anchor="middle" font-weight="bold">A $50K/year specialty drug can go to $0.</text>
</svg>`;

export const twoAggregatorsDiagram = `
<svg viewBox="0 0 600 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two aggregators: Dave aggregates fixed costs into one bill, TPA aggregates variable costs into one bill. CFO sees two numbers.">
  <style>
    .lbl { font-family: system-ui, sans-serif; text-anchor: middle; }
  </style>
  <text x="300" y="25" class="lbl" fill="#1a202c" font-size="16" font-weight="bold">Two Bills. That's It.</text>
  <!-- Dave side -->
  <rect x="30" y="50" width="240" height="80" rx="10" fill="#2b6cb0"/>
  <text x="150" y="80" class="lbl" fill="white" font-size="15" font-weight="bold">FIXED COSTS</text>
  <text x="150" y="100" class="lbl" fill="white" font-size="12">Dave aggregates → ONE invoice</text>
  <text x="150" y="118" class="lbl" fill="white" font-size="10">Stop loss, life, dental, vision, EAP, FSA...</text>
  <!-- TPA side -->
  <rect x="330" y="50" width="240" height="80" rx="10" fill="#9b2c2c"/>
  <text x="450" y="80" class="lbl" fill="white" font-size="15" font-weight="bold">VARIABLE COSTS</text>
  <text x="450" y="100" class="lbl" fill="white" font-size="12">TPA aggregates → ONE claims bill</text>
  <text x="450" y="118" class="lbl" fill="white" font-size="10">Medical claims + pharmacy claims</text>
  <!-- CFO -->
  <line x1="150" y1="130" x2="300" y2="175" stroke="#2b6cb0" stroke-width="2"/>
  <line x1="450" y1="130" x2="300" y2="175" stroke="#9b2c2c" stroke-width="2"/>
  <rect x="200" y="165" width="200" height="50" rx="10" fill="#1a365d"/>
  <text x="300" y="190" class="lbl" fill="white" font-size="14" font-weight="bold">CFO DASHBOARD</text>
  <text x="300" y="205" class="lbl" fill="white" font-size="11">Two numbers. Zero vendor chasing.</text>
</svg>`;

export const dataMoatDiagram = `
<svg viewBox="0 0 500 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Structural dependency: every month of data makes the moat deeper. To leave, rebuild everything from scratch.">
  <style>
    .lbl { font-family: system-ui, sans-serif; text-anchor: middle; }
  </style>
  <text x="250" y="25" class="lbl" fill="#1a202c" font-size="16" font-weight="bold">The Moat Gets Deeper Every Month</text>
  <!-- Layers building up -->
  <rect x="100" y="50" width="300" height="30" rx="4" fill="#ebf8ff" stroke="#2b6cb0"/>
  <text x="250" y="70" class="lbl" fill="#2b6cb0" font-size="11">Month 1: Enrollment data + vendor connections</text>
  <rect x="80" y="85" width="340" height="30" rx="4" fill="#bee3f8" stroke="#2b6cb0"/>
  <text x="250" y="105" class="lbl" fill="#2b6cb0" font-size="11">Month 6: Claims history + savings tracking</text>
  <rect x="60" y="120" width="380" height="30" rx="4" fill="#90cdf4" stroke="#2b6cb0"/>
  <text x="250" y="140" class="lbl" fill="#1a365d" font-size="11">Year 1: Full data warehouse + compliance trail</text>
  <rect x="40" y="155" width="420" height="30" rx="4" fill="#63b3ed" stroke="#2b6cb0"/>
  <text x="250" y="175" class="lbl" fill="white" font-size="11">Year 2: Trend analysis + renewal leverage + benchmarks</text>
  <rect x="20" y="190" width="460" height="30" rx="4" fill="#2b6cb0"/>
  <text x="250" y="210" class="lbl" fill="white" font-size="11">Year 3+: Irreplaceable operational layer</text>

  <text x="250" y="250" class="lbl" fill="#4a5568" font-size="12">To fire SVG, rebuild every API connection, every dashboard,</text>
  <text x="250" y="268" class="lbl" fill="#4a5568" font-size="12">every compliance tracker, and every data feed from scratch.</text>
</svg>`;

export const paradigmShiftDiagram = `
<svg viewBox="0 0 600 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Paradigm shift: Traditional Brokerage vs Insurance Informatics comparison">
  <style>
    .lbl { font-family: system-ui, sans-serif; text-anchor: middle; }
    .hdr { font-family: system-ui, sans-serif; text-anchor: middle; fill: white; font-weight: bold; }
  </style>
  <!-- Headers -->
  <rect x="140" y="10" width="200" height="35" rx="6" fill="#718096"/>
  <text x="240" y="33" class="hdr" font-size="13">Traditional Brokerage</text>
  <rect x="360" y="10" width="220" height="35" rx="6" fill="#2b6cb0"/>
  <text x="470" y="33" class="hdr" font-size="13">Insurance Informatics</text>
  <!-- Rows -->
  <text x="65" y="75" class="lbl" fill="#1a202c" font-size="12" font-weight="bold">Core Focus</text>
  <text x="240" y="75" class="lbl" fill="#718096" font-size="12">Chasing Price</text>
  <text x="470" y="75" class="lbl" fill="#2b6cb0" font-size="12" font-weight="bold">Engineering Process</text>
  <line x1="20" y1="88" x2="580" y2="88" stroke="#e2e8f0"/>

  <text x="65" y="115" class="lbl" fill="#1a202c" font-size="12" font-weight="bold">Input</text>
  <text x="240" y="115" class="lbl" fill="#718096" font-size="12">Messy Spreadsheets</text>
  <text x="470" y="115" class="lbl" fill="#2b6cb0" font-size="12" font-weight="bold">Structured Data (API + EDI)</text>
  <line x1="20" y1="128" x2="580" y2="128" stroke="#e2e8f0"/>

  <text x="65" y="155" class="lbl" fill="#1a202c" font-size="12" font-weight="bold">Tech</text>
  <text x="240" y="155" class="lbl" fill="#718096" font-size="12">Legacy Batch</text>
  <text x="470" y="155" class="lbl" fill="#2b6cb0" font-size="12" font-weight="bold">38-Node Cloudflare Edge</text>
  <line x1="20" y1="168" x2="580" y2="168" stroke="#e2e8f0"/>

  <text x="65" y="195" class="lbl" fill="#1a202c" font-size="12" font-weight="bold">Plan Design</text>
  <text x="240" y="195" class="lbl" fill="#718096" font-size="12">Endless HR Debates</text>
  <text x="470" y="195" class="lbl" fill="#2b6cb0" font-size="12" font-weight="bold">Rule of Twos</text>
  <line x1="20" y1="208" x2="580" y2="208" stroke="#e2e8f0"/>

  <text x="65" y="235" class="lbl" fill="#1a202c" font-size="12" font-weight="bold">Revenue</text>
  <text x="240" y="235" class="lbl" fill="#718096" font-size="12">Hidden Commissions</text>
  <text x="470" y="235" class="lbl" fill="#2b6cb0" font-size="12" font-weight="bold">Flat PEPM — Zero Commission</text>
</svg>`;
