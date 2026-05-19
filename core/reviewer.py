"""
Core Code Review Logic for Arjun
Orchestrates LLM and Database operations for comprehensive code review
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from database import DatabaseManager
from llm import LLMReviewer


@dataclass
class ReviewResult:
    """Data class to hold code review results."""
    filename: str
    is_new_file: bool
    language: str
    new_issues: List[Dict] = field(default_factory=list)
    existing_issues: List[Dict] = field(default_factory=list)
    resolved_issues: List[Dict] = field(default_factory=list)
    historical_resolved_issues: List[Dict] = field(default_factory=list)
    summary: str = ""
    acceptance_stats: Dict = field(default_factory=dict)
    error: Optional[str] = None


class ArjunReviewer:
    """Main code review orchestrator."""
    
    def __init__(self, model_name: str = "qwen2.5-coder:7b", db_path: str = "arjun_reviews.db"):
        """
        Initialize the Arjun Reviewer.
        
        Args:
            model_name: Ollama model to use for code review
            db_path: Path to SQLite database
        """
        self.db = DatabaseManager(db_path)
        self.llm = LLMReviewer(model_name=model_name)
    
    def review_file(self, filename: str, content: str) -> ReviewResult:
        """
        Perform a complete code review on a file.
        
        Args:
            filename: Name of the file to review
            content: Content of the file
            
        Returns:
            ReviewResult with categorized issues
        """
        # Compute hash and detect unchanged re-uploads
        file_hash = self.db.compute_file_hash(content)
        existing_file = self.db.get_file_by_name(filename)

        if existing_file and existing_file.get('file_hash') == file_hash:
            file_id = existing_file['id']
            result = ReviewResult(
                filename=filename,
                is_new_file=False,
                language=self.llm.detect_language(filename, content),
                new_issues=[],
                existing_issues=self.db.get_existing_issues(file_id),
                resolved_issues=[],
                historical_resolved_issues=self.db.get_resolved_issues(file_id),
                summary="No code changes detected since last scan; preserving previous issue state."
            )

            result.acceptance_stats = self.db.get_acceptance_ratio(file_id)
            self.db.record_scan_history(
                file_id=file_id,
                file_hash=file_hash,
                new_count=0,
                existing_count=len(result.existing_issues),
                resolved_count=0
            )
            return result

        # Get/create file record for changed content
        file_id, is_new_file = self.db.get_or_create_file(filename, file_hash)
        
        result = ReviewResult(
            filename=filename,
            is_new_file=is_new_file,
            language=self.llm.detect_language(filename, content)
        )
        
        if is_new_file:
            # First time review - no history
            result = self._review_new_file(file_id, filename, content, result)
        else:
            # File exists - compare with history
            result = self._review_existing_file(file_id, filename, content, result)
        
        # Calculate acceptance statistics
        result.acceptance_stats = self.db.get_acceptance_ratio(file_id)
        result.historical_resolved_issues = self.db.get_resolved_issues(file_id)
        
        # Record scan history
        self.db.record_scan_history(
            file_id=file_id,
            file_hash=file_hash,
            new_count=len(result.new_issues),
            existing_count=len(result.existing_issues),
            resolved_count=len(result.resolved_issues)
        )
        
        return result
    
    def _review_new_file(self, file_id: int, filename: str, 
                         content: str, result: ReviewResult) -> ReviewResult:
        """Review a file that has never been scanned before."""
        try:
            llm_result = self.llm.review_code(content, filename)
            
            if llm_result.get('error'):
                result.error = llm_result.get('summary', 'Unknown error')
                return result
            
            result.summary = llm_result.get('summary', 'Review completed')
            result.language = llm_result.get('language', result.language)
            
            # All issues are new for a new file
            for issue in llm_result.get('issues', []):
                issue_id, is_new = self.db.add_issue(file_id, filename, issue)
                issue['id'] = issue_id
                issue['is_new'] = is_new
                result.new_issues.append(issue)
            
        except Exception as e:
            result.error = f"Error during review: {str(e)}"
        
        return result
    
    def _review_existing_file(self, file_id: int, filename: str,
                              content: str, result: ReviewResult) -> ReviewResult:
        """Review a file that has been scanned before."""
        try:
            # Get existing open issues from database
            existing_db_issues = self.db.get_existing_issues(file_id)
            
            if not existing_db_issues:
                # No existing issues, treat as new review
                return self._review_new_file(file_id, filename, content, result)
            
            # Fresh review, then reconcile with existing issues.
            # This avoids false "resolved" events when only line numbers shift.
            llm_result = self.llm.review_code(content, filename)
            
            if llm_result.get('error'):
                result.error = llm_result.get('summary', 'Unknown error')
                return result
            
            result.summary = llm_result.get('summary', 'Review completed')
            result.language = llm_result.get('language', result.language)
            
            detected_issues = llm_result.get('issues', [])
            matched_existing_ids: Set[int] = set()

            # Match each detected issue against open issues.
            for detected_issue in detected_issues:
                matched_issue = self._find_best_existing_match(
                    detected_issue,
                    existing_db_issues,
                    matched_existing_ids
                )

                if matched_issue:
                    matched_existing_ids.add(matched_issue['id'])
                    previous_line = matched_issue.get('issue_line', 0)
                    new_line = detected_issue.get('issue_line', 0)
                    self.db.update_issue(matched_issue['id'], detected_issue)

                    updated_issue = dict(matched_issue)
                    updated_issue.update({
                        'severity': detected_issue['severity'],
                        'issue_line': new_line,
                        'issue_type': detected_issue['issue_type'],
                        'issue_description': detected_issue['issue_description'],
                        'issue_solution': detected_issue['issue_solution'],
                        'line_updated': previous_line != new_line,
                        'previous_issue_line': previous_line
                    })
                    result.existing_issues.append(updated_issue)
                else:
                    issue_id, is_new = self.db.add_issue(file_id, filename, detected_issue)
                    if is_new:
                        detected_issue['id'] = issue_id
                        detected_issue['is_new'] = True
                        result.new_issues.append(detected_issue)

            # Unmatched previously-open issues are genuinely resolved.
            resolved_issue_ids = []
            for issue in existing_db_issues:
                if issue['id'] not in matched_existing_ids:
                    result.resolved_issues.append(issue)
                    resolved_issue_ids.append(issue['id'])

            if resolved_issue_ids:
                self.db.mark_issues_resolved(resolved_issue_ids)
            
        except Exception as e:
            result.error = f"Error during review: {str(e)}"
        
        return result

    def _issue_identity_key(self, issue: Dict) -> Tuple[str, str]:
        """Build a stable identity for an issue independent of line number."""
        issue_type = str(issue.get('issue_type', '')).strip().lower()
        issue_description = self._normalize_text(issue.get('issue_description', ''))
        return issue_type, issue_description

    def _normalize_text(self, value: str) -> str:
        """Normalize text for robust cross-scan issue matching."""
        text = str(value or '').strip().lower()
        text = ''.join(character if character.isalnum() or character.isspace() else ' ' for character in text)
        return ' '.join(text.split())

    def _issue_similarity_score(self, detected_issue: Dict, existing_issue: Dict) -> float:
        """Compute semantic similarity score between detected and existing issue."""
        detected_type = str(detected_issue.get('issue_type', '')).strip().lower()
        existing_type = str(existing_issue.get('issue_type', '')).strip().lower()
        if detected_type != existing_type:
            return 0.0

        detected_description = self._normalize_text(detected_issue.get('issue_description', ''))
        existing_description = self._normalize_text(existing_issue.get('issue_description', ''))

        detected_solution = self._normalize_text(detected_issue.get('issue_solution', ''))
        existing_solution = self._normalize_text(existing_issue.get('issue_solution', ''))

        description_similarity = SequenceMatcher(None, detected_description, existing_description).ratio()
        solution_similarity = SequenceMatcher(None, detected_solution, existing_solution).ratio()

        detected_line = int(detected_issue.get('issue_line', 0) or 0)
        existing_line = int(existing_issue.get('issue_line', 0) or 0)
        line_distance = abs(detected_line - existing_line)
        if line_distance == 0:
            line_bonus = 0.10
        elif line_distance <= 3:
            line_bonus = 0.06
        elif line_distance <= 8:
            line_bonus = 0.03
        else:
            line_bonus = 0.0

        score = (description_similarity * 0.82) + (solution_similarity * 0.18) + line_bonus
        return min(score, 1.0)

    def _find_best_existing_match(self, detected_issue: Dict,
                                  existing_db_issues: List[Dict],
                                  matched_existing_ids: Set[int]) -> Optional[Dict]:
        """Find best matching open issue via exact identity or fuzzy semantic similarity."""
        detected_key = self._issue_identity_key(detected_issue)
        similarity_threshold = 0.72

        exact_line_candidate = None
        best_fuzzy_candidate = None
        best_fuzzy_score = 0.0

        for existing_issue in existing_db_issues:
            if existing_issue['id'] in matched_existing_ids:
                continue

            existing_key = self._issue_identity_key(existing_issue)
            if existing_key == detected_key:
                if existing_issue.get('issue_line', 0) == detected_issue.get('issue_line', 0):
                    exact_line_candidate = existing_issue
                    break
                if best_fuzzy_candidate is None:
                    best_fuzzy_candidate = existing_issue
                    best_fuzzy_score = 0.99
                continue

            candidate_score = self._issue_similarity_score(detected_issue, existing_issue)
            if candidate_score >= similarity_threshold and candidate_score > best_fuzzy_score:
                best_fuzzy_score = candidate_score
                best_fuzzy_candidate = existing_issue

        return exact_line_candidate or best_fuzzy_candidate
    
    def acknowledge_issue(self, issue_id: int):
        """Mark an issue as acknowledged by the user."""
        self.db.acknowledge_issue(issue_id)
    
    def get_file_history(self, filename: str) -> List[Dict]:
        """Get scan history for a file."""
        return self.db.get_file_history(filename)
    
    def get_global_stats(self) -> Dict:
        """Get global acceptance statistics."""
        return self.db.get_acceptance_ratio()
    
    def check_connection(self) -> bool:
        """Check if LLM connection is working."""
        return self.llm.check_ollama_connection()
