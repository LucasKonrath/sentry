"""
Main entry point for the PR Coverage Analyzer & Test Generator.

This module orchestrates the entire workflow:
1. Analyze PR for coverage data
2. Identify areas needing test coverage
3. Generate tests using LLM
4. Create new PR with improved tests
"""

import os
import sys
import logging
from typing import Optional
from dotenv import load_dotenv
import click
from rich.console import Console
from rich.logging import RichHandler

from analyzers.coverage_analyzer import CoverageAnalyzer
from analyzers.code_analyzer import CodeAnalyzer
from generators.test_generator import TestGenerator
from github.pr_manager import PRManager
from utils.config import Config

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)
console = Console()


class PRCoverageAnalyzer:
    """Main orchestrator for PR coverage analysis and test generation."""
    
    def __init__(self):
        self.config = Config()
        self.coverage_analyzer = CoverageAnalyzer(self.config)
        self.code_analyzer = CodeAnalyzer(self.config)
        self.test_generator = TestGenerator(self.config)
        self.pr_manager = PRManager(self.config)
        
    def analyze_pr(self, repo_url: str, pr_number: int) -> dict:
        """
        Analyze a pull request and generate improved test coverage.
        
        Args:
            repo_url: GitHub repository URL
            pr_number: Pull request number
            
        Returns:
            Dictionary containing analysis results and generated PR info
        """
        try:
            console.print(f"🔍 Analyzing PR #{pr_number} in {repo_url}", style="bold blue")
            
            # Step 1: Get PR information and files
            pr_info = self.pr_manager.get_pr_info(repo_url, pr_number)
            changed_files = self.pr_manager.get_changed_files(repo_url, pr_number)
            
            # Step 2: Analyze current coverage
            console.print("📊 Analyzing current test coverage...", style="yellow")
            coverage_report = self.coverage_analyzer.analyze_coverage(changed_files)
            
            # Step 3: Identify uncovered code areas
            uncovered_areas = self.code_analyzer.find_uncovered_areas(
                changed_files, coverage_report
            )
            
            # Step 4: Generate unit tests for uncovered areas
            if uncovered_areas:
                console.print(f"🤖 Generating tests for {len(uncovered_areas)} uncovered areas...", style="green")
                generated_tests = self.test_generator.generate_tests(uncovered_areas)
                
                # Step 5: Create new PR with generated tests
                new_pr_info = self.pr_manager.create_test_pr(
                    repo_url, pr_number, generated_tests, coverage_report
                )
                
                console.print(f"✅ Created new PR: {new_pr_info['url']}", style="bold green")
                return {
                    "original_pr": pr_info,
                    "coverage_report": coverage_report,
                    "generated_tests": generated_tests,
                    "new_pr": new_pr_info,
                    "success": True
                }
            else:
                console.print("✅ No additional tests needed - coverage is adequate!", style="bold green")
                return {
                    "original_pr": pr_info,
                    "coverage_report": coverage_report,
                    "message": "Coverage is adequate",
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"Error analyzing PR: {str(e)}")
            console.print(f"❌ Error: {str(e)}", style="bold red")
            return {
                "error": str(e),
                "success": False
            }


@click.command()
@click.option('--repo-url', required=True, help='GitHub repository URL')
@click.option('--pr-number', required=True, type=int, help='Pull request number')
@click.option('--config-file', help='Path to configuration file')
def main(repo_url: str, pr_number: int, config_file: Optional[str]):
    """Analyze PR coverage and generate tests to improve it."""
    
    if config_file:
        os.environ['CONFIG_FILE'] = config_file
    
    analyzer = PRCoverageAnalyzer()
    result = analyzer.analyze_pr(repo_url, pr_number)
    
    if result['success']:
        console.print("🎉 Analysis completed successfully!", style="bold green")
    else:
        console.print("💥 Analysis failed!", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()
