# security/validators/repo_validators.py
from typing import Tuple, Optional
import re
import logging

from ..configs.config_loader import settings

logger = logging.getLogger(__name__)

# Patterns for repository validation
GITHUB_URL_PATTERN = re.compile(
    r'^https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+(?:\.git)?/?$'
)
GITLAB_URL_PATTERN = re.compile(
    r'^https?://(?:www\.)?gitlab\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+(?:\.git)?/?$'
)
BITBUCKET_URL_PATTERN = re.compile(
    r'^https?://(?:www\.)?bitbucket\.org/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+(?:\.git)?/?$'
)
SSH_GIT_PATTERN = re.compile(
    r'^git@github\.com:[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\.git$'
)
LOCAL_PATH_PATTERN = re.compile(
    r'^[a-zA-Z0-9_\-./\\]+$'
)

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    r'<script',
    r'javascript:',
    r'data:',
    r'vbscript:',
    r'file://',
    r'ftp://',
    r'\.\./',
    r'\.\.\\',
    r'\x00',
    r'\r',
    r'\n',
    r'\t',
]

RE_DANGEROUS = re.compile('|'.join(DANGEROUS_PATTERNS), re.IGNORECASE)


def validate_repository_url(url: str) -> Tuple[bool, str]:
    """Validate repository URL for security and format."""
    if not url or not url.strip():
        return False, "Repository URL is required"
    
    url = url.strip()
    
    # Check length
    if len(url) > 2000:
        return False, "Repository URL is too long (max 2000 characters)"
    
    # Check for dangerous patterns
    if RE_DANGEROUS.search(url):
        logger.warning("Dangerous pattern detected in repository URL: %s", url)
        return False, "Repository URL contains invalid or dangerous characters"
    
    # Validate against allowed patterns
    is_valid = (
        GITHUB_URL_PATTERN.match(url) or
        GITLAB_URL_PATTERN.match(url) or
        BITBUCKET_URL_PATTERN.match(url) or
        SSH_GIT_PATTERN.match(url) or
        LOCAL_PATH_PATTERN.match(url)
    )
    
    if not is_valid:
        return False, "Repository URL format is not recognized. Use GitHub, GitLab, Bitbucket, SSH, or local path."
    
    return True, ""


def validate_project_description(description: str) -> Tuple[bool, str]:
    """Validate project description input."""
    if not description:
        return True, ""  # Optional field
    
    description = description.strip()
    
    # Check length
    if len(description) > 10000:
        return False, "Project description is too long (max 10000 characters)"
    
    # Check for dangerous patterns
    if RE_DANGEROUS.search(description):
        logger.warning("Dangerous pattern detected in project description")
        return False, "Project description contains invalid characters"
    
    return True, ""


def validate_goal(goal: str) -> Tuple[bool, str]:
    """Validate goal input."""
    if not goal:
        return True, ""  # Optional field
    
    goal = goal.strip()
    
    # Check length
    if len(goal) > 1000:
        return False, "Goal is too long (max 1000 characters)"
    
    # Check for dangerous patterns
    if RE_DANGEROUS.search(goal):
        logger.warning("Dangerous pattern detected in goal")
        return False, "Goal contains invalid characters"
    
    return True, ""


def validate_style(style: str) -> Tuple[bool, str]:
    """Validate writing style selection."""
    allowed_styles = [
        "Technical Blog",
        "Research Paper",
        "Documentation",
        "Marketing",
        "Tutorial"
    ]
    
    if not style:
        return True, ""  # Optional field
    
    if style not in allowed_styles:
        return False, f"Invalid style. Allowed styles: {', '.join(allowed_styles)}"
    
    return True, ""


def validate_comprehensive_submission(
    repo_url: str,
    goal: str = "",
    project_desc: str = "",
    style: str = ""
) -> Tuple[bool, str]:
    """Comprehensive validation of all submission inputs."""
    # Validate repository URL
    valid, error = validate_repository_url(repo_url)
    if not valid:
        return False, error
    
    # Validate goal
    valid, error = validate_goal(goal)
    if not valid:
        return False, f"Goal validation failed: {error}"
    
    # Validate project description
    valid, error = validate_project_description(project_desc)
    if not valid:
        return False, f"Project description validation failed: {error}"
    
    # Validate style
    valid, error = validate_style(style)
    if not valid:
        return False, f"Style validation failed: {error}"
    
    return True, ""


__all__ = [
    "validate_repository_url",
    "validate_project_description",
    "validate_goal",
    "validate_style",
    "validate_comprehensive_submission",
]