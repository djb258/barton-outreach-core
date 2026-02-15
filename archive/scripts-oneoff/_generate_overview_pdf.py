"""Generate Database Overview PDF for email sharing."""

from fpdf import FPDF
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "Barton_Database_Overview_2026-02-13.pdf")


class OverviewPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "BARTON OUTREACH  |  DATABASE OVERVIEW  |  2026-02-13", align="R")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 90, 160)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(0, 90, 160)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def add_table(self, headers, rows, col_widths=None, header_color=(0, 90, 160)):
        if col_widths is None:
            avail = self.w - self.l_margin - self.r_margin
            col_widths = [avail / len(headers)] * len(headers)

        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*header_color)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 8)
        fill = False
        for row in rows:
            if self.get_y() > 265:
                self.add_page()
            self.set_fill_color(240, 245, 250) if fill else self.set_fill_color(255, 255, 255)
            self.set_text_color(30, 30, 30)
            is_bold = row[0].startswith("**") if row else False
            for i, cell in enumerate(row):
                txt = cell.replace("**", "")
                if is_bold:
                    self.set_font("Helvetica", "B", 8)
                else:
                    self.set_font("Helvetica", "", 8)
                align = "L" if i == 0 else "R"
                self.cell(col_widths[i], 6, txt, border=1, fill=True, align=align)
            self.ln()
            fill = not fill
        self.ln(3)

    def add_note(self, text):
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 4, text)
        self.ln(2)


