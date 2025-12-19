# Barton Outreach Core - Spokes Package
# Each spoke anchors to the Company Hub (Master Node)
#
# BICYCLE WHEEL DOCTRINE v1.1:
# All spokes MUST anchor to a valid Company Hub record.
# No spoke processes records without company_id + domain + email_pattern.

from typing import List

# Import all spoke implementations
from .people import PeopleNodeSpoke, PersonRecord
from .dol import DOLNodeSpoke, Form5500Record, ScheduleARecord
from .blog import BlogNewsSpoke, BlogArticle, NewsEvent
from .talent_flow import TalentFlowSpoke, TalentMovement, MovementType
from .outreach import OutreachSpoke, OutreachConfig, OutreachCandidate, CampaignTarget

REGISTERED_SPOKES: List[str] = [
    "people",      # Spoke #1 - People/Contacts - ACTIVE
    "dol",         # Spoke #2 - DOL Form 5500 - ACTIVE
    "blog_news",   # Spoke #3 - Blog/News - ACTIVE
    "talent_flow", # Spoke #4 - Talent Flow - ACTIVE
    "outreach",    # Spoke #6 - Outreach - ACTIVE (OUTPUT SPOKE)
]

__all__ = [
    # Spoke Registry
    "REGISTERED_SPOKES",
    # People Spoke (#1)
    "PeopleNodeSpoke",
    "PersonRecord",
    # DOL Spoke (#2)
    "DOLNodeSpoke",
    "Form5500Record",
    "ScheduleARecord",
    # Blog Spoke (#3)
    "BlogNewsSpoke",
    "BlogArticle",
    "NewsEvent",
    # Talent Flow Spoke (#4)
    "TalentFlowSpoke",
    "TalentMovement",
    "MovementType",
    # Outreach Spoke (#6 - OUTPUT)
    "OutreachSpoke",
    "OutreachConfig",
    "OutreachCandidate",
    "CampaignTarget",
]
