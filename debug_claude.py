#!/usr/bin/env python3
"""
Debug Claude response to see what it's returning
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

def debug_claude_response():
    """Debug what Claude is actually returning."""
    
    console.print(Panel.fit(
        "[bold blue]🔍 Debug Claude Response[/bold blue]",
        border_style="blue"
    ))
    
    # Load configuration
    config = Config()
    generator = TestGenerator(config)
    
    # Create mock uncovered area
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
    
    # Get the source code context
    source_code = """
    public class SimpleCalculator {
        public int add(int a, int b) {
            return a + b;
        }
        
        public int multiply(int a, int b) {
            return a * b;
        }
        
        public int subtract(int a, int b) {
            return a - b;
        }
    }
    """
    
    # Create prompt
    prompt = generator._create_test_generation_prompt(uncovered_area, source_code)
    system_prompt = generator._get_system_prompt("java")
    
    console.print("[bold yellow]System Prompt:[/bold yellow]")
    console.print(Panel(system_prompt, title="System"))
    
    console.print("[bold yellow]User Prompt:[/bold yellow]")
    console.print(Panel(prompt, title="User"))
    
    # Call Claude
    try:
        response_content = generator._call_llm(system_prompt, prompt)
        
        console.print("[bold green]Claude Raw Response:[/bold green]")
        console.print(Panel(response_content, title="Raw Response"))
        
        # Try to parse it
        result = generator._parse_test_response(response_content, uncovered_area)
        
        if result:
            console.print("[bold green]✅ Parsing successful![/bold green]")
            console.print(Panel(str(result), title="Parsed Result"))
        else:
            console.print("[bold red]❌ Parsing failed[/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")

if __name__ == "__main__":
    debug_claude_response()
