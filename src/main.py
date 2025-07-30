"""
Main entry point for AutoGraph.
Provides command-line interface for codebase analysis.
"""

import json
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .analyzer.codebase_analyzer import CodebaseAnalyzer
from .utils.logger import get_logger
from .utils.file_utils import FileUtils

console = Console()
logger = get_logger(__name__)


@click.command()
@click.option('--codebase', '-c', required=True, help='Path to the codebase to analyze')
@click.option('--output', '-o', default='graph', help='Output directory for graph files')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--format', '-f', default='json', type=click.Choice(['json', 'yaml']), help='Output format')
def main(codebase: str, output: str, verbose: bool, format: str):
    """AutoGraph - LLM-powered Hierarchical Codebase Graph Generator"""
    
    if verbose:
        console.print("[bold blue]AutoGraph[/bold blue] - Starting analysis...")
    
    try:
        # Validate codebase path
        if not FileUtils.validate_codebase_path(codebase):
            console.print(f"[red]Error: Invalid codebase path: {codebase}[/red]")
            sys.exit(1)
        
        # Create analyzer
        analyzer = CodebaseAnalyzer()
        
        # Run analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing codebase...", total=None)
            
            result = analyzer.analyze_codebase(codebase)
            
            if not result['success']:
                progress.update(task, description="Analysis failed")
                console.print(f"[red]Analysis failed: {result.get('error', 'Unknown error')}[/red]")
                sys.exit(1)
            
            progress.update(task, description="Analysis completed")
        
        # Display results
        display_results(result, verbose)
        
        # Save results
        save_results(result, output, format)
        
        if verbose:
            console.print(f"\n[green]Analysis completed successfully![/green]")
            console.print(f"Results saved to: {output}/")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def display_results(result: dict, verbose: bool):
    """Display analysis results in a formatted table."""
    stats = result['statistics']
    
    # Create summary table
    table = Table(title="Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Files", str(stats['total_files']))
    table.add_row("Successful Parses", str(stats['successful_parses']))
    table.add_row("Coverage Percentage", f"{stats['coverage_percentage']:.1f}%")
    table.add_row("HLD Nodes", str(stats['hld_nodes']))
    table.add_row("LLD Nodes", str(stats['lld_nodes']))
    table.add_row("Total Edges", str(stats['total_edges']))
    
    console.print(table)
    
    if verbose and result.get('validation_issues'):
        console.print("\n[yellow]Validation Issues:[/yellow]")
        for issue in result['validation_issues']:
            console.print(f"  - {issue}")


def save_results(result: dict, output_dir: str, format: str):
    """Save analysis results to files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save graph as JSON
    graph_file = output_path / f"graph.{format}"
    with open(graph_file, 'w') as f:
        if format == 'json':
            json.dump(result['graph'].dict(), f, indent=2, default=str)
        else:
            # For now, just save as JSON even if YAML is requested
            json.dump(result['graph'].dict(), f, indent=2, default=str)
    
    # Save analysis report
    report_file = output_path / "analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump({
            'success': result['success'],
            'codebase_path': result['codebase_path'],
            'statistics': result['statistics'],
            'validation_issues': result.get('validation_issues', []),
            'timestamp': result['graph'].metadata.analysis_timestamp.isoformat() if result['graph'] else None
        }, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    main() 