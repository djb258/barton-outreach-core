"""
Doc Filler Backend - Barton Toolbox Hub
Barton ID: 04.04.02.04.10000.005
Altitude: 12000ft

Fills templates with mapped data
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from jinja2 import Template

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.composio_client import ComposioClient, ComposioMCPError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_BARTON_ID = "04.04.02.04.10000.005"
BLUEPRINT_ID = "04.svg.marketing.outreach.v1"


class DocFiller:
    """Document template filling engine with Google Docs and Jinja2 support"""

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self.composio = ComposioClient()
        logger.info(f"[{TOOL_BARTON_ID}] DocFiller initialized")

    def get_template_from_db(self, template_id: int) -> Optional[Dict]:
        """
        Retrieve template from database

        Args:
            template_id: Template ID in config.document_templates

        Returns:
            Template dictionary or None
        """
        query = """
            SELECT
                template_id,
                template_name,
                template_type,
                template_content,
                template_variables,
                google_docs_template_id
            FROM config.document_templates
            WHERE template_id = %s AND enabled = true
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (template_id,))
            result = cur.fetchone()
            return dict(result) if result else None

    def fill_jinja2_template(self, template_content: str, variables: Dict) -> str:
        """
        Fill Jinja2 template with variables

        Args:
            template_content: Jinja2 template string
            variables: Dictionary of variable values

        Returns:
            Filled template content
        """
        try:
            template = Template(template_content)
            filled_content = template.render(**variables)
            logger.info(f"[{TOOL_BARTON_ID}] ✅ Jinja2 template filled successfully")
            return filled_content
        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Jinja2 template error: {e}")
            raise

    def fill_google_docs_template(
        self,
        google_template_id: str,
        variables: Dict,
        new_title: Optional[str] = None
    ) -> Optional[str]:
        """
        Fill Google Docs template via Composio MCP

        Args:
            google_template_id: Google Docs template ID
            variables: Dictionary of placeholder values
            new_title: Title for new document

        Returns:
            New Google Doc ID or None
        """
        try:
            unique_id = f"HEIR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-DOCFILL"

            doc_id = self.composio.fill_doc_template(
                template_id=google_template_id,
                variables=variables,
                new_title=new_title,
                unique_id=unique_id
            )

            logger.info(f"[{TOOL_BARTON_ID}] ✅ Google Docs template filled: {doc_id}")
            return doc_id

        except ComposioMCPError as e:
            logger.error(f"[{TOOL_BARTON_ID}] Composio MCP error: {e}")
            self.log_error("composio_mcp_failed", str(e), {"google_template_id": google_template_id})
            return None
        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Unexpected error: {e}")
            self.log_error("doc_fill_failed", str(e), {"google_template_id": google_template_id})
            return None

    def fill_template(
        self,
        template_id: int,
        data: Dict,
        output_format: str = "google_docs"
    ) -> Optional[str]:
        """
        Fill document template with data

        Args:
            template_id: Database template ID
            data: Variable data for template
            output_format: "google_docs", "jinja2", or "both"

        Returns:
            Google Doc ID (if google_docs), filled content (if jinja2), or both
        """
        try:
            # Get template from database
            template = self.get_template_from_db(template_id)

            if not template:
                logger.error(f"[{TOOL_BARTON_ID}] Template {template_id} not found")
                return None

            logger.info(f"[{TOOL_BARTON_ID}] Filling template: {template['template_name']}")

            result = None

            # Fill Google Docs template if available
            if output_format in ["google_docs", "both"] and template.get('google_docs_template_id'):
                doc_id = self.fill_google_docs_template(
                    google_template_id=template['google_docs_template_id'],
                    variables=data,
                    new_title=f"{template['template_name']} - {datetime.now().strftime('%Y-%m-%d')}"
                )

                if doc_id:
                    result = doc_id
                    self.log_audit("template.filled", {
                        "template_id": template_id,
                        "template_name": template['template_name'],
                        "output_format": "google_docs",
                        "doc_id": doc_id
                    })

            # Fill Jinja2 template
            elif output_format in ["jinja2", "both"]:
                filled_content = self.fill_jinja2_template(
                    template_content=template['template_content'],
                    variables=data
                )

                result = filled_content
                self.log_audit("template.filled", {
                    "template_id": template_id,
                    "template_name": template['template_name'],
                    "output_format": "jinja2",
                    "content_length": len(filled_content)
                })

            return result

        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Error filling template {template_id}: {e}")
            self.log_error("template_fill_failed", str(e), {
                "template_id": template_id,
                "output_format": output_format
            })
            return None

    def fill_outreach_document(
        self,
        company_id: str,
        template_id: int,
        output_format: str = "google_docs"
    ) -> Optional[str]:
        """
        Fill outreach document with company/contact data

        Args:
            company_id: Company unique ID
            template_id: Template ID from database
            output_format: Output format (google_docs or jinja2)

        Returns:
            Document ID or content
        """
        try:
            # Fetch company and contact data from database
            query = """
                SELECT
                    c.company_unique_id,
                    c.company_name,
                    c.industry,
                    c.employee_count,
                    p.full_name as contact_name,
                    p.title as contact_title,
                    p.email as contact_email
                FROM marketing.company_master c
                LEFT JOIN marketing.people_master p ON p.company_unique_id = c.company_unique_id
                WHERE c.company_unique_id = %s
                LIMIT 1
            """

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (company_id,))
                result = cur.fetchone()

                if not result:
                    logger.error(f"[{TOOL_BARTON_ID}] Company {company_id} not found")
                    return None

                company_data = dict(result)

            # Prepare template variables
            variables = {
                "company_name": company_data.get('company_name', ''),
                "industry": company_data.get('industry', ''),
                "employee_count": company_data.get('employee_count', ''),
                "contact_name": company_data.get('contact_name', 'Hiring Manager'),
                "contact_title": company_data.get('contact_title', ''),
                "contact_email": company_data.get('contact_email', ''),
                "date": datetime.now().strftime("%B %d, %Y"),
                "current_year": datetime.now().strftime("%Y")
            }

            # Fill template
            result = self.fill_template(
                template_id=template_id,
                data=variables,
                output_format=output_format
            )

            logger.info(f"[{TOOL_BARTON_ID}] ✅ Outreach document created for {company_data.get('company_name')}")

            return result

        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Error creating outreach document: {e}")
            self.log_error("outreach_doc_failed", str(e), {
                "company_id": company_id,
                "template_id": template_id
            })
            return None

    def log_audit(self, event_type: str, data: Dict):
        """Log to audit table"""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO shq.audit_log (event_type, event_data, barton_id, created_at) VALUES (%s, %s, %s, NOW())",
                (event_type, json.dumps(data), TOOL_BARTON_ID)
            )
            self.conn.commit()

    def log_error(self, error_code: str, error_message: str, context: Dict):
        """Log error to error_master table"""
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO shq.error_master
                (error_code, error_message, severity, component, context, barton_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                (error_code, error_message, "error", "docfiller", json.dumps(context), TOOL_BARTON_ID)
            )
            self.conn.commit()


def main():
    connection_string = os.getenv("NEON_CONNECTION_STRING", "")
    filler = DocFiller(connection_string)
    logger.info(f"[{TOOL_BARTON_ID}] DocFiller ready")


if __name__ == "__main__":
    main()
