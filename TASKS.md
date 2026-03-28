# agentic-slide-filler

## Phase 1: Planning & Setup
- [x] Define technical architecture: select Python as base language, choose `python-pptx` for PPT manipulation, `openai` API (or `anthropic`) for AI generation, and `python-docx` for Word outline parsing; create system architecture diagram
- [x] Set up project structure with `src/`, `tests/`, `templates/`, `output/`, `docs/` directories; initialize Python virtual environment and `requirements.txt` with `python-pptx>=0.6.21`, `openai>=1.0.0`, `python-docx>=0.8.11`
- [x] Create configuration management: implement `config.yaml` for API keys, template paths, and output settings; add `.env.example` template with `OPENAI_API_KEY` placeholder
- [x] Establish Git repository with `.gitignore` for Python, IDE files, and sensitive configs; write initial `README.md` with project overview and setup instructions

## Phase 2: Template & Outline Processing
- [x] Build PPT template parser: create `TemplateParser` class in `src/template_parser.py` that reads `.pptx` files, extracts slide layouts, placeholders, and shape types, returns structured template metadata
- [ ] Implement doc outline parser: develop `OutlineParser` class in `src/outline_parser.py` supporting `.docx` and `.md` formats; extracts headings, sections, and content hierarchy into JSON structure
- [ ] Create content mapping engine: build `ContentMapper` class in `src/content_mapper.py` that aligns outline sections with template slide placeholders using section titles and placeholder tags
- [ ] Add template validation: write unit tests in `tests/test_template_parser.py` that verify placeholder detection, layout identification, and error handling for corrupted templates

## Phase 3: AI Content Generation
- [ ] Design LLM prompt templates: create prompt engineering module in `src/prompts.py` with specialized prompts for title slides, bullet points, charts, and image descriptions; include few-shot examples
- [ ] Build AI content generator: implement `AIContentGenerator` class in `src/ai_generator.py` that calls OpenAI API with temperature control, handles rate limits, and caches responses in `cache/` directory
- [ ] Add content validation and sanitization: create `ContentValidator` in `src/validator.py` that checks generated text for length constraints, formatting rules, and placeholder compatibility
- [ ] Implement fallback mechanisms: add retry logic with exponential backoff, alternative model support (`gpt-4` → `gpt-3.5-turbo`), and error reporting to `logs/` directory

## Phase 4: Integration, Testing & Output
- [ ] Assemble end-to-end pipeline: create main `SlideFiller` class in `src/slide_filler.py` that orchestrates parsing, mapping, generation, and filling; integrate all modules with dependency injection
- [ ] Build output generation: implement `PPTXWriter` in `src/pptx_writer.py` that populates template with AI content, preserves formatting, and saves to `output/` with timestamped filenames
- [ ] Create CLI interface: develop `cli.py` with argparse supporting arguments for template path, outline path, output path, and verbose logging; add `--dry-run` flag for testing
- [ ] Write comprehensive test suite: add integration tests in `tests/test_integration.py` covering full workflow; create `tests/fixtures/` with sample templates and outlines; achieve 80%+ coverage with pytest
