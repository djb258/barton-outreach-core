"""
Composio MCP Client Wrapper - Barton Toolbox Hub
Provides unified interface to Google Workspace services via Composio MCP server

Usage:
    from lib.composio_client import ComposioClient

    client = ComposioClient()
    sheet_id = client.create_google_sheet("Error Log", data)
    doc_id = client.fill_google_doc(template_id, data)
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ComposioConfig:
    """Composio MCP configuration"""
    mcp_url: str
    api_key: str
    client_id: Optional[str] = None
    timeout: int = 30

    @classmethod
    def from_env(cls):
        return cls(
            mcp_url=os.getenv("COMPOSIO_MCP_URL", "http://localhost:3001"),
            api_key=os.getenv("COMPOSIO_API_KEY", ""),
            client_id=os.getenv("COMPOSIO_CLIENT_ID"),
            timeout=int(os.getenv("COMPOSIO_TIMEOUT", "30"))
        )


class ComposioMCPError(Exception):
    """Base exception for Composio MCP errors"""
    pass


class ComposioClient:
    """
    Unified client for Google Workspace services via Composio MCP

    Supports:
    - Google Sheets (create, write, read)
    - Google Docs (create, fill templates)
    - Gmail (send emails)
    - Google Drive (file operations)
    """

    def __init__(self, config: Optional[ComposioConfig] = None):
        self.config = config or ComposioConfig.from_env()
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        })

    def _make_request(
        self,
        tool: str,
        action: str,
        data: Dict,
        unique_id: str,
        process_id: str = "PRC-COMPOSIO-001",
        orbt_layer: int = 2
    ) -> Dict:
        """
        Make request to Composio MCP server

        Args:
            tool: Tool name (e.g., "googlesheets", "googledocs")
            action: Action to perform (e.g., "create_sheet", "fill_template")
            data: Action-specific data
            unique_id: HEIR unique ID
            process_id: Process ID
            orbt_layer: ORBT layer number

        Returns:
            Response data from MCP server
        """
        payload = {
            "tool": f"{tool}_{action}",
            "data": data,
            "unique_id": unique_id,
            "process_id": process_id,
            "orbt_layer": orbt_layer,
            "blueprint_version": "1.0"
        }

        try:
            response = self.session.post(
                f"{self.config.mcp_url}/tool",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"[Composio] {tool}.{action} completed: {result.get('status')}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"[Composio] Request failed: {e}")
            raise ComposioMCPError(f"MCP request failed: {e}")

    # ==================== GOOGLE SHEETS ====================

    def create_google_sheet(
        self,
        title: str,
        data: List[List[Any]],
        headers: Optional[List[str]] = None,
        unique_id: Optional[str] = None
    ) -> str:
        """
        Create a new Google Sheet with data

        Args:
            title: Sheet title
            data: 2D array of cell values
            headers: Optional header row
            unique_id: HEIR unique ID (auto-generated if not provided)

        Returns:
            Google Sheet ID
        """
        if unique_id is None:
            unique_id = f"HEIR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-SHEET"

        sheet_data = data
        if headers:
            sheet_data = [headers] + data

        request_data = {
            "title": title,
            "data": sheet_data,
            "share": True  # Make shareable with link
        }

        result = self._make_request(
            tool="googlesheets",
            action="create",
            data=request_data,
            unique_id=unique_id
        )

        if result.get("status") == "success":
            sheet_id = result.get("data", {}).get("spreadsheet_id")
            sheet_url = result.get("data", {}).get("spreadsheet_url")
            logger.info(f"[Composio] Created Google Sheet: {sheet_url}")
            return sheet_id
        else:
            raise ComposioMCPError(f"Failed to create sheet: {result.get('message')}")

    def write_to_sheet(
        self,
        sheet_id: str,
        tab_name: str,
        data: List[List[Any]],
        start_cell: str = "A1",
        unique_id: Optional[str] = None
    ) -> bool:
        """
        Write data to existing Google Sheet

        Args:
            sheet_id: Google Sheet ID
            tab_name: Tab/worksheet name
            data: 2D array of cell values
            start_cell: Starting cell (e.g., "A1")
            unique_id: HEIR unique ID

        Returns:
            True if successful
        """
        if unique_id is None:
            unique_id = f"HEIR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-WRITE"

        request_data = {
            "spreadsheet_id": sheet_id,
            "range": f"{tab_name}!{start_cell}",
            "values": data
        }

        result = self._make_request(
            tool="googlesheets",
            action="update",
            data=request_data,
            unique_id=unique_id
        )

        return result.get("status") == "success"

    def read_from_sheet(
        self,
        sheet_id: str,
        tab_name: str,
        range_spec: str = "A1:Z1000",
        unique_id: Optional[str] = None
    ) -> List[List[Any]]:
        """
        Read data from Google Sheet

        Args:
            sheet_id: Google Sheet ID
            tab_name: Tab/worksheet name
            range_spec: Cell range (e.g., "A1:Z1000")
            unique_id: HEIR unique ID

        Returns:
            2D array of cell values
        """
        if unique_id is None:
            unique_id = f"HEIR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-READ"

        request_data = {
            "spreadsheet_id": sheet_id,
            "range": f"{tab_name}!{range_spec}"
        }

        result = self._make_request(
            tool="googlesheets",
            action="read",
            data=request_data,
            unique_id=unique_id
        )

        if result.get("status") == "success":
            return result.get("data", {}).get("values", [])
        else:
            raise ComposioMCPError(f"Failed to read sheet: {result.get('message')}")

    # ==================== GOOGLE DOCS ====================

    def create_google_doc(
        self,
        title: str,
        content: str,
        unique_id: Optional[str] = None
    ) -> str:
        """
        Create a new Google Doc

        Args:
            title: Document title
            content: Document content (plain text or HTML)
            unique_id: HEIR unique ID

        Returns:
            Google Doc ID
        """
        if unique_id is None:
            unique_id = f"HEIR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-DOC"

        request_data = {
            "title": title,
            "content": content
        }

        result = self._make_request(
            tool="googledocs",
            action="create",
            data=request_data,
            unique_id=unique_id
        )

        if result.get("status") == "success":
            doc_id = result.get("data", {}).get("document_id")
            doc_url = result.get("data", {}).get("document_url")
            logger.info(f"[Composio] Created Google Doc: {doc_url}")
            return doc_id
        else:
            raise ComposioMCPError(f"Failed to create doc: {result.get('message')}")

    def fill_doc_template(
        self,
        template_id: str,
        variables: Dict[str, str],
        new_title: Optional[str] = None,
        unique_id: Optional[str] = None
    ) -> str:
        """
        Fill a Google Docs template with variables

        Args:
            template_id: Template document ID
            variables: Dictionary of {placeholder: value} pairs
            new_title: Title for the new document (optional)
            unique_id: HEIR unique ID

        Returns:
            New document ID
        """
        if unique_id is None:
            unique_id = f"HEIR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-FILL"

        request_data = {
            "template_id": template_id,
            "variables": variables,
            "new_title": new_title or f"Document {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }

        result = self._make_request(
            tool="googledocs",
            action="fill_template",
            data=request_data,
            unique_id=unique_id
        )

        if result.get("status") == "success":
            doc_id = result.get("data", {}).get("document_id")
            doc_url = result.get("data", {}).get("document_url")
            logger.info(f"[Composio] Filled template: {doc_url}")
            return doc_id
        else:
            raise ComposioMCPError(f"Failed to fill template: {result.get('message')}")

    # ==================== GMAIL ====================

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        unique_id: Optional[str] = None
    ) -> bool:
        """
        Send email via Gmail

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            unique_id: HEIR unique ID

        Returns:
            True if sent successfully
        """
        if unique_id is None:
            unique_id = f"HEIR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-EMAIL"

        request_data = {
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc,
            "bcc": bcc
        }

        result = self._make_request(
            tool="gmail",
            action="send",
            data=request_data,
            unique_id=unique_id
        )

        if result.get("status") == "success":
            logger.info(f"[Composio] Email sent to {to}")
            return True
        else:
            logger.error(f"[Composio] Failed to send email: {result.get('message')}")
            return False

    # ==================== UTILITY METHODS ====================

    def health_check(self) -> bool:
        """
        Check if Composio MCP server is healthy

        Returns:
            True if server is responding
        """
        try:
            response = self.session.get(
                f"{self.config.mcp_url}/mcp/health",
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_connected_accounts(self) -> List[Dict]:
        """
        List all connected Google accounts

        Returns:
            List of account info dictionaries
        """
        try:
            result = self._make_request(
                tool="manage",
                action="connected_account",
                data={"action": "list"},
                unique_id=f"HEIR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-LIST"
            )

            if result.get("status") == "success":
                return result.get("data", {}).get("accounts", [])
            else:
                return []
        except ComposioMCPError:
            return []


# ==================== CONVENIENCE FUNCTIONS ====================

def create_error_sheet(
    errors: List[Dict],
    sheet_title: str = "Error Log"
) -> str:
    """
    Create a Google Sheet for error tracking

    Args:
        errors: List of error dictionaries
        sheet_title: Sheet title

    Returns:
        Google Sheet ID
    """
    client = ComposioClient()

    # Define headers
    headers = [
        "Error ID",
        "Company ID",
        "Error Type",
        "Error Message",
        "Severity",
        "Created At",
        "Status"
    ]

    # Convert errors to rows
    data = []
    for error in errors:
        row = [
            error.get("error_id", ""),
            error.get("company_unique_id", ""),
            error.get("error_type", ""),
            error.get("error_message", ""),
            error.get("severity", ""),
            error.get("created_at", ""),
            error.get("resolution_status", "pending")
        ]
        data.append(row)

    return client.create_google_sheet(
        title=sheet_title,
        data=data,
        headers=headers
    )


def fill_outreach_template(
    template_id: str,
    company_name: str,
    contact_name: str,
    title: str,
    additional_vars: Optional[Dict] = None
) -> str:
    """
    Fill an outreach email/doc template

    Args:
        template_id: Google Docs template ID
        company_name: Company name
        contact_name: Contact person name
        title: Contact's title
        additional_vars: Additional template variables

    Returns:
        New document ID
    """
    client = ComposioClient()

    variables = {
        "company_name": company_name,
        "contact_name": contact_name,
        "title": title,
        "date": datetime.now().strftime("%B %d, %Y")
    }

    if additional_vars:
        variables.update(additional_vars)

    return client.fill_doc_template(
        template_id=template_id,
        variables=variables,
        new_title=f"Outreach - {company_name}"
    )


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Test Composio MCP connection
    client = ComposioClient()

    print(f"[Test] Checking Composio MCP health...")
    if client.health_check():
        print("[Test] ✅ Composio MCP is healthy")
    else:
        print("[Test] ❌ Composio MCP is not responding")
        exit(1)

    print(f"\n[Test] Listing connected accounts...")
    accounts = client.list_connected_accounts()
    print(f"[Test] Found {len(accounts)} connected account(s)")
    for account in accounts:
        print(f"  - {account.get('email', 'Unknown')}")

    print("\n[Test] Composio client is ready!")
