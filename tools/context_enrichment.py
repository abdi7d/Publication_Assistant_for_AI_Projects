# tools/context_enrichment.py
"""
Context Enrichment Tool for gathering external repository context.
Fetches GitHub context, analyzes dependencies, and enriches repository analysis.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import logging
import re
import requests
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class GitHubContext:
    """Context gathered from GitHub repository."""
    stars: int
    forks: int
    open_issues: int
    contributors: List[str]
    recent_commits: List[Dict[str, str]]
    pull_request_patterns: List[str]
    issue_discussions: List[str]
    release_history: List[Dict[str, str]]
    community_signals: Dict[str, Any]
    activity_level: str


@dataclass
class DependencyAnalysis:
    """Analysis of project dependencies."""
    core_dependencies: List[str]
    development_dependencies: List[str]
    outdated_packages: List[str]
    security_vulnerabilities: List[str]
    dependency_categories: Dict[str, List[str]]
    ecosystem_mapping: Dict[str, List[str]]
    version_conflicts: List[str]


@dataclass
class EnrichedContext:
    """Enriched context for repository analysis."""
    github_context: Optional[GitHubContext]
    dependency_analysis: DependencyAnalysis
    technology_trends: Dict[str, str]
    best_practices_alignment: Dict[str, Any]
    competitive_landscape: List[str]


class ContextEnrichmentTool:
    """
    Enrich repository analysis with external context.
    Fetches GitHub data, analyzes dependencies, and provides
    additional context for intelligent documentation generation.
    """

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.session = requests.Session()
        if github_token:
            self.session.headers.update({"Authorization": f"token {github_token}"})

    def enrich_repository(self, repo_url: str, dependencies: List[str], files: Dict[str, str]) -> EnrichedContext:
        """Enrich repository analysis with external context."""
        logger.info("ContextEnrichmentTool: enriching repository context for %s", repo_url)
        
        # Extract GitHub context if available
        github_context = self._fetch_github_context(repo_url) if self._is_github_url(repo_url) else None
        
        # Analyze dependencies
        dependency_analysis = self._analyze_dependencies(dependencies)
        
        # Analyze technology trends
        technology_trends = self._analyze_technology_trends(dependencies, files)
        
        # Check best practices alignment
        best_practices_alignment = self._check_best_practices(files)
        
        # Analyze competitive landscape
        competitive_landscape = self._analyze_competitive_landscape(dependencies)
        
        return EnrichedContext(
            github_context=github_context,
            dependency_analysis=dependency_analysis,
            technology_trends=technology_trends,
            best_practices_alignment=best_practices_alignment,
            competitive_landscape=competitive_landscape,
        )

    def _is_github_url(self, repo_url: str) -> bool:
        """Check if URL is a GitHub repository."""
        return "github.com" in repo_url.lower()

    def _fetch_github_context(self, repo_url: str) -> Optional[GitHubContext]:
        """Fetch context from GitHub API."""
        try:
            # Extract owner/repo from URL
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
            if not match:
                return None
            
            owner, repo = match.groups()
            repo = repo.replace('.git', '')
            
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code != 200:
                logger.warning("GitHub API request failed: %s", response.status_code)
                return None
            
            data = response.json()
            
            # Fetch additional context
            contributors = self._fetch_contributors(owner, repo)
            commits = self._fetch_recent_commits(owner, repo)
            issues = self._fetch_issues(owner, repo)
            releases = self._fetch_releases(owner, repo)
            
            # Analyze activity level
            activity_level = self._calculate_activity_level(data, commits)
            
            return GitHubContext(
                stars=data.get('stargazers_count', 0),
                forks=data.get('forks_count', 0),
                open_issues=data.get('open_issues_count', 0),
                contributors=contributors[:10],  # Limit to top 10
                recent_commits=commits[:5],  # Limit to recent 5
                pull_request_patterns=self._analyze_pr_patterns(issues),
                issue_discussions=self._extract_issue_topics(issues),
                release_history=releases,
                community_signals={
                    "has_wiki": data.get('has_wiki', False),
                    "has_pages": data.get('has_pages', False),
                    "has_downloads": data.get('has_downloads', False),
                    "license": data.get('license', {}).get('name') if data.get('license') else None,
                },
                activity_level=activity_level,
            )
            
        except Exception as e:
            logger.warning("Failed to fetch GitHub context: %s", e)
            return None

    def _fetch_contributors(self, owner: str, repo: str) -> List[str]:
        """Fetch repository contributors."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return [contributor.get('login', '') for contributor in response.json()[:20]]
        except Exception as e:
            logger.warning("Failed to fetch contributors: %s", e)
        return []

    def _fetch_recent_commits(self, owner: str, repo: str) -> List[Dict[str, str]]:
        """Fetch recent commits."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                commits = []
                for commit in response.json()[:10]:
                    commits.append({
                        "sha": commit.get('sha', '')[:7],
                        "message": commit.get('commit', {}).get('message', ''),
                        "author": commit.get('author', {}).get('login', ''),
                        "date": commit.get('commit', {}).get('author', {}).get('date', ''),
                    })
                return commits
        except Exception as e:
            logger.warning("Failed to fetch commits: %s", e)
        return []

    def _fetch_issues(self, owner: str, repo: str) -> List[Dict[str, str]]:
        """Fetch recent issues and pull requests."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                issues = []
                for issue in response.json()[:15]:
                    issues.append({
                        "title": issue.get('title', ''),
                        "state": issue.get('state', ''),
                        "number": issue.get('number', 0),
                        "created_at": issue.get('created_at', ''),
                        "is_pull_request": 'pull_request' in issue,
                    })
                return issues
        except Exception as e:
            logger.warning("Failed to fetch issues: %s", e)
        return []

    def _fetch_releases(self, owner: str, repo: str) -> List[Dict[str, str]]:
        """Fetch release history."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/releases"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                releases = []
                for release in response.json()[:5]:
                    releases.append({
                        "tag_name": release.get('tag_name', ''),
                        "name": release.get('name', ''),
                        "published_at": release.get('published_at', ''),
                        "draft": release.get('draft', False),
                    })
                return releases
        except Exception as e:
            logger.warning("Failed to fetch releases: %s", e)
        return []

    def _calculate_activity_level(self, repo_data: Dict, commits: List[Dict]) -> str:
        """Calculate repository activity level."""
        if not commits:
            return "Low"
        
        # Check recency of commits
        from datetime import datetime, timedelta
        now = datetime.now()
        recent_commits = [c for c in commits if datetime.fromisoformat(c['date'].replace('Z', '+00:00')) > now - timedelta(days=30)]
        
        if len(recent_commits) >= 5:
            return "High"
        elif len(recent_commits) >= 2:
            return "Medium"
        else:
            return "Low"

    def _analyze_pr_patterns(self, issues: List[Dict]) -> List[str]:
        """Analyze pull request patterns."""
        prs = [issue for issue in issues if issue.get('is_pull_request')]
        patterns = []
        
        for pr in prs:
            title = pr.get('title', '').lower()
            if 'fix' in title or 'bug' in title:
                patterns.append("Bug fixes")
            if 'feature' in title or 'add' in title:
                patterns.append("Feature additions")
            if 'refactor' in title or 'clean' in title:
                patterns.append("Refactoring")
            if 'doc' in title or 'readme' in title:
                patterns.append("Documentation updates")
        
        return list(set(patterns))

    def _extract_issue_topics(self, issues: List[Dict]) -> List[str]:
        """Extract common topics from issue discussions."""
        topics = []
        for issue in issues[:10]:
            title = issue.get('title', '')
            # Simple keyword extraction
            words = re.findall(r'\b\w+\b', title.lower())
            meaningful_words = [w for w in words if len(w) > 3 and w not in {'the', 'and', 'for', 'with', 'from', 'that', 'this'}]
            topics.extend(meaningful_words[:3])
        
        # Return most common topics
        topic_counts = Counter(topics)
        return [topic for topic, count in topic_counts.most_common(5)]

    def _analyze_dependencies(self, dependencies: List[str]) -> DependencyAnalysis:
        """Analyze project dependencies."""
        # Categorize dependencies
        core_deps = []
        dev_deps = []
        
        for dep in dependencies:
            dep_lower = dep.lower()
            if any(test in dep_lower for test in ['pytest', 'test', 'coverage', 'lint', 'black', 'flake']):
                dev_deps.append(dep)
            else:
                core_deps.append(dep)
        
        # Categorize by purpose
        categories = {
            "web_frameworks": [],
            "data_processing": [],
            "ai_ml": [],
            "database": [],
            "utilities": [],
            "security": [],
        }
        
        for dep in core_deps:
            dep_lower = dep.lower()
            if any(fw in dep_lower for fw in ['fastapi', 'flask', 'django', 'starlette']):
                categories["web_frameworks"].append(dep)
            elif any(dp in dep_lower for dp in ['pandas', 'numpy', 'polars']):
                categories["data_processing"].append(dep)
            elif any(ai in dep_lower for ai in ['torch', 'tensorflow', 'langchain', 'transformers', 'openai']):
                categories["ai_ml"].append(dep)
            elif any(db in dep_lower for db in ['sqlalchemy', 'psycopg', 'pymongo', 'redis']):
                categories["database"].append(dep)
            elif any(sec in dep_lower for sec in ['cryptography', 'jwt', 'oauth', 'auth']):
                categories["security"].append(dep)
            else:
                categories["utilities"].append(dep)
        
        # Map ecosystem
        ecosystem_mapping = {}
        for dep in core_deps:
            if 'langchain' in dep.lower():
                ecosystem_mapping.setdefault("LangChain Ecosystem", []).append(dep)
            elif 'fastapi' in dep.lower():
                ecosystem_mapping.setdefault("FastAPI Ecosystem", []).append(dep)
            elif 'aws' in dep.lower():
                ecosystem_mapping.setdefault("AWS", []).append(dep)
        
        return DependencyAnalysis(
            core_dependencies=core_deps,
            development_dependencies=dev_deps,
            outdated_packages=[],  # Would require external API
            security_vulnerabilities=[],  # Would require security advisory API
            dependency_categories=categories,
            ecosystem_mapping=ecosystem_mapping,
            version_conflicts=[],  # Would require version analysis
        )

    def _analyze_technology_trends(self, dependencies: List[str], files: Dict[str, str]) -> Dict[str, str]:
        """Analyze technology trends and modernization."""
        trends = {}
        
        # Check for modern Python patterns
        py_content = "\n".join([c for f, c in files.items() if f.endswith('.py')])
        
        if 'async def' in py_content:
            trends["async_patterns"] = "Modern async/await patterns detected"
        if 'typing' in py_content:
            trends["type_hints"] = "Type hints extensively used"
        if 'dataclass' in py_content:
            trends["dataclasses"] = "Modern dataclass patterns present"
        if 'contextlib' in py_content:
            trends["context_managers"] = "Context manager patterns used"
        
        # Check framework trends
        if any('fastapi' in dep.lower() for dep in dependencies):
            trends["web_framework"] = "Modern async web framework (FastAPI)"
        if any('langchain' in dep.lower() or 'langgraph' in dep.lower() for dep in dependencies):
            trends["ai_framework"] = "Cutting-edge AI framework stack"
        
        return trends

    def _check_best_practices(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Check alignment with development best practices."""
        alignment = {
            "has_tests": False,
            "has_ci_cd": False,
            "has_documentation": False,
            "has_linting": False,
            "has_type_hints": False,
            "has_security": False,
            "has_licensing": False,
        }
        
        # Check for tests
        if any('test' in f.lower() for f in files.keys()):
            alignment["has_tests"] = True
        
        # Check for CI/CD
        if any('.github' in f or 'workflow' in f.lower() or 'ci' in f.lower() for f in files.keys()):
            alignment["has_ci_cd"] = True
        
        # Check for documentation
        if any('readme' in f.lower() or 'doc' in f.lower() for f in files.keys()):
            alignment["has_documentation"] = True
        
        # Check for linting configuration
        if any(cfg in f.lower() for f in files.keys() for cfg in ['.flake8', '.pylintrc', 'black.toml', 'pyproject.toml']):
            alignment["has_linting"] = True
        
        # Check for type hints
        py_content = "\n".join([c for f, c in files.items() if f.endswith('.py')])
        if 'typing' in py_content or 'from typing import' in py_content:
            alignment["has_type_hints"] = True
        
        # Check for security practices
        if any('auth' in f.lower() or 'security' in f.lower() for f in files.keys()):
            alignment["has_security"] = True
        
        # Check for licensing
        if any('license' in f.lower() for f in files.keys()):
            alignment["has_licensing"] = True
        
        # Calculate overall score
        score = sum(alignment.values()) / len(alignment) * 100
        alignment["overall_score"] = score
        
        return alignment

    def _analyze_competitive_landscape(self, dependencies: List[str]) -> List[str]:
        """Analyze competitive landscape based on technology stack."""
        landscape = []
        
        # Identify the technology domain
        if any('langchain' in dep.lower() or 'langgraph' in dep.lower() for dep in dependencies):
            landscape.extend([
                "LangChain ecosystem",
                "Multi-agent AI frameworks",
                "LLM application development",
            ])
        
        if any('fastapi' in dep.lower() for dep in dependencies):
            landscape.extend([
                "Modern Python web frameworks",
                "API development",
                "Async Python ecosystem",
            ])
        
        if any('torch' in dep.lower() or 'tensorflow' in dep.lower() for dep in dependencies):
            landscape.extend([
                "Deep learning frameworks",
                "ML model deployment",
                "AI/ML research tools",
            ])
        
        return list(set(landscape))


__all__ = [
    "ContextEnrichmentTool",
    "EnrichedContext",
    "GitHubContext",
    "DependencyAnalysis",
]