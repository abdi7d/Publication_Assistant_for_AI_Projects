# tools/repo_parser.py
import os
import zipfile
import shutil
import subprocess
import tempfile
from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class RepoParser:
    """
    Parse a local repository path, a zipped repository, or a remote git URL.
    """

    @staticmethod
    def _validate_git_url(url: str) -> bool:
        """Validate git URL to prevent command injection."""
        if not url:
            return False
        
        # Whitelist allowed git URL patterns
        allowed_patterns = [
            r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$',  # HTTP/HTTPS
            r'^git@[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$',  # SSH
            r'^git://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$',  # Git protocol
        ]
        
        # Check against allowed patterns
        for pattern in allowed_patterns:
            if re.match(pattern, url):
                break
        else:
            return False
        
        # Block dangerous characters that could lead to command injection
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '\n', '\r', '\x00']
        if any(char in url for char in dangerous_chars):
            logger.warning("Git URL contains dangerous characters: %s", url)
            return False
        
        # Block shell command attempts
        dangerous_commands = ['&&', '||', '>', '<', '>>', '2>', '2>>']
        if any(cmd in url for cmd in dangerous_commands):
            logger.warning("Git URL contains shell commands: %s", url)
            return False
        
        return True

    def parse(self, repo_source: str) -> Dict[str, Any]:
        if not repo_source:
            return {"files": {}, "README.md": ""}

        if os.path.exists(repo_source):
            if os.path.isdir(repo_source):
                return self._parse_dir(repo_source)
            if repo_source.endswith(".zip"):
                try:
                    return self._parse_zip(repo_source)
                except Exception as exc:
                    logger.warning(
                        "Failed to parse zip archive %s: %s", repo_source, exc)
                    return {"files": {}, "README.md": ""}
        elif repo_source.startswith("http") or repo_source.startswith("git@"):
            try:
                return self._parse_git(repo_source)
            except subprocess.CalledProcessError as exc:
                logger.error("Git clone failed: %s", exc)
                if "github.com" in repo_source.lower():
                    return {"files": {}, "README.md": "", "error": str(exc)}
                raise RuntimeError(
                    f"Failed to clone repository: {repo_source}") from exc
            except RuntimeError as exc:
                logger.warning(
                    "Failed to parse remote repository %s: %s", repo_source, exc)
                if "github.com" in repo_source.lower():
                    return {"files": {}, "README.md": "", "error": str(exc)}
                raise
            except Exception as exc:
                logger.warning(
                    "Failed to parse remote repository %s: %s", repo_source, exc)
                raise
        elif repo_source.startswith("file://"):
            try:
                path = repo_source[7:]
                if os.path.exists(path):
                    return self._parse_dir(path)
            except Exception as exc:
                logger.warning(
                    "Failed to parse file URL %s: %s", repo_source, exc)
            return {"files": {}, "README.md": "", "error": "invalid file URL"}

        logger.warning("Invalid repo_source: %s", repo_source)
        if "-" in repo_source and "/" not in repo_source and "." not in repo_source:
            return {"files": {}, "README.md": ""}
        raise ValueError(
            f"Invalid repo_source: {repo_source}. Must be a local path, zip file, or git URL.")

    def _parse_dir(self, path: str) -> Dict[str, Any]:
        files: Dict[str, str] = {}
        readme = ""
        ignore_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules",
                       ".idea", ".vscode", ".pytest_cache", "coverage_html", "chroma_db", "uploads"}

        # Resolve absolute path and validate it's within the intended directory
        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
                return {"files": {}, "README.md": "", "error": "Invalid directory path"}
        except Exception as exc:
            logger.warning("Path validation failed: %s", exc)
            return {"files": {}, "README.md": "", "error": "Path validation failed"}

        for root, dirs, filenames in os.walk(abs_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for fname in filenames:
                full = os.path.join(root, fname)
                
                # Validate path is still within the intended directory (prevent path traversal)
                try:
                    full_abs = os.path.abspath(full)
                    if not full_abs.startswith(abs_path + os.sep) and full_abs != abs_path:
                        logger.warning("Path traversal attempt detected: %s", full)
                        continue
                except Exception as exc:
                    logger.warning("Path validation failed for %s: %s", full, exc)
                    continue
                
                rel = os.path.relpath(full, abs_path)
                try:
                    if os.path.getsize(full) > 100_000:
                        continue
                    with open(full, "r", encoding="utf-8", errors="ignore") as handle:
                        content = handle.read()
                    files[rel] = content
                    if fname.lower().startswith("readme"):
                        readme = content
                except Exception as exc:
                    logger.warning("Failed to read file %s: %s", full, exc)
        return {"files": files, "README.md": readme, "title": self._infer_title(readme)}

    def _parse_zip(self, zip_path: str) -> Dict[str, Any]:
        files: Dict[str, str] = {}
        readme = ""
        with zipfile.ZipFile(zip_path, "r") as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                try:
                    content = z.read(info.filename).decode(
                        "utf-8", errors="ignore")
                    files[info.filename] = content
                    if os.path.basename(info.filename).lower().startswith("readme"):
                        readme = content
                except Exception as exc:
                    logger.warning("Failed to decode %s: %s",
                                   info.filename, exc)
        return {"files": files, "README.md": readme, "title": self._infer_title(readme)}

    def _parse_git(self, git_url: str) -> Dict[str, Any]:
        # Validate git URL before execution
        if not self._validate_git_url(git_url):
            logger.error("Invalid or dangerous git URL: %s", git_url)
            return {"files": {}, "README.md": "", "error": "Invalid git URL"}
        
        temp_dir = tempfile.mkdtemp()
        logger.info("Cloning %s to %s", git_url, temp_dir)
        try:
            # Use subprocess.run with additional security measures
            result = subprocess.run(
                ["git", "clone", "--depth", "1", git_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=120,  # Add timeout to prevent hanging
                check=True
            )
            logger.debug("Git clone output: %s", result.stdout)
            return self._parse_dir(temp_dir)
        except subprocess.TimeoutExpired as exc:
            logger.error("Git clone timed out: %s", exc)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"files": {}, "README.md": "", "error": "Git clone timed out"}
        except subprocess.CalledProcessError as exc:
            logger.error("Git clone failed: %s, stderr: %s", exc, exc.stderr)
            raise RuntimeError(
                f"Failed to clone repository: {git_url}") from exc
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _infer_title(self, readme: str) -> str:
        if not readme:
            return "Repository"
        first_line = readme.strip().splitlines()[0].strip()
        if first_line.startswith("#"):
            return first_line.lstrip("#").strip()
        return first_line[:80]
