"""
LLM Integration for Arjun Code Review Tool
Uses LangChain with Ollama for local LLM-based code review
"""

import json
import re
from typing import List, Dict, Optional
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


class CodeIssue(BaseModel):
    """Model for a single code issue."""
    severity: str = Field(description="Issue severity: 'critical', 'high', 'medium', or 'low'")
    issue_line: int = Field(description="Line number where the issue occurs")
    issue_type: str = Field(description="Type of issue (e.g., 'security', 'performance', 'style', 'bug', 'maintainability')")
    issue_description: str = Field(description="Clear description of the issue")
    issue_solution: str = Field(description="Suggested solution or fix for the issue")


class CodeReviewResponse(BaseModel):
    """Model for the complete code review response."""
    issues: List[CodeIssue] = Field(description="List of identified code issues")
    summary: str = Field(description="Brief summary of the code quality")


class LLMReviewer:
    def __init__(self, model_name: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434"):
        """
        Initialize the LLM Reviewer with Ollama.
        
        Args:
            model_name: Name of the Ollama model to use (default: deepseek-coder)
            base_url: URL of the Ollama server
        """
        self.model_name = model_name
        self.base_url = base_url
        self.llm = OllamaLLM(
            model=model_name,
            base_url=base_url,
            temperature=0.1,  # Low temperature for consistent, focused reviews
        )
        
        self.review_prompt = PromptTemplate(
            input_variables=["code", "filename", "language"],
            template="""You are an expert code reviewer named Arjun. Analyze the following code and identify issues.

IMPORTANT: You must respond with ONLY a valid JSON object, no additional text.
IMPORTANT: The code below is prefixed with explicit line numbers in the format 'NNN: code'.
IMPORTANT: `issue_line` must be the exact numeric prefix of the line where the issue appears.

Filename: {filename}
Language: {language}

Code to review:
```
{code}
```

Analyze this code for:
1. Security vulnerabilities
2. Bugs and potential errors
3. Performance issues
4. Code style and best practices
5. Maintainability concerns

For each issue found, provide:
- severity: One of "critical", "high", "medium", "low"
- issue_line: The exact prefixed line number where the issue occurs
- issue_type: Category like "security", "bug", "performance", "style", "maintainability"
- issue_description: Clear explanation of the problem
- issue_solution: Specific suggestion to fix the issue

Respond with this exact JSON structure:
{{
    "issues": [
        {{
            "severity": "high",
            "issue_line": 10,
            "issue_type": "security",
            "issue_description": "Description of the issue",
            "issue_solution": "How to fix it"
        }}
    ],
    "summary": "Brief overall assessment of code quality"
}}

If no issues are found, return an empty issues array.
Respond with ONLY the JSON, no markdown formatting or additional text."""
        )
        
        self.comparison_prompt = PromptTemplate(
            input_variables=["code", "filename", "language", "existing_issues"],
            template="""You are an expert code reviewer named Arjun. Analyze the following code and compare with previously identified issues.

IMPORTANT: You must respond with ONLY a valid JSON object, no additional text.
IMPORTANT: The code below is prefixed with explicit line numbers in the format 'NNN: code'.
IMPORTANT: `issue_line` must be the exact numeric prefix of the line where the issue appears.

Filename: {filename}
Language: {language}

Code to review:
```
{code}
```

Previously identified issues (check if these are now resolved):
{existing_issues}

Tasks:
1. Check each previously identified issue - has it been resolved in the current code?
2. Identify any NEW issues not in the previous list

For each issue (new or existing), provide:
- severity: One of "critical", "high", "medium", "low"
- issue_line: The exact prefixed line number where the issue occurs (use 0 if resolved/not applicable)
- issue_type: Category like "security", "bug", "performance", "style", "maintainability"
- issue_description: Clear explanation of the problem
- issue_solution: Specific suggestion to fix the issue

Respond with this exact JSON structure:
{{
    "new_issues": [
        {{
            "severity": "high",
            "issue_line": 10,
            "issue_type": "security",
            "issue_description": "Description of the issue",
            "issue_solution": "How to fix it"
        }}
    ],
    "resolved_issue_indices": [0, 2],
    "summary": "Brief assessment of changes and current code quality"
}}

The "resolved_issue_indices" should contain the indices (0-based) of issues from the existing_issues list that have been fixed.
Respond with ONLY the JSON, no markdown formatting or additional text."""
        )

    def _add_line_numbers(self, code: str) -> str:
        """Prefix code lines with stable 1-based line numbers for the LLM."""
        lines = code.splitlines()
        width = max(3, len(str(len(lines) or 1)))
        return "\n".join(
            f"{line_number:0{width}d}: {line}"
            for line_number, line in enumerate(lines, start=1)
        )

    def _extract_quoted_terms(self, text: str) -> List[str]:
        """Extract quoted identifiers and terms from issue text."""
        if not text:
            return []

        matches = re.findall(r"['\"]([^'\"]+)['\"]", text)
        return [match.strip().lower() for match in matches if match.strip()]

    def _build_issue_keywords(self, issue: Dict) -> List[str]:
        """Build weighted search keywords from issue metadata."""
        issue_type = str(issue.get('issue_type', '')).lower()
        description = str(issue.get('issue_description', '')).lower()
        solution = str(issue.get('issue_solution', '')).lower()
        keywords: List[str] = []

        keywords.extend(self._extract_quoted_terms(description))
        keywords.extend(self._extract_quoted_terms(solution))

        if issue_type == 'security' or 'sql injection' in description:
            keywords.extend([
                'statement', 'execute(', 'executepdate(', 'executequery(',
                'insert into', 'select ', 'update ', 'delete ', 'values (',
                'drivermanager.getconnection', 'preparedstatement', 'createStatement'.lower()
            ])

        if issue_type == 'performance' or 'thread' in description:
            keywords.extend(['new thread', '.start()', 'executorservice', 'thread('])

        if issue_type == 'bug':
            keywords.extend(['.get(', 'null', 'catch', 'throw', 'index'])
            if 'out of bounds' in description or 'index' in description:
                keywords.extend(['.get(', '[', 'index'])
            if 'nullpointer' in description or 'null' in description:
                keywords.extend(['null', '== null'])

        if issue_type == 'style' or issue_type == 'maintainability':
            keywords.extend(['class ', 'static ', 'final ', 'public class', 'private static', 'public static'])

        return [keyword for keyword in dict.fromkeys(keywords) if keyword]

    def _score_issue_line(self, issue: Dict, line: str, line_number: int, guessed_line: int) -> float:
        """Score how well a source line matches a reported issue."""
        if not line.strip():
            return float('-inf')

        line_lower = line.lower()
        description = str(issue.get('issue_description', '')).lower()
        solution = str(issue.get('issue_solution', '')).lower()
        issue_type = str(issue.get('issue_type', '')).lower()
        score = 0.0

        for keyword in self._build_issue_keywords(issue):
            if keyword in line_lower:
                score += 3.0 if len(keyword) > 3 else 1.5

        if issue_type in line_lower:
            score += 2.0

        if 'sql injection' in description:
            if '+' in line and ('insert' in line_lower or 'select' in line_lower or 'update' in line_lower or 'delete' in line_lower):
                score += 5.0
            if 'createstatement' in line_lower or 'execute(' in line_lower:
                score += 4.0

        if 'thread' in description and 'new thread' in line_lower:
            score += 6.0

        if 'out of bounds' in description and '.get(' in line_lower:
            score += 6.0

        if 'nullpointer' in description and 'null' in line_lower:
            score += 4.0

        if 'class name' in description and 'class ' in line_lower:
            score += 6.0

        if 'static fields' in description and 'static' in line_lower:
            score += 5.0

        if 'preparedstatement' in solution and 'preparedstatement' in line_lower:
            score += 6.0

        if guessed_line > 0:
            score -= abs(line_number - guessed_line) * 0.05

        return score

    def _find_best_issue_line(self, issue: Dict, lines: List[str]) -> int:
        """Find the most likely source line for a reported issue."""
        guessed_line = int(issue.get('issue_line', 0) or 0)

        best_line = guessed_line
        best_score = float('-inf')

        for line_number, line in enumerate(lines, start=1):
            score = self._score_issue_line(issue, line, line_number, guessed_line)
            if score > best_score:
                best_score = score
                best_line = line_number

        if best_score < 2.5:
            return guessed_line

        return best_line

    def _verify_issue_lines(self, result: Dict, code: str) -> Dict:
        """Snap issue lines to the best-matching source lines after LLM inference."""
        lines = code.splitlines()

        for issue in result.get('issues', []):
            issue['issue_line'] = self._find_best_issue_line(issue, lines)

        for issue in result.get('new_issues', []):
            issue['issue_line'] = self._find_best_issue_line(issue, lines)

        return result

    def _fallback_static_issues(self, code: str, language: str) -> List[Dict]:
        """Run lightweight deterministic checks for common high-impact issues."""
        lines = code.splitlines()
        issues: List[Dict] = []
        seen_keys = set()

        def add_issue(line_number: int, severity: str, issue_type: str,
                      description: str, solution: str):
            key = (line_number, issue_type, description)
            if key in seen_keys:
                return
            seen_keys.add(key)
            issues.append({
                'severity': severity,
                'issue_line': line_number,
                'issue_type': issue_type,
                'issue_description': description,
                'issue_solution': solution
            })

        for line_number, line in enumerate(lines, start=1):
            line_lower = line.lower()

            has_sql_keyword = any(keyword in line_lower for keyword in ['select ', 'insert ', 'update ', 'delete '])
            if has_sql_keyword and '+' in line:
                add_issue(
                    line_number,
                    'high',
                    'security',
                    'Potential SQL injection due to string concatenation in query construction.',
                    'Use parameterized queries or prepared statements instead of concatenating user input.'
                )

            if 'createStatement'.lower() in line_lower:
                add_issue(
                    line_number,
                    'medium',
                    'security',
                    'Raw SQL Statement usage detected; this can be unsafe with dynamic input.',
                    'Prefer PreparedStatement (or language equivalent) with bound parameters.'
                )

            if 'new thread(' in line_lower:
                add_issue(
                    line_number,
                    'low',
                    'performance',
                    'Creating a new thread per item can cause performance and resource issues.',
                    'Use a thread pool / executor service for controlled concurrency.'
                )

            if re.search(r'\bcatch\s*\([^)]*\)\s*\{\s*\}\s*$', line):
                add_issue(
                    line_number,
                    'medium',
                    'bug',
                    'Empty catch block suppresses exceptions and hides failures.',
                    'Log, rethrow, or handle the exception appropriately.'
                )

        if language.lower() == 'java':
            for line_number, line in enumerate(lines, start=1):
                line_lower = line.lower()
                if 'public static ' in line_lower and ' = ' in line and ' final ' not in f" {line_lower} ":
                    add_issue(
                        line_number,
                        'low',
                        'style',
                        'Mutable public static field detected; this can lead to global shared-state issues.',
                        'Restrict visibility and immutability where possible (private/final) or avoid shared mutable statics.'
                    )

        return issues

    def _normalize_issue_lines(self, result: Dict, total_lines: int) -> Dict:
        """Coerce returned issue lines to valid integers within file bounds."""
        def normalize_issue(issue: Dict):
            try:
                line_number = int(issue.get('issue_line', 0))
            except (TypeError, ValueError):
                line_number = 0

            if line_number < 0:
                line_number = 0
            elif total_lines > 0 and line_number > total_lines:
                line_number = total_lines

            issue['issue_line'] = line_number

        for issue in result.get('issues', []):
            normalize_issue(issue)

        for issue in result.get('new_issues', []):
            normalize_issue(issue)

        return result

    def _deduplicate_issues(self, issues: List[Dict]) -> List[Dict]:
        """Remove duplicate issues based on normalized type + description + nearby line."""
        deduplicated: List[Dict] = []
        seen = set()

        for issue in issues:
            issue_type = str(issue.get('issue_type', '')).strip().lower()
            description = re.sub(r'\s+', ' ', str(issue.get('issue_description', '')).strip().lower())
            line_number = int(issue.get('issue_line', 0) or 0)
            line_bucket = line_number // 3
            key = (issue_type, description, line_bucket)

            if key in seen:
                continue

            seen.add(key)
            deduplicated.append(issue)

        return deduplicated
    
    def detect_language(self, filename: str, code: str) -> str:
        """Detect programming language from filename extension."""
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'JavaScript (React)',
            '.tsx': 'TypeScript (React)',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C/C++ Header',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.sql': 'SQL',
            '.sh': 'Shell/Bash',
            '.ps1': 'PowerShell',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'LESS',
        }
        
        for ext, lang in extension_map.items():
            if filename.lower().endswith(ext):
                return lang
        
        return 'Unknown'
    
    def parse_llm_response(self, response: str) -> Dict:
        """Parse the LLM response, handling potential formatting issues."""
        # Clean up the response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith('```'):
            lines = response.split('\n')
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)
        
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            response = json_match.group()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Return a default response if parsing fails
            return {
                "issues": [],
                "summary": f"Failed to parse LLM response: {str(e)}",
                "parse_error": True
            }
    
    def review_code(self, code: str, filename: str) -> Dict:
        """
        Review code for the first time (no existing issues).
        
        Args:
            code: The code content to review
            filename: Name of the file being reviewed
            
        Returns:
            Dictionary containing issues and summary
        """
        language = self.detect_language(filename, code)
        numbered_code = self._add_line_numbers(code)
        total_lines = len(code.splitlines())
        
        prompt = self.review_prompt.format(
            code=numbered_code,
            filename=filename,
            language=language
        )
        
        try:
            response = self.llm.invoke(prompt)
            result = self.parse_llm_response(response)

            if result.get('parse_error'):
                return {
                    "issues": self._fallback_static_issues(code, language),
                    "summary": "LLM response could not be parsed reliably for this model; returning deterministic fallback checks.",
                    "error": False,
                    "language": language,
                    "fallback_used": True
                }

            result = self._verify_issue_lines(result, code)
            result = self._normalize_issue_lines(result, total_lines)
            result['issues'] = self._deduplicate_issues(result.get('issues', []))

            if not result.get('issues'):
                fallback_issues = self._fallback_static_issues(code, language)
                if fallback_issues:
                    result['issues'] = fallback_issues
                    result['fallback_used'] = True
                    result['summary'] = (
                        result.get('summary', 'Review completed') +
                        ' | LLM returned no issues; deterministic checks found potential issues.'
                    )

            result['language'] = language
            return result
        except Exception as e:
            return {
                "issues": [],
                "summary": f"Error during review: {str(e)}",
                "error": True,
                "language": language
            }
    
    def review_code_with_history(self, code: str, filename: str, 
                                  existing_issues: List[Dict]) -> Dict:
        """
        Review code comparing against previously identified issues.
        
        Args:
            code: The code content to review
            filename: Name of the file being reviewed
            existing_issues: List of previously identified issues
            
        Returns:
            Dictionary containing new issues, resolved indices, and summary
        """
        language = self.detect_language(filename, code)
        numbered_code = self._add_line_numbers(code)
        total_lines = len(code.splitlines())
        
        # Format existing issues for the prompt
        existing_issues_str = json.dumps([
            {
                "index": i,
                "severity": issue.get('severity', 'medium'),
                "issue_line": issue.get('issue_line', 0),
                "issue_type": issue.get('issue_type', 'unknown'),
                "issue_description": issue.get('issue_description', '')
            }
            for i, issue in enumerate(existing_issues)
        ], indent=2)
        
        prompt = self.comparison_prompt.format(
            code=numbered_code,
            filename=filename,
            language=language,
            existing_issues=existing_issues_str
        )
        
        try:
            response = self.llm.invoke(prompt)
            result = self.parse_llm_response(response)
            result['language'] = language

            if result.get('parse_error'):
                return {
                    "new_issues": self._fallback_static_issues(code, language),
                    "resolved_issue_indices": [],
                    "summary": "LLM response could not be parsed reliably for this model; returning deterministic fallback checks.",
                    "error": False,
                    "language": language,
                    "fallback_used": True
                }
            
            # Ensure required keys exist
            if 'new_issues' not in result:
                result['new_issues'] = result.get('issues', [])
            if 'resolved_issue_indices' not in result:
                result['resolved_issue_indices'] = []

            result = self._verify_issue_lines(result, code)
            result = self._normalize_issue_lines(result, total_lines)
            result['new_issues'] = self._deduplicate_issues(result.get('new_issues', []))

            if not result.get('new_issues'):
                fallback_issues = self._fallback_static_issues(code, language)
                if fallback_issues:
                    result['new_issues'] = fallback_issues
                    result['fallback_used'] = True
                    result['summary'] = (
                        result.get('summary', 'Review completed') +
                        ' | LLM returned no new issues; deterministic checks found potential issues.'
                    )
            
            return result
        except Exception as e:
            return {
                "new_issues": [],
                "resolved_issue_indices": [],
                "summary": f"Error during review: {str(e)}",
                "error": True,
                "language": language
            }
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama server is accessible."""
        try:
            # Simple test query
            self.llm.invoke("Say 'OK' if you can hear me.")
            return True
        except Exception:
            return False


def get_severity_color(severity: str) -> str:
    """Get color code for severity level."""
    colors = {
        'critical': '#FF0000',  # Red
        'high': '#FF6600',      # Orange
        'medium': '#FFCC00',    # Yellow
        'low': '#00CC00',       # Green
    }
    return colors.get(severity.lower(), '#808080')


def get_severity_emoji(severity: str) -> str:
    """Get emoji for severity level."""
    emojis = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
    }
    return emojis.get(severity.lower(), '⚪')
