from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import List, Tuple

class ApplicationStatus(Enum):
    """Status of a job application"""

    APPLYING = "Applying"
    APPLIED = "Applied"
    ONLINE_ASSESSMENT = "Online Assessment"
    TECHNICAL_INTERVIEW = "Technical Interview"
    BEHAVIORAL_INTERVIEW = "Behavioral Interview"
    REJECTED = "Rejected"
    GHOSTED = "Ghosted"
    OFFER = "Offer"


@dataclass
class ApplicationMetadata:
    """Metadata for a job application"""

    url: str  # posting url
    role: str
    company: str
    location: str
    duration: str  # e.g. "4 months W24"
    description: str
    notes: str
    check_url: str  # url to check application status
    questions: List[Tuple[str, str]] = field(default_factory=list)  # question, answer
    question_ids: dict = field(default_factory=dict)  # map of index to question ID
    resume_path: str = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class Application:
    """Job application data"""

    metadata: ApplicationMetadata
    status: ApplicationStatus = ApplicationStatus.APPLYING
    id: int = None  # database ID, None for new applications
