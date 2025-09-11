"""
GitHub API integration for managing pull requests and repository operations.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from github import Github, GithubException
from datetime import datetime

logger = logging.getLogger(__name__)


class PRManager:
    """Manages GitHub pull request operations."""
    
    def __init__(self, config):
        self.config = config
        self.github = Github(config.github_token)
        self.pr_branch_prefix = config.pr_branch_prefix
        self.pr_title_prefix = config.pr_title_prefix
    
    def get_pr_info(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a pull request.
        
        Args:
            repo_url: GitHub repository URL
            pr_number: Pull request number
            
        Returns:
            Dictionary containing PR information
        """
        try:
            repo_name = self._extract_repo_name(repo_url)
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            return {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "author": pr.user.login,
                "url": pr.html_url,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "commits": pr.commits
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting PR info: {str(e)}")
            raise
    
    def get_changed_files(self, repo_url: str, pr_number: int) -> List[str]:
        """
        Get list of files changed in a pull request.
        
        Args:
            repo_url: GitHub repository URL
            pr_number: Pull request number
            
        Returns:
            List of file paths that were changed
        """
        try:
            repo_name = self._extract_repo_name(repo_url)
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            changed_files = []
            for file in pr.get_files():
                if file.status in ['added', 'modified']:
                    changed_files.append(file.filename)
            
            return changed_files
            
        except GithubException as e:
            logger.error(f"GitHub API error getting changed files: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting changed files: {str(e)}")
            raise
    
    def get_file_content(self, repo_url: str, file_path: str, ref: str = None) -> str:
        """
        Get content of a specific file from the repository.
        
        Args:
            repo_url: GitHub repository URL
            file_path: Path to the file in the repository
            ref: Git reference (branch, commit, tag). Defaults to default branch
            
        Returns:
            File content as string
        """
        try:
            repo_name = self._extract_repo_name(repo_url)
            repo = self.github.get_repo(repo_name)
            
            file_content = repo.get_contents(file_path, ref=ref)
            return file_content.decoded_content.decode('utf-8')
            
        except GithubException as e:
            logger.error(f"GitHub API error getting file content: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting file content: {str(e)}")
            raise
    
    def create_test_pr(self, repo_url: str, original_pr_number: int, 
                      generated_tests: List[Dict[str, Any]], 
                      coverage_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new pull request with generated tests.
        
        Args:
            repo_url: GitHub repository URL
            original_pr_number: Original PR number that was analyzed
            generated_tests: List of generated test information
            coverage_report: Coverage analysis results
            
        Returns:
            Dictionary containing new PR information
        """
        try:
            repo_name = self._extract_repo_name(repo_url)
            repo = self.github.get_repo(repo_name)
            
            # Get original PR info
            original_pr = repo.get_pull(original_pr_number)
            
            # Create new branch for tests
            branch_name = f"{self.pr_branch_prefix}pr-{original_pr_number}-{int(datetime.now().timestamp())}"
            base_branch = repo.get_branch(original_pr.base.ref)
            
            # Create new branch
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_branch.commit.sha
            )
            
            # Create test files
            created_files = []
            for test_info in generated_tests:
                file_path = test_info["test_file_path"]
                test_code = test_info["test_code"]
                
                # Ensure test directory exists in the repository structure
                self._create_test_file_in_repo(repo, file_path, test_code, branch_name)
                created_files.append(file_path)
            
            # Create PR description
            pr_description = self._generate_pr_description(
                original_pr_number, generated_tests, coverage_report, created_files
            )
            
            # Create pull request
            new_pr = repo.create_pull(
                title=f"{self.pr_title_prefix} (PR #{original_pr_number})",
                body=pr_description,
                head=branch_name,
                base=original_pr.base.ref
            )
            
            logger.info(f"Created new PR: {new_pr.html_url}")
            
            return {
                "number": new_pr.number,
                "title": new_pr.title,
                "url": new_pr.html_url,
                "branch": branch_name,
                "created_files": created_files,
                "test_count": len(generated_tests)
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error creating PR: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating test PR: {str(e)}")
            raise
    
    def _create_test_file_in_repo(self, repo, file_path: str, content: str, branch: str):
        """Create a test file in the repository."""
        try:
            # Check if file already exists
            try:
                existing_file = repo.get_contents(file_path, ref=branch)
                # File exists, update it
                repo.update_file(
                    path=file_path,
                    message=f"Update test file {file_path}",
                    content=content,
                    sha=existing_file.sha,
                    branch=branch
                )
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(
                    path=file_path,
                    message=f"Add test file {file_path}",
                    content=content,
                    branch=branch
                )
                
        except Exception as e:
            logger.error(f"Error creating test file {file_path}: {str(e)}")
            raise
    
    def _generate_pr_description(self, original_pr_number: int, 
                               generated_tests: List[Dict[str, Any]], 
                               coverage_report: Dict[str, Any],
                               created_files: List[str]) -> str:
        """Generate description for the new PR."""
        
        current_coverage = coverage_report.get("overall_coverage", 0)
        
        description = f"""
# 🤖 Automated Test Generation

This PR was automatically generated to improve test coverage for PR #{original_pr_number}.

## 📊 Coverage Analysis

- **Current Coverage**: {current_coverage:.1f}%
- **Target Coverage**: {self.config.coverage_threshold}%
- **Generated Tests**: {len(generated_tests)}

## 🧪 Generated Test Files

"""
        
        for file_path in created_files:
            description += f"- `{file_path}`\n"
        
        description += f"""

## 🔍 Test Generation Summary

"""
        
        for i, test_info in enumerate(generated_tests, 1):
            source_func = test_info["source_function"]
            description += f"""
### {i}. {source_func['function_name']} ({source_func['file_path']})
- **Type**: {source_func['function_type']}
- **Complexity**: {source_func['complexity']}
- **Test Methods**: {len(test_info['test_methods'])}
- **Strategy**: {test_info.get('explanation', 'N/A')}
"""
        
        description += f"""

## ✅ Next Steps

1. Review the generated tests for accuracy
2. Run the test suite to ensure all tests pass
3. Merge this PR to improve code coverage
4. Consider merging after PR #{original_pr_number} is merged

---

*This PR was automatically generated by the PR Coverage Analyzer & Test Generator*
"""
        
        return description
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from GitHub URL."""
        # Handle different URL formats
        if repo_url.startswith('https://github.com/'):
            repo_name = repo_url.replace('https://github.com/', '').rstrip('/')
        elif repo_url.startswith('git@github.com:'):
            repo_name = repo_url.replace('git@github.com:', '').replace('.git', '')
        else:
            # Assume it's already in owner/repo format
            repo_name = repo_url
        
        return repo_name
    
    def add_pr_comment(self, repo_url: str, pr_number: int, comment: str) -> None:
        """Add a comment to a pull request."""
        try:
            repo_name = self._extract_repo_name(repo_url)
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            pr.create_issue_comment(comment)
            logger.info(f"Added comment to PR #{pr_number}")
            
        except Exception as e:
            logger.error(f"Error adding PR comment: {str(e)}")
            raise
    
    def get_repository_languages(self, repo_url: str) -> Dict[str, int]:
        """Get programming languages used in the repository."""
        try:
            repo_name = self._extract_repo_name(repo_url)
            repo = self.github.get_repo(repo_name)
            
            return repo.get_languages()
            
        except Exception as e:
            logger.error(f"Error getting repository languages: {str(e)}")
            return {}
