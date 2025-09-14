#!/usr/bin/env python3
"""
Real Claude API test - Generate tests for the Java calculator using Claude 3.5 Sonnet
"""

import os
import sys
from pathlib import Path

# Add src to path to import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from src.utils.config import Config
from src.generators.test_generator import TestGenerator

console = Console()

def test_claude_generation():
    """Test real Claude API call for test generation."""
    
    console.print(Panel.fit(
        "[bold blue]🤖 Real Claude API Test - Java Calculator[/bold blue]",
        border_style="blue"
    ))
    
    # Load configuration
    config = Config()
    console.print(f"✅ LLM Provider: {config.llm_provider}")
    console.print(f"✅ Model: {config.llm_model}")
    console.print(f"✅ Local Mode: {config.local_mode}")
    
    # Initialize test generator
    generator = TestGenerator(config)
    
    if not generator._is_client_configured():
        console.print("[red]❌ No LLM client available. Check your API key configuration.[/red]")
        return
    
    client = generator.anthropic_client if config.llm_provider == "claude" else generator.openai_client
    console.print(f"✅ Claude client initialized: {type(client).__name__}")
    
    # Create mock uncovered area for our Java calculator
    uncovered_area = {
        "file_path": "/Users/lucasdamaceno/Documents/pocs/sentry/test-java-project/src/main/java/com/example/calculator/SimpleCalculator.java",
        "function_name": "multiply",
        "function_type": "method", 
        "signature": "public int multiply(int a, int b)",
        "line_start": 14,
        "line_end": 16,
        "complexity": 1,
        "missing_lines": [14, 15],
        "language": "java",
        "docstring": "Multiplies two integers and returns the result"
    }
    
    console.print("\n[bold yellow]📊 Analyzing uncovered method:[/bold yellow]")
    console.print(f"• Method: {uncovered_area['function_name']}")
    console.print(f"• Signature: {uncovered_area['signature']}")
    console.print(f"• Missing lines: {uncovered_area['missing_lines']}")
    
    console.print("\n[bold cyan]🚀 Calling Claude 3.5 Sonnet to generate tests...[/bold cyan]")
    
    try:
        # Call Claude to generate tests
        generated_tests = generator.generate_tests([uncovered_area])
        
        if generated_tests:
            console.print(f"\n[bold green]✅ Successfully generated {len(generated_tests)} test(s)![/bold green]")
            
            for i, test in enumerate(generated_tests, 1):
                console.print(f"\n[bold magenta]📝 Generated Test {i}:[/bold magenta]")
                
                if 'test_code' in test:
                    console.print(Panel(
                        Syntax(test['test_code'], "java", theme="monokai", line_numbers=True),
                        title=f"[green]Test for {test.get('target_function', 'Unknown')}[/green]",
                        border_style="green"
                    ))
                
                if 'explanation' in test:
                    console.print(f"[cyan]Explanation: {test['explanation']}[/cyan]")
                    
                if 'test_cases' in test:
                    console.print("[yellow]Test Cases Covered:[/yellow]")
                    for case in test['test_cases']:
                        console.print(f"  • {case}")
        else:
            console.print("[red]❌ No tests were generated.[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error during test generation: {str(e)}[/red]")
        import traceback
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

def test_simple_claude_call():
    """Test a simple direct Claude API call."""
    
    console.print(Panel.fit(
        "[bold blue]🧪 Simple Claude API Test[/bold blue]",
        border_style="blue"
    ))
    
    try:
        import anthropic
        
        config = Config()
        client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        
        console.print("✅ Anthropic client created")
        console.print("🚀 Making simple test call to Claude...")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            temperature=0.2,
            system="You are a helpful coding assistant.",
            messages=[
                {
                    "role": "user",
                    "content": "Generate a simple Java JUnit test method for testing a multiply(int a, int b) method. Just return the test method code."
                }
            ]
        )
        
        console.print("[bold green]✅ Claude API call successful![/bold green]")
        console.print("\n[bold cyan]Claude's Response:[/bold cyan]")
        console.print(Panel(
            Syntax(response.content[0].text, "java", theme="monokai", line_numbers=True),
            title="[green]Claude Generated Test[/green]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]❌ Simple API test failed: {str(e)}[/red]")
        import traceback
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

if __name__ == "__main__":
    # First try simple API call
    test_simple_claude_call()
    
    console.print("\n" + "="*60 + "\n")
    
    # Then try full test generation
    test_claude_generation()
