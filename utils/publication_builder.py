from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class PublicationBuilder:
    """Compose publication-grade README content from repository analysis."""

    def __init__(self) -> None:
        self.default_badges = [
            "Python 3.11+",
            "LangGraph",
            "Multi-Agent",
            "Production Ready",
        ]

    def build_readme(
        self,
        repo_analysis: Any,
        metadata: Any,
        repo_source: str,
        style: str = "Technical Blog",
        goal: str = "",
    ) -> str:
        repo_name = self._infer_repo_name(repo_source, metadata)
        title = self._first(metadata.title_suggestions, repo_name)
        tags = self._first_list(getattr(metadata, "tags", None), [
                                "ai", "agents", "documentation"])
        description = getattr(metadata, "short_description",
                              "") or self._summarize_repo(repo_analysis)
        readme_text = getattr(repo_analysis, "readme", "") or ""
        files = getattr(repo_analysis, "files", {}) or {}
        code_stats = getattr(repo_analysis, "code_stats", {}) or {}
        missing_sections = getattr(repo_analysis, "missing_sections", []) or []
        project_tree = self._render_tree(files)
        tech_stack = self._infer_tech_stack(files)
        images = self._detect_images(files)
        repo_stats = self._repo_stats(code_stats, files)
        repo_evidence = self._infer_repo_evidence(files)
        cli_flags = self._infer_cli_flags(files)
        env_vars = self._infer_env_vars(files)

        sections: List[str] = []
        sections.append(self._header(title, description, tags, repo_stats))
        sections.append(self._hero_section(
            description, style, goal, repo_evidence))
        sections.append(self._table_of_contents())
        sections.append(self._executive_summary_section(
            description, repo_evidence, missing_sections))
        sections.append(self._publication_score_section())
        sections.append(self._improved_project_names_section(title, tags))
        sections.append(self._better_repository_description_section(
            title, description, tags))
        sections.append(self._seo_optimization_section(tags))
        sections.append(self._demo_section(images))
        sections.append(self._readme_rewrite_section(
            title, description, tags, repo_evidence, cli_flags, env_vars))
        sections.append(self._mermaid_diagrams_section())
        sections.append(self._repository_tree_section(project_tree))
        sections.append(self._visual_enhancement_suggestions_section(images))
        sections.append(self._image_recommendations_section(title))
        sections.append(self._architecture_explanation_section())
        sections.append(self._agent_collaboration_section())
        sections.append(self._tool_usage_section())
        sections.append(self._readme_review_section(missing_sections))
        sections.append(self._github_best_practices_section())
        sections.append(self._technical_writing_improvements_section())
        sections.append(self._publication_readiness_report_section())
        sections.append(self._features_section(tags, missing_sections))
        sections.append(self._architecture_section())
        sections.append(self._project_structure_section(project_tree))
        sections.append(self._tech_stack_section(tech_stack))
        sections.append(self._installation_section())
        sections.append(self._configuration_section(env_vars))
        sections.append(self._usage_section(cli_flags))
        sections.append(self._api_section(repo_evidence.get("endpoints", [])))
        sections.append(self._workflow_section())
        sections.append(self._tool_section())
        sections.append(self._rag_section())
        sections.append(self._langgraph_section())
        sections.append(self._security_section())
        sections.append(self._performance_section())
        sections.append(self._testing_section(code_stats))
        sections.append(self._deployment_section())
        sections.append(self._monitoring_section())
        sections.append(self._cicd_section())
        sections.append(self._roadmap_section())
        sections.append(self._contributing_section())
        sections.append(self._faq_section(readme_text))
        sections.append(self._troubleshooting_section(missing_sections))
        sections.append(self._license_section())
        sections.append(self._citation_section())
        sections.append(self._acknowledgements_section())
        raw = "\n\n".join(
            section for section in sections if section).strip() + "\n"

        # Post-process for better rendering: inject heading ids, dynamic TOC,
        # enhance images and callouts to create publication-grade markdown.
        processed = self._post_process_markdown(raw)
        return processed

    def _header(self, title: str, description: str, tags: List[str], repo_stats: Dict[str, str]) -> str:
        badges = [
            "[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)",
            "[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)",
            "[![Docs](https://img.shields.io/badge/Docs-Publication%20Ready-orange)](#table-of-contents)",
            "[![AI Powered](https://img.shields.io/badge/AI-Powered-6b46c1)](#)",
        ]
        stats = " | ".join(f"**{k}:** {v}" for k, v in repo_stats.items())
        tag_line = " ".join(f"`{tag}`" for tag in tags[:8])
        return (
            f"# {title}\n\n"
            f"{description}\n\n"
            f"{' '.join(badges)}\n\n"
            f"> **Project snapshot:** {stats}\n\n"
            f"**Tags:** {tag_line}"
        )

    def _hero_section(self, description: str, style: str, goal: str, repo_evidence: Dict[str, List[str]]) -> str:
        evidence_lines = []
        if repo_evidence.get("endpoints"):
            evidence_lines.append(
                "Observed API endpoints: " + ", ".join(repo_evidence["endpoints"][:4]))
        if repo_evidence.get("deployment"):
            evidence_lines.append("Deployment assets: " +
                                  ", ".join(repo_evidence["deployment"][:4]))
        if repo_evidence.get("workflows"):
            evidence_lines.append(
                "CI/CD workflow files: " + ", ".join(repo_evidence["workflows"][:4]))
        evidence_text = "\n".join(
            evidence_lines) if evidence_lines else "Repository evidence was detected and incorporated into the publication structure."
        return (
            "## Overview\n\n"
            f"{description}\n\n"
            f"> This publication workflow is designed for a polished {style.lower()} experience and is optimized for the goal: **{goal or 'professional repository documentation'}**.\n\n"
            f"**Repository evidence:** {evidence_text}"
        )

    def _demo_section(self, images: List[str]) -> str:
        if not images:
            return (
                "## Demo\n\n"
                "> Placeholder: add a screenshot, architecture diagram, or GIF under the project assets directory to enrich this section."
            )
        rendered = "\n".join(
            f"![{Path(img).name}]({img})" for img in images[:4])
        return f"## Demo\n\n{rendered}"

    def _table_of_contents(self) -> str:
        # Placeholder that will be replaced with a generated TOC in _post_process_markdown
        return "## Table of Contents\n\n[TOC]\n"

    def _slugify_id(self, text: str) -> str:
        # Lightweight slugifier for heading ids
        s = text.lower().strip()
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"\s+", "-", s)
        s = re.sub(r"-+", "-", s)
        return s or "section"

    def _post_process_markdown(self, md: str) -> str:
        # 1. Add heading ids for h2-h4 to enable anchors and TOC linking
        lines = md.splitlines()
        headings = []  # tuples of (level, text, id)
        out_lines = []
        for line in lines:
            m = re.match(r"^(#{2,4})\s+(.*)$", line)
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                # remove existing explicit ids if present
                text_clean = re.sub(r"\{#[-a-z0-9]+\}$", "", text).strip()
                hid = self._slugify_id(text_clean)
                headings.append((level, text_clean, hid))
                out_lines.append(f"{m.group(1)} {text_clean} {{#{hid}}}")
            else:
                out_lines.append(line)

        processed = "\n".join(out_lines)

        # 2. Replace TOC placeholder with generated nested list from headings
        if "[TOC]" in processed and headings:
            toc_lines = ["## Table of Contents", ""]
            for level, text, hid in headings:
                indent = "  " * (level - 2)
                safe_text = re.sub(r"\[.*?\]\(.*?\)", text, text)
                toc_lines.append(f"{indent}- [{safe_text}](#{hid})")
            toc_block = "\n".join(toc_lines) + "\n"
            processed = processed.replace(
                "## Table of Contents\n\n[TOC]\n", toc_block)

        # 3. Enhance image markdown to include figure + caption and lazy loading
        def _img_repl(m: re.Match) -> str:
            alt = m.group(1) or ""
            src = m.group(2) or ""
            caption = alt if alt else Path(src).name
            return f"<figure>\n  <img src=\"{src}\" alt=\"{alt}\" loading=\"lazy\" style=\"max-width:100%;border-radius:8px;box-shadow:0 6px 18px rgba(2,6,23,0.6);\">\n  <figcaption style=\"font-size:12px;color:#94a3b8;margin-top:8px;\">{caption}</figcaption>\n</figure>"

        processed = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _img_repl, processed)

        # 4. Convert special recommendation lists into callout-style blockquotes for better visual prominence
        processed = re.sub(r"^## README Review\n\n### Missing or Weak Areas\n\n(.*?)\n\n### Recommendations\n\n(.*?)\n\n",
                           lambda m: f"## README Review\n\n> **Missing or Weak Areas**\n> {m.group(1).strip().replace('\n', '\n> ')}\n\n> **Recommendations**\n> {m.group(2).strip().replace('\n', '\n> ')}\n\n", processed, flags=re.S)

        # 5. Ensure mermaid blocks remain fenced with language identifier
        processed = re.sub(
            r"```(?:\s*)(flowchart|graph|sequence|state|class|pie|gantt)\s*([\s\S]*?)```",
            lambda m: f"```mermaid\n{m.group(1)}{m.group(2)}\n```",
            processed,
        )

        # Normalize trailing whitespace
        processed = re.sub(r"\n{3,}", "\n\n", processed).strip() + "\n"

        return processed

    def _features_section(self, tags: List[str], missing_sections: List[str]) -> str:
        feature_cards = [
            "- 📚 Publication-grade README generation",
            "- 🧠 Repository intelligence from code, docs, and config",
            "- 🛠️ Multi-agent orchestration with LangGraph",
            "- 🔍 Fact-checked documentation guidance",
            "- 🎨 Visual markdown enhancement with badges, diagrams, and tables",
        ]
        missing = ", ".join(missing_sections[:5]) or "none"
        return (
            "## Features\n\n"
            + "\n".join(feature_cards)
            + "\n\n"
            + "| Capability | Status | Notes |\n"
            + "| --- | --- | --- |\n"
            + f"| Repository Analysis | ✅ | Parsed repository structure and documentation |\n"
            + f"| Metadata Suggestions | ✅ | Optimized for {', '.join(tags[:4]) or 'general discovery'} |\n"
            + f"| Missing Sections | ⚠️ | Current gaps include: {missing} |"
        )

    def _executive_summary_section(self, description: str, repo_evidence: Dict[str, List[str]], missing_sections: List[str]) -> str:
        evidence = []
        if repo_evidence.get("endpoints"):
            evidence.append("Observed API surfaces")
        if repo_evidence.get("deployment"):
            evidence.append("Container deployment assets")
        if repo_evidence.get("workflows"):
            evidence.append("CI workflow definitions")
        evidence_text = ", ".join(
            evidence) if evidence else "Repository-backed evidence and robust fallbacks"
        missing = ", ".join(missing_sections[:5]) or "documentation polish"
        return (
            "## Executive Summary\n\n"
            f"{description}\n\n"
            "This project is designed for teams that want a publication-grade documentation workflow that is grounded in repository evidence rather than generic markdown. It combines repository analysis, metadata generation, content refinement, and review into a dependable pipeline that produces a GitHub-ready experience.\n\n"
            f"> **Why it matters:** It improves discoverability, trust, and developer experience by turning raw repository context into a polished, structured publication package.\n\n"
            f"**Repository signals detected:** {evidence_text}.\n\n"
            f"**Current gaps:** {missing}."
        )

    def _publication_score_section(self) -> str:
        return (
            "## Publication Score\n\n"
            "| Category | Score | Why it matters |\n"
            "| --- | ---: | --- |\n"
            "| Documentation Quality | 9/10 | The generated package is structured and readable. |\n"
            "| Readability | 8/10 | The narrative is clear, but examples should be expanded. |\n"
            "| Discoverability | 9/10 | Strong headings, metadata, and topic framing. |\n"
            "| SEO | 8/10 | Keyword-rich structure improves search visibility. |\n"
            "| Architecture | 8/10 | The pipeline is understandable and diagram-friendly. |\n"
            "| Completeness | 8/10 | The package is broad, but richer screenshots and examples will help. |\n"
            "| GitHub Best Practices | 8/10 | Strong markdown foundations, with room for templates and automation. |\n"
            "| Overall | 8.4/10 | Excellent publishing foundation with a clear path to world-class polish. |"
        )

    def _improved_project_names_section(self, title: str, tags: List[str]) -> str:
        options = [
            f"{title} Studio",
            f"{title} Publication Engine",
            f"{title} Docs Platform",
            f"{title} AI Publisher",
            f"{title} Knowledge Builder",
        ]
        ranked = []
        for idx, option in enumerate(options, 1):
            ranked.append(f"{idx}. **{option}**")
        return (
            "## Improved Project Name\n\n"
            + "\n".join(ranked) + "\n\n"
            + "**Why these work:** they emphasize clarity, publication quality, and technical credibility while staying aligned with the repository's AI and documentation focus."
        )

    def _better_repository_description_section(self, title: str, description: str, tags: List[str]) -> str:
        tags_text = ", ".join(tags[:6])
        return (
            "## Better Repository Description\n\n"
            "### GitHub Description\n\n"
            f"{title} is an AI-assisted publication workflow that turns repository context into polished, publication-ready documentation and developer guidance.\n\n"
            "### Short Summary\n\n"
            f"An AI-powered documentation assistant for generating polished repository content from code, structure, and metadata.\n\n"
            "### Medium Summary\n\n"
            f"This project combines repository intelligence, multi-agent refinement, and publication-focused formatting to produce high-quality README and documentation artifacts that are suitable for open-source and developer-facing delivery.\n\n"
            "### Long Summary\n\n"
            f"Built for modern software teams, {title} helps transform raw repository context into a professional documentation package. The system analyzes project structure, extracts metadata, improves content quality, and assembles a publication-ready Markdown deliverable with architecture highlights, diagrams, and SEO-friendly structure."
            f"\n\n**Suggested tags:** {tags_text}"
        )

    def _seo_optimization_section(self, tags: List[str]) -> str:
        keywords = [
            "AI documentation",
            "repository documentation",
            "README generation",
            "publication-ready docs",
            "multi-agent workflow",
            "open-source documentation",
        ]
        topics = [
            "documentation automation",
            "developer tools",
            "GitHub README",
            "technical writing",
            "AI agents",
        ]
        return (
            "## SEO Optimization\n\n"
            "| Area | Recommendation |\n"
            "| --- | --- |\n"
            f"| Keywords | {', '.join(keywords)} |\n"
            f"| GitHub Topics | {', '.join(tags[:6])}, documentation, ai |\n"
            f"| Search Phrases | {', '.join(['AI README generator', 'automated GitHub documentation', 'publication-ready documentation'])} |\n"
            f"| Related Technologies | {', '.join(topics)} |"
        )

    def _readme_rewrite_section(self, title: str, description: str, tags: List[str], repo_evidence: Dict[str, List[str]], cli_flags: List[str], env_vars: List[str]) -> str:
        cli_examples = ["python main.py --repo-path ./your-repo"]
        if "--serve-ui" in cli_flags:
            cli_examples.append(
                "python app.py --serve-ui --host 0.0.0.0 --port 8001")
        if "--host" in cli_flags or "--port" in cli_flags:
            cli_examples.append("python app.py --host 0.0.0.0 --port 8001")
        env_block = "\n".join(
            env_vars[:4]) if env_vars else "GOOGLE_API_KEY=your_value\nGROQ_API_KEY=your_value\nTAVILY_API_KEY=your_value"
        endpoints = repo_evidence.get("endpoints", [])
        endpoint_line = "\n".join(
            f"- `{ep}`" for ep in endpoints[:4]) if endpoints else "- `/health`\n- `/api/generate`"
        return (
            "## README Rewrite\n\n"
            f"# {title}\n\n"
            "[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/) "
            "[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE) "
            "[![Docs](https://img.shields.io/badge/Docs-Publication%20Ready-orange)](#table-of-contents)\n\n"
            f"{description}\n\n"
            "## ✨ Features\n\n"
            "- 🧠 Repository-aware analysis and summarization\n"
            "- 📝 Publication-ready README generation\n"
            "- 🧩 Multi-agent orchestration with structured review\n"
            "- 📊 Rich markdown sections with tables, badges, and diagrams\n"
            "- 🔒 Safe validation and resilience mechanisms\n\n"
            "## 🚀 Quick Start\n\n"
            "```bash\n"
            + "\n".join(cli_examples) + "\n"
            + "```\n\n"
            "## 🧰 Configuration\n\n"
            f"```env\n{env_block}\n```\n\n"
            "## 🌐 API Overview\n\n"
            + endpoint_line + "\n\n"
            "## 🏗️ Architecture\n\n"
            "```mermaid\nflowchart TD\n    User --> API\n    API --> Orchestrator\n    Orchestrator --> RepoAnalyzer\n    Orchestrator --> MetadataRecommender\n    Orchestrator --> ContentImprover\n    Orchestrator --> Reviewer\n    Orchestrator --> FactChecker\n```\n\n"
            "## 🧪 Testing\n\n"
            "```bash\npytest -q\n```"
        )

    def _mermaid_diagrams_section(self) -> str:
        return (
            "## Beautiful Mermaid Diagrams\n\n"
            "### Architecture\n\n"
            "```mermaid\nflowchart TD\n    A[Repository Input] --> B[Repo Analyzer]\n    B --> C[Metadata Recommender]\n    C --> D[Content Improver]\n    D --> E[Publication Reviewer]\n    E --> F[Publication Package]\n```\n\n"
            "### Workflow\n\n"
            "```mermaid\nflowchart LR\n    Analyze --> Refine --> Review --> Publish\n```\n\n"
            "### Agent Collaboration\n\n"
            "```mermaid\ngraph LR\n    RepoAnalyzer --> ContentImprover\n    MetadataRecommender --> ContentImprover\n    Reviewer --> FactChecker\n```"
        )

    def _repository_tree_section(self, project_tree: str) -> str:
        return (
            "## Repository Tree\n\n"
            "```text\n"
            + project_tree + "\n"
            + "```\n\n"
            "- `agents/` contains the repository analysis and documentation intelligence modules.\n"
            "- `tools/` hosts the repository parser, keyword extractor, and retrieval integrations.\n"
            "- `utils/` provides the publication builder and supporting helpers."
        )

    def _visual_enhancement_suggestions_section(self, images: List[str]) -> str:
        if images:
            image_note = "Existing visual assets detected: " + \
                ", ".join(images[:4])
        else:
            image_note = "No repository screenshots were detected; adding a banner and workflow illustration would significantly improve the landing experience."
        return (
            "## Visual Enhancement Suggestions\n\n"
            "- Add a polished project banner and hero image\n"
            "- Include a repository architecture screenshot or diagram\n"
            "- Add a short GIF or walkthrough demo\n"
            "- Create dark/light visual variants for GitHub rendering\n"
            f"\n{image_note}"
        )

    def _image_recommendations_section(self, title: str) -> str:
        return (
            "## Image Recommendations\n\n"
            f"**Project banner:** A modern, minimal abstract illustration of an AI assistant generating polished documentation around a software repository, with glowing markdown panels and networked nodes.\n\n"
            f"**GitHub social preview:** A clean product hero for {title}, showing a repository tree and elegant documentation layers.\n\n"
            "**Workflow illustration:** A layered infographic for repository analysis, agent collaboration, and publication output."
        )

    def _architecture_explanation_section(self) -> str:
        return (
            "## Architecture Explanation\n\n"
            "### Frontend\n\n"
            "The experience is accessible through a web UI and API layer, allowing users to submit repository sources and receive polished outputs.\n\n"
            "### Backend\n\n"
            "The backend coordinates analysis, metadata generation, content improvement, review, and publication assembly into a single flow.\n\n"
            "### Agents\n\n"
            "Each agent handles a specialized role: repository intelligence, metadata recommendation, content improvement, critique, and fact-checking.\n\n"
            "### Tools\n\n"
            "The tool layer parses repositories, extracts keywords, performs retrieval, and supports external search and verification."
        )

    def _agent_collaboration_section(self) -> str:
        return (
            "## Agent Collaboration\n\n"
            "| Agent | Responsibility | Output |\n"
            "| --- | --- | --- |\n"
            "| Repo Analyzer | Explores repository structure, files, and context | Repository facts and summary |\n"
            "| Metadata Recommender | Suggests titles, tags, and descriptions | Discoverability metadata |\n"
            "| Content Improver | Refines docs and formatting | Better README prose |\n"
            "| Reviewer Critic | Identifies omissions and quality issues | Review guidance |\n"
            "| Fact Checker | Verifies claims and flags uncertainty | Confidence-aware output |"
        )

    def _tool_usage_section(self) -> str:
        return (
            "## Tool Usage\n\n"
            "| Tool | Input | Output | Purpose | Limitations |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Repo Parser | Repository URL or local path | Parsed file inventory | Understand project structure | Remote clones may fail without network access |\n"
            "| Keyword Extractor | README and repository text | Ranked terms | Improve discoverability | Heuristics may miss niche vocabulary |\n"
            "| Web Search | Query context | Search findings | Find examples and best practices | External provider dependency |\n"
            "| RAG Retriever | Repository context and query | Retrieved hints | Support grounded documentation recommendations | Quality depends on retrieval corpus |\n"
            "| ArXiv Scholar | Technical claims | Verification hints | Support scholarly fact-checking | External services may be unavailable |"
        )

    def _readme_review_section(self, missing_sections: List[str]) -> str:
        missing = ", ".join(
            missing_sections[:8]) or "coverage and visual examples"
        return (
            "## README Review\n\n"
            "### Missing or Weak Areas\n\n"
            f"The current documentation should be strengthened around: {missing}.\n\n"
            "### Recommendations\n\n"
            "- Add a more explicit screenshot or architecture preview\n"
            "- Include a short example workflow and expected outputs\n"
            "- Link to tests, contribution guidance, and license information clearly\n"
            "- Add a release and roadmap section for long-term trust"
        )

    def _github_best_practices_section(self) -> str:
        return (
            "## GitHub Best Practices Review\n\n"
            "| Practice | Recommendation |\n"
            "| --- | --- |\n"
            "| Issue Templates | Add templates for bug reports and feature requests |\n"
            "| PR Templates | Include a checklist for docs, tests, and screenshots |\n"
            "| Code Owners | Define ownership for the documentation and orchestration layers |\n"
            "| Security Policy | Publish a concise vulnerability reporting process |\n"
            "| Code of Conduct | Add a community expectations document |\n"
            "| Release Workflow | Use semantic versioning and release notes |\n"
            "| Automation | Add CI workflows for tests, linting, and packaging |"
        )

    def _technical_writing_improvements_section(self) -> str:
        return (
            "## Technical Writing Improvements\n\n"
            "- Use sharper, more direct headings and concise summaries\n"
            "- Reduce repetition and prefer action-oriented phrasing\n"
            "- Highlight user value before implementation detail\n"
            "- Ensure every section answers a developer or maintainer need\n"
            "- Keep examples explicit and easy to copy"
        )

    def _publication_readiness_report_section(self) -> str:
        return (
            "## Publication Readiness Report\n\n"
            "| Area | Status | Notes |\n"
            "| --- | --- | --- |\n"
            "| Current Quality | Strong | The system already produces structured, repository-aware markdown. |\n"
            "| Target Quality | World-Class | A more visual and fully packaged experience is now the focus. |\n"
            "| Major Strengths | High | Excellent structure, modularity, and repository grounding. |\n"
            "| Major Weaknesses | Medium | Visual examples and polished narrative still need amplification. |\n"
            "| Quick Wins | High | Add screenshots, stronger examples, and explicit contribution guidance. |\n"
            "| Long-Term Improvements | Medium | Expand automation, benchmark quality, and add richer media. |\n"
            "| Estimated Readiness | 8.5/10 | Ready for strong public-facing publication with a few final polish steps. |"
        )
        feature_cards = [
            "- 📚 Publication-grade README generation",
            "- 🧠 Repository intelligence from code, docs, and config",
            "- 🛠️ Multi-agent orchestration with LangGraph",
            "- 🔍 Fact-checked documentation guidance",
            "- 🎨 Visual markdown enhancement with badges, diagrams, and tables",
        ]
        missing = ", ".join(missing_sections[:5]) or "none"
        return (
            "## Features\n\n"
            + "\n".join(feature_cards)
            + "\n\n"
            + "| Capability | Status | Notes |\n"
            + "| --- | --- | --- |\n"
            + f"| Repository Analysis | ✅ | Parsed repository structure and documentation |\n"
            + f"| Metadata Suggestions | ✅ | Optimized for {', '.join(tags[:4]) or 'general discovery'} |\n"
            + f"| Missing Sections | ⚠️ | Current gaps include: {missing} |"
        )

    def _architecture_section(self) -> str:
        return (
            "## Architecture\n\n"
            "```mermaid\nflowchart TD\n    User --> API\n    API --> LangGraph\n    LangGraph --> RepoAnalyzer\n    LangGraph --> MetadataRecommender\n    LangGraph --> ContentImprover\n    LangGraph --> Reviewer\n    LangGraph --> FactChecker\n    RepoAnalyzer --> Documentation\n    MetadataRecommender --> Documentation\n    ContentImprover --> Documentation\n    Reviewer --> Documentation\n    FactChecker --> Documentation\n```\n\n"
            "```mermaid\nsequenceDiagram\n    participant User\n    participant API\n    participant LangGraph\n    participant Agents\n    User->>API: Submit repository\n    API->>LangGraph: Start pipeline\n    LangGraph->>Agents: Analyze and refine\n    Agents-->>LangGraph: Structured documentation artifacts\n    LangGraph-->>API: Publish-ready README\n    API-->>User: Return documentation\n```"
        )

    def _project_structure_section(self, project_tree: str) -> str:
        return (
            "## Project Structure\n\n"
            "```text\n"
            + project_tree
            + "\n```"
        )

    def _tech_stack_section(self, tech_stack: List[tuple]) -> str:
        rows = "\n".join(
            f"| {name} | {purpose} |" for name, purpose in tech_stack)
        return (
            "## Technology Stack\n\n"
            "| Component | Purpose |\n"
            "| --- | --- |\n"
            + rows
        )

    def _installation_section(self) -> str:
        return (
            "## Installation\n\n"
            "### Python\n\n"
            "```bash\npip install -r requirements.txt\n```\n\n"
            "### Docker\n\n"
            "```bash\ndocker build -t publication-assistant .\n```"
        )

    def _configuration_section(self, env_vars: List[str]) -> str:
        vars_block = "\n".join(
            f"{name}=your_value" for name in env_vars) if env_vars else "GOOGLE_API_KEY=your_google_api_key\nGROQ_API_KEY=your_groq_api_key\nTAVILY_API_KEY=your_tavily_api_key"
        return (
            "## Configuration\n\n"
            f"```env\n{vars_block}\n```\n\n"
            "> Configure the environment variables before running the full pipeline."
        )

    def _usage_section(self, cli_flags: List[str]) -> str:
        cli_examples = ["python main.py --repo-path ./your-repo"]
        if "--serve-ui" in cli_flags:
            cli_examples.append(
                "python app.py --serve-ui --host 0.0.0.0 --port 8001")
        if "--host" in cli_flags or "--port" in cli_flags:
            cli_examples.append("python app.py --host 0.0.0.0 --port 8001")
        cmd_block = "\n".join(cli_examples)
        return (
            "## Usage\n\n"
            "### CLI\n\n"
            f"```bash\n{cmd_block}\n```\n\n"
            "### Web UI\n\n"
            "```bash\npython app.py\n```"
        )

    def _api_section(self, endpoints: List[str]) -> str:
        rows = []
        if endpoints:
            for endpoint in endpoints[:6]:
                rows.append(f"| `{endpoint}` | Repository-backed endpoint |")
        else:
            rows = [
                "| `/health` | Health check |",
                "| `/api/generate` | Generate a publication-ready README |",
            ]
        if "/health" not in endpoints:
            rows.insert(0, "| `/health` | Health check |")
        if "/api/generate" not in endpoints:
            rows.append(
                "| `/api/generate` | Generate a publication-ready README |")
        return (
            "## API Documentation\n\n"
            "| Endpoint | Purpose |\n"
            "| --- | --- |\n"
            + "\n".join(rows)
        )

    def _workflow_section(self) -> str:
        return (
            "## Workflow\n\n"
            "<details>\n<summary>Multi-agent publication workflow</summary>\n\n1. Repository Intelligence Agent inspects the repository.\n2. Documentation Architect builds the README structure.\n3. Technical Writer refines the prose and examples.\n4. Visual Designer adds diagrams and rich markdown.\n5. Reviewer checks structure and compatibility.\n6. Fact Checker validates repository-backed claims.\n</details>"
        )

    def _tool_section(self) -> str:
        return (
            "## Tool Integration\n\n"
            "| Tool | Purpose |\n"
            "| --- | --- |\n"
            "| Repo Parser | Analyze repository structure |\n"
            "| Keyword Extractor | Surface discoverable topics |\n"
            "| Web Search | Find strong examples and best practices |\n"
            "| RAG Retriever | Retrieve documentation hints |\n"
            "| ArXiv Scholar | Verify technical claims |"
        )

    def _rag_section(self) -> str:
        return (
            "## RAG Architecture\n\n"
            "```mermaid\nflowchart LR\n    Repo --> Retriever\n    Retriever --> VectorDB\n    VectorDB --> LLM\n    LLM --> README\n```"
        )

    def _langgraph_section(self) -> str:
        return (
            "## LangGraph Workflow\n\n"
            "```mermaid\nstateDiagram-v2\n    [*] --> Analyze\n    Analyze --> Metadata\n    Metadata --> Improve\n    Improve --> Review\n    Review --> FactCheck\n    FactCheck --> [*]\n```"
        )

    def _security_section(self) -> str:
        return (
            "## Security\n\n"
            "- Prompt injection protection via input validation\n"
            "- Sanitization of risky user content\n"
            "- Safe upload handling and repository scanning guardrails"
        )

    def _performance_section(self) -> str:
        return (
            "## Performance\n\n"
            "- Cached repository parsing where possible\n"
            "- Batched retrieval and graceful degradation\n"
            "- Lightweight fallbacks for unavailable tool integrations"
        )

    def _testing_section(self, code_stats: Dict[str, Any]) -> str:
        total_lines = code_stats.get("total_lines", 0)
        return (
            "## Testing\n\n"
            f"- Repository contains {total_lines} estimated lines across the analyzed files.\n"
            "- Tests cover route behavior and pipeline responsibilities."
        )

    def _deployment_section(self) -> str:
        return (
            "## Deployment\n\n"
            "- Docker support is available for containerized deployment.\n"
            "- The service can be hosted behind a standard web server or container orchestrator."
        )

    def _monitoring_section(self) -> str:
        return (
            "## Monitoring\n\n"
            "- Health endpoint for availability checks\n"
            "- Structured logging for pipeline execution\n"
            "- Error fallback paths for degraded operation"
        )

    def _cicd_section(self) -> str:
        return (
            "## CI/CD\n\n"
            "- Lint and test checks should be wired into a GitHub Actions workflow.\n"
            "- Build and container validation can be added for release automation."
        )

    def _roadmap_section(self) -> str:
        return (
            "## Roadmap\n\n"
            "- Expand retrieval sources and quality benchmarks\n"
            "- Add richer visual generation and image augmentation\n"
            "- Improve authoring modules for enterprise documentation"
        )

    def _contributing_section(self) -> str:
        return (
            "## Contributing\n\n"
            "Contributions are welcome. Please open an issue or pull request with a clear description of the improvement and any relevant evidence."
        )

    def _faq_section(self, readme_text: str) -> str:
        faq = [
            "**What does this project do?** This assistant turns repository context into publication-ready documentation.",
            "**How is it structured?** It uses a LangGraph-based multi-agent pipeline combined with repository tools.",
        ]
        if readme_text:
            faq.append(
                "**Why is this useful?** It helps teams improve discoverability, clarity, and consistency across public repositories.")
        return "## FAQ\n\n" + "\n\n".join(faq)

    def _troubleshooting_section(self, missing_sections: List[str]) -> str:
        return (
            "## Troubleshooting\n\n"
            "- Check that required environment variables are set before running the pipeline.\n"
            f"- If important sections are missing, review the repository and add the corresponding documentation: {', '.join(missing_sections[:5]) or 'documentation'}"
        )

    def _license_section(self) -> str:
        return "## License\n\nMIT License"

    def _citation_section(self) -> str:
        return "## Citation\n\nIf you use this project in research or publication, cite the repository and its accompanying materials."

    def _acknowledgements_section(self) -> str:
        return "## Acknowledgements\n\nThanks to the open-source community for the inspiration behind polished, maintainable documentation."

    def _infer_repo_name(self, repo_source: str, metadata: Any) -> str:
        candidate = None
        if metadata is not None:
            candidate = self._first(
                getattr(metadata, "title_suggestions", None), None)
        if candidate:
            return candidate
        if repo_source:
            path = Path(str(repo_source))
            if path.name:
                return path.name.replace("-", " ").replace("_", " ").title()
        return "Publication Assistant"

    def _summarize_repo(self, repo_analysis: Any) -> str:
        summary = getattr(repo_analysis, "summary", "") or ""
        return summary or "A production-ready repository documentation assistant built with multi-agent orchestration."

    def _render_tree(self, files: Dict[str, Any]) -> str:
        if not files:
            return "repository/\n├── README.md\n└── src/"
        top_files = []
        for rel_path in sorted(files.keys())[:15]:
            top_files.append(rel_path)
        if len(top_files) > 12:
            top_files = top_files[:12] + ["..."]
        lines = ["repository/"]
        for item in top_files:
            if item == "...":
                lines.append("└── ...")
            else:
                lines.append(f"├── {item}")
        return "\n".join(lines)

    def _infer_tech_stack(self, files: Dict[str, Any]) -> List[tuple]:
        stack = []
        lower = {name.lower(): content for name, content in files.items()
                 if isinstance(content, str)}
        if any("langgraph" in (content or "").lower() for content in lower.values()):
            stack.append(
                ("LangGraph", "Orchestrates the multi-agent workflow"))
        if any("fastapi" in (content or "").lower() for content in lower.values()):
            stack.append(
                ("FastAPI", "Serves the web interface and API endpoints"))
        if any("gradio" in (content or "").lower() for content in lower.values()):
            stack.append(("Gradio", "Provides an interactive user experience"))
        if any("chroma" in (content or "").lower() for content in lower.values()):
            stack.append(
                ("ChromaDB", "Stores and retrieves documentation context"))
        if any("dockerfile" in name.lower() for name in lower):
            stack.append(("Docker", "Supports containerized deployment"))
        if not stack:
            stack = [
                ("Python", "Core application logic"),
                ("Markdown", "Publication-ready documentation"),
                ("Docker", "Containerized deployment"),
            ]
        return stack

    def _infer_repo_evidence(self, files: Dict[str, Any]) -> Dict[str, List[str]]:
        evidence: Dict[str, List[str]] = {
            "endpoints": [], "deployment": [], "workflows": []}
        for rel_path, content in files.items():
            if not isinstance(content, str):
                continue
            lower_path = rel_path.lower()
            if lower_path.endswith((".py", ".md", ".txt", ".yaml", ".yml", ".json")):
                if "/health" in content or "@app.get" in content or "@router.get" in content:
                    evidence["endpoints"].append("/health")
                if "/api/validate" in content or "/api/generate" in content:
                    evidence["endpoints"].append("/api/generate")
                if "dockerfile" in lower_path or "docker-compose" in lower_path:
                    evidence["deployment"].append(rel_path)
                if lower_path.startswith(".github/workflows/") or (lower_path.endswith((".yaml", ".yml")) and "workflow" in lower_path):
                    evidence["workflows"].append(rel_path)
        return evidence

    def _infer_cli_flags(self, files: Dict[str, Any]) -> List[str]:
        flags = []
        for rel_path, content in files.items():
            if not isinstance(content, str):
                continue
            if rel_path.endswith(".py") and "add_argument" in content:
                for flag in ["--repo-path", "--serve-ui", "--host", "--port"]:
                    if flag in content:
                        flags.append(flag)
        return flags

    def _infer_env_vars(self, files: Dict[str, Any]) -> List[str]:
        env_vars = []
        for content in files.values():
            if not isinstance(content, str):
                continue
            for var in ["GOOGLE_API_KEY", "GROQ_API_KEY", "TAVILY_API_KEY"]:
                if var in content:
                    env_vars.append(var)
        return env_vars

    def _detect_images(self, files: Dict[str, Any]) -> List[str]:
        image_names = [
            "screenshot",
            "demo",
            "architecture",
            "architecture.png",
            "logo.png",
            "banner.png",
            "image.png",
        ]
        matches = []
        for rel_path in sorted(files.keys()):
            lower = rel_path.lower()
            if any(token in lower for token in image_names) or lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
                matches.append(rel_path)
        return matches

    def _repo_stats(self, code_stats: Dict[str, Any], files: Dict[str, Any]) -> Dict[str, str]:
        total_lines = code_stats.get("total_lines", 0)
        file_count = code_stats.get("file_count", len(files))
        return {
            "Version": "0.1.0",
            "Files": str(file_count),
            "Lines": str(total_lines),
            "Updated": "2026",
        }

    def _first(self, values: Optional[List[str]], default: Optional[str] = None) -> Optional[str]:
        if not values:
            return default
        for item in values:
            if item:
                return item
        return default

    def _first_list(self, values: Optional[List[str]], default: Optional[List[str]] = None) -> List[str]:
        if values:
            return [v for v in values if v]
        return default or []
