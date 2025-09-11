"""
Example script demonstrating how to use the PR Coverage Analyzer.
"""

import os
import sys
from dotenv import load_dotenv

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import PRCoverageAnalyzer

# Load environment variables
load_dotenv()


def main():
    """Example usage of the PR Coverage Analyzer."""
    
    # Check if required environment variables are set
    if not os.getenv('GITHUB_TOKEN'):
        print("❌ Please set GITHUB_TOKEN environment variable")
        return
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    # Example repository and PR
    repo_url = "https://github.com/your-username/your-repo"
    pr_number = 123
    
    print(f"🚀 Analyzing PR #{pr_number} in {repo_url}")
    print("=" * 50)
    
    # Create analyzer instance
    analyzer = PRCoverageAnalyzer()
    
    # Analyze the PR
    result = analyzer.analyze_pr(repo_url, pr_number)
    
    if result['success']:
        print("✅ Analysis completed successfully!")
        
        if 'new_pr' in result:
            print(f"📝 Created new PR: {result['new_pr']['url']}")
            print(f"📊 Generated {result['new_pr']['test_count']} test files")
        else:
            print("ℹ️  No additional tests were needed")
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
