"""Command-line interface for SlideFiller."""

import argparse
import sys
from pathlib import Path

from src.slide_filler import SlideFiller

logger = None  # Will be configured by SlideFiller if needed


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate presentation slides from an outline using AI and a PPTX template"
    )

    parser.add_argument(
        "-t",
        "--template",
        required=True,
        help="Path to the PowerPoint template (.pptx)",
    )
    parser.add_argument(
        "-o",
        "--outline",
        required=True,
        help="Path to the outline document (.docx or .md)",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        help="OpenAI API key (if not provided, uses OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "-d",
        "--output-dir",
        default="output",
        help="Output directory for generated presentation (default: output/)",
    )
    parser.add_argument(
        "-c",
        "--cache-dir",
        default="cache",
        help="Cache directory for AI responses (default: cache/)",
    )
    parser.add_argument(
        "-m",
        "--mapping-strategy",
        choices=["auto", "sequential", "hierarchical"],
        default="auto",
        help="Content mapping strategy (default: auto)",
    )
    parser.add_argument(
        "-n",
        "--output-name",
        help="Output filename (without extension). If not provided, uses timestamp",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="AI generation temperature, 0.0-1.0 (default: 0.7)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4",
        help="Primary OpenAI model (default: gpt-4)",
    )
    parser.add_argument(
        "--fallback-model",
        default="gpt-3.5-turbo",
        help="Fallback OpenAI model (default: gpt-3.5-turbo)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts for API calls (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without generating content or writing files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    try:
        # Create SlideFiller instance
        filler = SlideFiller(
            template_path=args.template,
            outline_path=args.outline,
            api_key=args.api_key,
            output_dir=args.output_dir,
            cache_dir=args.cache_dir,
            mapping_strategy=args.mapping_strategy,
            ai_temperature=args.temperature,
            ai_model=args.model,
            ai_fallback_model=args.fallback_model,
            ai_max_retries=args.max_retries,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

        # Run the pipeline
        output_path = filler.run(output_name=args.output_name)

        # Print mapping report
        print("\n" + filler.get_mapping_report())

        if not args.dry_run:
            print(f"\n✅ Presentation generated: {output_path}")
        else:
            print("\n✅ Dry run completed successfully")

        return 0

    except FileNotFoundError as e:
        print(f"❌ File error: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        print(f"❌ Pipeline error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n❌ Interrupted by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
