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
pip install python-pptx openai python-docx pytest PyYAML

# Or with requirements.txt
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the tool
python -m src.cli --template template.pptx --outline outline.docx --output presentation.pptx
```

## Project Structure

```
.
├── README.md              # This file
├── TASKS.md               # Development progress
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
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

✅ **Phase 1**: Planning & Setup - In Progress

Next: Set up project structure and configuration management.
