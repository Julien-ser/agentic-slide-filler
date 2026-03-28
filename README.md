# Agentic Slide Filler

An AI-powered tool that automatically generates professional PowerPoint presentations from document outlines using LLMs.

## Architecture

### Technology Stack
- **Language**: Python 3.11+
- **PPT Manipulation**: `python-pptx` (>=0.6.21)
- **AI Generation**: OpenAI API (GPT-4/3.5) or Anthropic API
- **Document Parsing**: `python-docx` (>=0.8.11), Markdown support
- **CLI**: argparse
- **Testing**: pytest

### System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Files   │    │   AI Content     │    │   Output File   │
│  • Template     │───▶│   Generation     │───▶│  • presentation │
│  • Outline       │    │                  │    │    .pptx        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▲
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ TemplateParser  │    │  AIContent       │    │   PPTXWriter    │
│ • Layout extract│    │  Generator       │    │ • Populate      │
│ • Placeholders  │    │ • API calls      │    │ • Formatting    │
└─────────────────┘    │ • Rate limiting  │    └─────────────────┘
         │              │ • Caching        │            │
         ▼              └──────────────────┘            │
┌─────────────────┘                ▲                   │
│ OutlineParser    │                │                   │
│ • Docx/MD parse  │───────────────┘                   │
│ • Hierarcy JSON  │                                    │
└─────────────────┘                                    │
         │                                              │
         └────────────────┬─────────────────────────────┘
                          ▼
              ┌─────────────────────┐
              │   ContentMapper     │
              │ • Section align     │
              │ • Placeholder match │
              └─────────────────────┘
```

### Data Flow
1. **Parse Template**: Extract slide layouts, placeholders, and shape types
2. **Parse Outline**: Convert document (DOCX/MD) to hierarchical content structure
3. **Map Content**: Align outline sections with appropriate template placeholders
4. **Generate AI Content**: Call LLM API with prompts to generate slide content
5. **Validate Content**: Check length, formatting, and compatibility
6. **Write PPTX**: Populate template with generated content and save

## Setup

```bash
# Install dependencies
pip install python-pptx openai python-docx pytest PyYAML python-dotenv

# Or with requirements.txt
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Optional: customize configuration
# Copy and modify config.yaml as needed
cp config.yaml config.local.yaml

# Run the tool
python -m src.cli --template template.pptx --outline outline.docx --output presentation.pptx
```

## Configuration

The application supports configuration through:

**Environment Variables** (`.env` file):
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `ANTHROPIC_API_KEY` - Anthropic API key (optional, for Claude)

**Configuration File** (`config.yaml` or `config.local.yaml`):
- OpenAI model settings (model name, temperature, max tokens)
- File paths (templates, output, cache, logs)
- Output filename patterns
- Content generation parameters (retry attempts, caching)
- Logging configuration

Configuration precedence: environment variables > `config.local.yaml` > `config.yaml`

## Project Structure

```
.
├── README.md              # This file
├── TASKS.md               # Development progress
├── requirements.txt       # Python dependencies
├── config.yaml            # Application configuration
├── config.local.yaml      # Local overrides (optional)
├── .env.example          # Environment variable template
├── .env                  # Local environment variables (gitignored)
├── src/                  # Source code
│   ├── template_parser.py
│   ├── outline_parser.py
│   ├── content_mapper.py
│   ├── ai_generator.py
│   ├── validator.py
│   ├── pptx_writer.py
│   ├── slide_filler.py
│   ├── prompts.py
│   └── cli.py
├── tests/                # Test suite
├── templates/            # Sample PPT templates
├── output/               # Generated presentations
├── cache/                # LLM response cache
└── logs/                 # Application logs
```

## Current Status

✅ **Phase 1**: Planning & Setup - Complete
🔄 **Phase 2**: Template & Outline Processing - In Progress

### Completed
- ✅ Template parser (`src/template_parser.py`): Extracts slide layouts, placeholders, and metadata from PPTX templates
- ✅ Outline parser (`src/outline_parser.py`): Extracts hierarchical content from DOCX and Markdown documents
- ✅ Content mapper (`src/content_mapper.py`): Aligns outline sections with template placeholders using intelligent matching
- ✅ Comprehensive unit tests (`tests/test_template_parser.py`) covering placeholder detection, layout identification, and error handling
- ✅ Comprehensive unit tests (`tests/test_outline_parser.py`) covering DOCX/Markdown parsing, hierarchy extraction, and error handling

### In Progress
- 🔄 Adding template validation

### Up Next
- Design LLM prompt templates (`src/prompts.py`)
- Build AI content generator (`src/ai_generator.py`)