def build_pdf():
    pdf = OverviewPDF("P", "mm", "Letter")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # =========================================================================
    # TITLE
    # =========================================================================
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 90, 160)
    pdf.cell(0, 12, "BARTON OUTREACH", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Database Overview", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Total Companies: 94,129  |  Updated: 2026-02-13", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # =========================================================================
    # SOVEREIGN STATES
    # =========================================================================
    pdf.section_title("SOVEREIGN STATES (90,308 companies - excludes CA & NY)")

    state_headers = ["State", "Companies", "50+ Emp%", "DOL%", "Blog%", "Co LI%",
                     "CEO%", "CEO LI%", "CFO%", "CFO LI%", "HR%", "HR LI%"]
    w = pdf.w - pdf.l_margin - pdf.r_margin
    state_widths = [w*0.07, w*0.09, w*0.08, w*0.07, w*0.07, w*0.08,
                    w*0.07, w*0.08, w*0.07, w*0.08, w*0.07, w*0.08]
    state_rows = [
        ["PA", "17,566", "42.1%", "76.6%", "99.9%", "50.6%", "66.1%", "53.4%", "58.9%", "47.5%", "58.6%", "48.1%"],
        ["OH", "17,012", "40.3%", "79.0%", "99.9%", "47.7%", "65.3%", "52.4%", "59.8%", "48.8%", "62.4%", "52.0%"],
        ["VA", "12,645", "44.1%", "76.2%", "99.8%", "51.9%", "68.1%", "55.6%", "61.3%", "51.1%", "59.5%", "49.8%"],
        ["NC", "11,866", "44.9%", "71.6%", "99.8%", "54.8%", "69.2%", "55.8%", "63.4%", "51.7%", "65.8%", "55.1%"],
        ["MD", "9,784", "39.0%", "79.6%", "99.9%", "45.1%", "65.2%", "52.4%", "61.0%", "49.9%", "62.7%", "52.2%"],
        ["KY", "4,352", "--", "81.0%", "99.9%", "43.3%", "60.6%", "47.3%", "56.2%", "43.5%", "58.7%", "46.2%"],
        ["DC", "2,621", "--", "98.6%", "100%", "47.0%", "84.4%", "69.1%", "84.5%", "70.6%", "84.3%", "70.7%"],
        ["OK", "1,849", "--", "55.1%", "99.8%", "36.8%", "58.2%", "42.8%", "56.0%", "41.2%", "56.0%", "40.6%"],
    ]
    pdf.add_table(state_headers, state_rows, state_widths)

    # =========================================================================
    # CT SUB-HUB
    # =========================================================================
    pdf.section_title("CT SUB-HUB")

    ct_widths = [w*0.50, w*0.25, w*0.25]
    ct_rows = [
        ["Has Employee Data", "70,392", "74.8%"],
        ["50+ Employees", "37,493", "39.8%"],
        ["**Total Employees (50+)**", "**16,205,443**", "**--**"],
        ["Email Method", "80,950", "86.0%"],
        ["Domain Reachable", "52,870", "85.4%"],
        ["Domain Unreachable", "9,047", "14.6%"],
    ]
    pdf.add_table(["Metric", "Count", "%"], ct_rows, ct_widths)

    pdf.sub_title("Employee Size Bands (50+ only)")
    band_widths = [w*0.25, w*0.25, w*0.30, w*0.20]
    band_rows = [
        ["50-100", "24,179", "1,233,129", "64.5%"],
        ["101-250", "6,795", "1,365,795", "18.1%"],
        ["501-1,000", "2,696", "1,350,696", "7.2%"],
        ["1,001-5,000", "2,657", "2,659,657", "7.1%"],
        ["5,001+", "1,166", "9,596,166", "3.1%"],
        ["**Total**", "**37,493**", "**16,205,443**", "**100%**"],
    ]
    pdf.add_table(["Band", "Companies", "Total Employees", "%"], band_rows, band_widths)
    pdf.add_note("Employee counts are Hunter enrichment band minimums (floor estimates). Real totals are higher.")

    # =========================================================================
    # DOL SUB-HUB
    # =========================================================================
    pdf.section_title("DOL SUB-HUB")

    dol_widths = [w*0.50, w*0.25, w*0.25]
    dol_rows = [
        ["**DOL Linked (EIN)**", "**73,617**", "**78.2% of companies**"],
        ["  -> Has Filing", "69,318", "94.2% of DOL"],
        ["  -> Renewal Month", "69,029", "93.8% of DOL"],
        ["  -> Carrier", "9,991", "13.6% of DOL"],
        ["  -> Broker/Advisor", "6,818", "9.3% of DOL"],
    ]
    pdf.add_table(["Metric", "Count", "%"], dol_rows, dol_widths)
    pdf.add_note("DOL Linked is measured against total companies. All sub-metrics cascade off DOL Linked.")

    pdf.sub_title("Funding Type")
    fund_widths = [w*0.40, w*0.30, w*0.30]
    fund_rows = [
        ["Pension Only", "54,673", "74.3%"],
        ["Fully Insured", "11,567", "15.7%"],
        ["Unknown", "4,588", "6.2%"],
        ["Self-Funded", "2,874", "3.9%"],
    ]
    pdf.add_table(["Type", "Count", "% of DOL"], fund_rows, fund_widths)

    # =========================================================================
    # BLOG SUB-HUB
    # =========================================================================
    pdf.section_title("BLOG SUB-HUB")

    blog_widths = [w*0.50, w*0.25, w*0.25]
    blog_rows = [
        ["Blog Coverage", "93,596", "99.4%"],
        ["Companies with Sitemap", "31,679", "33.7%"],
        ["Companies with Source URLs", "40,381", "42.9%"],
        ["Company LinkedIn", "45,057", "47.9%"],
    ]
    pdf.add_table(["Metric", "Count", "%"], blog_rows, blog_widths)

    # =========================================================================
    # PEOPLE SUB-HUB
    # =========================================================================
    pdf.section_title("PEOPLE SUB-HUB")

    pdf.sub_title("Readiness Funnel")
    funnel_widths = [w*0.50, w*0.25, w*0.25]
    funnel_rows = [
        ["**Total Companies**", "**94,129**", "**100%**"],
        ["At Least 1 Slot Filled", "63,648", "67.6%"],
        ["At Least 1 Person Reachable", "60,180", "63.9%"],
        ["Zero Slots (unreachable)", "30,481", "32.4%"],
    ]
    pdf.add_table(["Step", "Count", "%"], funnel_rows, funnel_widths)
    pdf.add_note("Reachable = has a verified email (outreach_ready = TRUE) OR a LinkedIn URL for at least one filled slot.")

    pdf.sub_title("Depth of Coverage")
    depth_widths = [w*0.20, w*0.15, w*0.20, w*0.22, w*0.23]
    depth_rows = [
        ["**All 3 Filled**", "54,949", "32,585 (59.3%)", "41,689 (75.9%)", "25,014 (45.5%)"],
        ["2 of 3 Filled", "2,884", "1,155 (40.0%)", "2,271 (78.7%)", "1,048 (36.3%)"],
        ["1 of 3 Filled", "5,815", "2,843 (48.9%)", "4,949 (85.1%)", "2,749 (47.3%)"],
        ["0 Filled", "30,481", "--", "--", "--"],
    ]
    pdf.add_table(["Depth", "Companies", "All Have Email", "All Have LinkedIn", "Full Coverage"], depth_rows, depth_widths)

    pdf.sub_title("Email Verification")
    ev_widths = [w*0.50, w*0.25, w*0.25]
    ev_rows = [
        ["People with Email", "181,478", "--"],
        ["Email Verified", "145,358", "80.1%"],
        ["Outreach Ready", "122,094", "67.3%"],
        ["Companies with 1+ Ready Email", "47,504", "50.5%"],
    ]
    pdf.add_table(["Metric", "Count", "%"], ev_rows, ev_widths)

    # =========================================================================
    # THREE MESSAGING LANES
    # =========================================================================
    pdf.section_title("THREE MESSAGING LANES")
    lane_widths = [w*0.60, w*0.40]
    lane_rows = [
        ["Cold Outreach", "94,129"],
        ["Appointments Already Had", "771"],
        ["Fractional CFO Partners", "833"],
    ]
    pdf.add_table(["Lane", "Records"], lane_rows, lane_widths)

    # =========================================================================
    # PAGE 2: ZIP 24015
    # =========================================================================
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 90, 160)
    pdf.cell(0, 12, "ZIP 24015 (Roanoke, VA) - 100-Mile Radius", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Market View", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Total Companies: 3,561  |  Updated: 2026-02-13", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # States in radius
    pdf.section_title("STATES IN RADIUS")
    zip_state_rows = [
        ["NC", "1,749", "44.6%", "71.1%", "99.9%", "53.5%", "68.8%", "81.2%", "63.0%", "82.1%", "65.5%", "84.3%"],
        ["VA", "1,305", "43.5%", "75.2%", "99.9%", "48.1%", "68.2%", "79.3%", "63.8%", "80.3%", "61.1%", "80.1%"],
        ["WV", "141", "36.2%", "70.2%", "100%", "47.5%", "52.5%", "60.8%", "47.5%", "62.7%", "48.9%", "60.9%"],
    ]
    pdf.add_table(state_headers, zip_state_rows, state_widths)

    # CT
    pdf.section_title("CT SUB-HUB")
    zip_ct_rows = [
        ["Has Employee Data", "2,727", "76.6%"],
        ["50+ Employees", "1,516", "42.6%"],
        ["**Total Employees (50+)**", "**623,416**", "**--**"],
        ["Email Method", "3,134", "88.0%"],
        ["Domain Reachable", "1,987", "84.7%"],
        ["Domain Unreachable", "360", "15.3%"],
    ]
    pdf.add_table(["Metric", "Count", "%"], zip_ct_rows, ct_widths)

    pdf.sub_title("Employee Size Bands (50+ only)")
    zip_band_rows = [
        ["50-100", "1,018", "51,918", "67.2%"],
        ["101-250", "260", "52,260", "17.2%"],
        ["501-1,000", "94", "47,094", "6.2%"],
        ["1,001-5,000", "102", "102,102", "6.7%"],
        ["5,001+", "42", "370,042", "2.8%"],
        ["**Total**", "**1,516**", "**623,416**", "**100%**"],
    ]
    pdf.add_table(["Band", "Companies", "Total Employees", "%"], zip_band_rows, band_widths)

    # DOL
    pdf.section_title("DOL SUB-HUB")
    zip_dol_rows = [
        ["**DOL Linked (EIN)**", "**2,685**", "**75.4% of companies**"],
        ["  -> Has Filing", "2,533", "94.3% of DOL"],
        ["  -> Renewal Month", "2,558", "95.3% of DOL"],
        ["  -> Carrier", "428", "15.9% of DOL"],
        ["  -> Broker/Advisor", "275", "10.2% of DOL"],
    ]
    pdf.add_table(["Metric", "Count", "%"], zip_dol_rows, dol_widths)

    pdf.sub_title("Funding Type")
    zip_fund_rows = [
        ["Pension Only", "2,199", "81.9%"],
        ["Fully Insured", "224", "8.3%"],
        ["Self-Funded", "136", "5.1%"],
    ]
    pdf.add_table(["Type", "Count", "% of DOL"], zip_fund_rows, fund_widths)

    # Blog
    pdf.section_title("BLOG SUB-HUB")
    zip_blog_rows = [
        ["Blog Coverage", "3,559", "99.9%"],
        ["Companies with Sitemap", "1,212", "34.0%"],
        ["Company LinkedIn", "1,685", "47.3%"],
    ]
    pdf.add_table(["Metric", "Count", "%"], zip_blog_rows, blog_widths)

    # People
    pdf.section_title("PEOPLE SUB-HUB")

    pdf.sub_title("Readiness Funnel")
    zip_funnel_rows = [
        ["**Total Companies**", "**3,561**", "**100%**"],
        ["At Least 1 Slot Filled", "2,499", "70.2%"],
        ["At Least 1 Person Reachable", "2,460", "69.1%"],
        ["Zero Slots (unreachable)", "1,062", "29.8%"],
    ]
    pdf.add_table(["Step", "Count", "%"], zip_funnel_rows, funnel_widths)

    pdf.sub_title("Depth of Coverage")
    zip_depth_rows = [
        ["**All 3 Filled**", "2,168", "1,246 (57.5%)", "1,610 (74.3%)", "914 (42.2%)"],
        ["2 of 3 Filled", "110", "47 (42.7%)", "95 (86.4%)", "43 (39.1%)"],
        ["1 of 3 Filled", "221", "110 (49.8%)", "196 (88.7%)", "108 (48.9%)"],
        ["0 Filled", "1,062", "--", "--", "--"],
    ]
    pdf.add_table(["Depth", "Companies", "All Have Email", "All Have LinkedIn", "Full Coverage"], zip_depth_rows, depth_widths)

    pdf.sub_title("Email Verification")
    zip_ev_rows = [
        ["People with Email", "6,937", "--"],
        ["Email Verified", "5,511", "79.4%"],
        ["Outreach Ready", "4,735", "68.3%"],
    ]
    pdf.add_table(["Metric", "Count", "%"], zip_ev_rows, ev_widths)

    # Lanes
    pdf.section_title("MESSAGING LANES (in radius)")
    zip_lane_rows = [
        ["Cold Outreach", "3,561"],
        ["Appointments Already Had", "5"],
    ]
    pdf.add_table(["Lane", "Records"], zip_lane_rows, lane_widths)

    # =========================================================================
    # OUTPUT
    # =========================================================================
    pdf.output(OUTPUT_PATH)
    print(f"PDF generated: {OUTPUT_PATH}")
    print(f"Size: {os.path.getsize(OUTPUT_PATH):,} bytes")


if __name__ == "__main__":
    build_pdf()
