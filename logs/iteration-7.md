# Iteration 7 - agentic-slide-filler

**Timestamp:** Fri Mar 27 11:56:32 PM EDT 2026
**Task:** Build PPT template parser: create `TemplateParser` class in `src/template_parser.py` that reads `.pptx` files, extracts slide layouts, placeholders, and shape types, returns structured template metadata

## Prompt Sent

```
# Project Agent Instructions (Step 3.5 Flash)

## ROLE DETECTION

**CRITICAL**: Before reading further, check your role:
```bash
cat .agent_role
```

**If your role is one of these SPECIALISTS:**
- `devops-engineer` → **STOP & LOAD**: `../../../agents/devops-engineer.md`
- `qa-specialist` → **STOP & LOAD**: `../../../agents/qa-specialist.md`
- `release-manager` → **STOP & LOAD**: `../../../agents/release-manager.md`
- `documentation-specialist` → **STOP & LOAD**: `../../../agents/documentation-specialist.md`
- `project-orchestrator` → **STOP & LOAD**: `../../../agents/project-orchestrator.md`

**If your role is:**
- `generic` → Continue reading this prompt (you're the full-stack developer)

---

**Available specialized agents** (description only, see full prompts in `/agents/`):
- `generic` - Full-stack developer, implement everything
- `devops-engineer` - CI/CD, infrastructure, GitHub Actions
- `qa-specialist` - Testing, quality assurance, test automation
- `release-manager` - Versioning, releases, deployment coordination
- `documentation-specialist` - Docs, READMEs, technical writing
- `project-orchestrator` - Coordination, task assignment, blocking issues

---

## GENERIC DEVELOPER MODE

## CORE MISSION
1. Read `TASKS.md`
2. Complete ONE task per iteration
3. Update `TASKS.md` with progress: Mark completed tasks with `[x]`
4. Commit & push to GitHub
5. Repeat until all tasks done

## CRITICAL: ALWAYS DO FIRST

**Task 0: GitHub Actions Workflow Setup** (Do before Task 1)

Detect tech stack from these files:
| File | Language |
|------|----------|
| `package.json` | Node.js |
| `pyproject.toml` or `requirements.txt` | Python |
| `go.mod` or `go.sum` | Go |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby |
| `pom.xml` or `build.gradle` | Java |
| `Dockerfile` (only) | Docker |
| None | Shell/Unknown |

Create `.github/workflows/test.yml` using the correct template:

<details>
<summary>Node.js Template</summary>

```yaml
name: Test & Validate (Node.js)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ['18.x', '20.x']
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: npm ci
    - run: npm run lint || true
      continue-on-error: true
    - run: npm run build || true
      continue-on-error: true
    - run: npm test || true
      continue-on-error: true
```
</details>

<details>
<summary>Python Template</summary>

```yaml
name: Test & Validate (Python)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - run: pip install uv && uv pip install -e . || uv pip install -r requirements.txt
    - run: pip install pytest && pytest tests/ -v || true
      continue-on-error: true
```
</details>

<details>
<summary>Go Template</summary>

```yaml
name: Test & Validate (Go)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        go-version: ['1.21', '1.22']
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-go@v4
      with:
        go-version: ${{ matrix.go-version }}
    - run: go mod download
    - run: go test -v ./...
```
</details>

<details>
<summary>Rust Template</summary>

```yaml
name: Test & Validate (Rust)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
    - run: cargo fmt -- --check
    - run: cargo test
```
</details>

**Then commit IMMEDIATELY:**
```bash
git add .github/workflows/test.yml TASKS.md
git commit -m "ci: setup github actions workflow"
git push origin main
```

## WORKFLOW (Every Iteration)

1. **Read the current task** from TASKS.md
2. **Understand requirements** - Ask clarifying questions if blocked
3. **Implement** - Write code/docs
4. **Test locally** - Verify it works
5. **Commit** - `git add . && git commit -m "Feature: description" && git push`
6. **Update TASKS.md** - Mark `[x]` when DONE
7. **Next iteration** - Move to next task

## CONSTRAINTS

- ❌ NO virtual environments (`venv`, `virtualenv`, `.venv`) unless absolutely necessary
- ❌ NO docker containers unless absolutely necessary
- ✅ Use system Python/Node.js directly
- ✅ Keep dependencies minimal
- ✅ Write tests alongside code
- ✅ Document all public functions
- ✅ Update README with usage examples

## FILE STRUCTURE
```
.
├── README.md          # How to run the project
├── TASKS.md          # Task list (you update this)
├── .github/workflows/test.yml  # CI pipeline you create
├── requirements.txt / package.json  # Dependencies
└── src/              # Your code
```

## SUCCESS CRITERIA (For Each Task)

✅ Code compiles/runs without errors  
✅ Tests pass locally  
✅ Documented (code comments + README update)  
✅ Committed to GitHub  
✅ Task marked `[x]` in TASKS.md  

## IF YOU GET STUCK

1. **Document the issue** in TASKS.md as a note
2. **Move to next task** - don't block progress
3. **Continue** - come back to it later
4. **Never delete tasks** - mark as blocked with explanation

## GIT WORKFLOW (Exact Commands)

```bash
# After making changes:
git add .
git commit -m "Feature: [brief description]"
git push origin main

# Push any new branches:
git push origin [branch-name]

# Force update after rebasing (only if needed):
git push origin main --force-with-lease
```

## EXECUTION MODE

- Process ONE task per iteration
- Be efficient - no lengthy explanations
- Prefer code over documentation
- Use short, descriptive commit messages
- Push to GitHub after every task completion

---

## ROLE-SPECIFIC QUICK START

### If `.agent_role = qa-specialist`
Load full instructions: `../../../agents/qa-specialist.md`

**Quick mission:**
1. Review TASKS.md for testing-related tasks
2. Create/enhance test files (`tests/`, `__tests__/`, `spec/`)
3. Run test suites locally and validate coverage
4. Update `.github/workflows/test.yml` with test steps
5. Document test setup in README
6. Commit: `git commit -m "test: [what tests you added]"`

### If `.agent_role = devops-engineer`
Load full instructions: `../../../agents/devops-engineer.md`

**Quick mission:**
1. Review TASKS.md for CI/CD and infra tasks
2. Create/enhance `.github/workflows/test.yml` and `deploy-*.yml`
3. Set up GitHub environments if needed
4. Test workflows locally with `act` tool (optional)
5. Document deployment process in README
6. Commit: `git commit -m "ci: [workflow changes]"`

### If `.agent_role = release-manager`
Load full instructions: `../../../agents/release-manager.md`

**Quick mission:**
1. Review TASKS.md for version/release tasks
2. Update version numbers in files (`package.json`, `setup.py`, etc.)
3. Create/update CHANGELOG or release notes
4. Tag releases: `git tag -a v1.0.0 -m "Release 1.0.0"`
5. Push tags: `git push origin --tags`
6. Commit: `git commit -m "chore: bump version to v1.0.0"`

### If `.agent_role = documentation-specialist`
Load full instructions: `../../../agents/documentation-specialist.md`

**Quick mission:**
1. Review TASKS.md for docs-related tasks
2. Update/expand README.md with usage examples
3. Add API/function documentation (docstrings)
4. Create/update CONTRIBUTING.md, SETUP.md, TROUBLESHOOTING.md
5. Validate all code examples work
6. Commit: `git commit -m "docs: [what documentation you added]"`

### If `.agent_role = project-orchestrator`
Load full instructions: `../../../agents/project-orchestrator.md`

**Quick mission:**
1. Review TASKS.md and identify blockers/dependencies
2. Plan which tasks can run in parallel
3. Assign work to specialists (update `.agent_role` as needed)
4. Track progress and update status
5. Escalate blockers and risks
6. Commit: `git commit -m "chore: priority update - [what changed]"`

---

## CALLING SPECIALIZED AGENTS

If a task needs a specialist you can't handle alone, update `.agent_role`:

```bash
# Switch to a specialist for specific work
echo "devops-engineer" > .agent_role
git add .agent_role
git commit -m "ops: switch to devops-engineer for CI/CD setup"
git push origin main
```

After switching, the next iteration will load that agent's expertise.

**Common task-to-agent mappings:**
- Implementing feature → Stay as `generic`
- Need tests? → Switch to `qa-specialist`
- Ready to release? → Switch to `release-manager`
- Need better docs? → Switch to `documentation-specialist`
- Complex multi-part work? → Switch to `project-orchestrator`
- Setting up CI/CD? → Switch to `devops-engineer`

Switch back to `generic` when the specialist work is done.

---

**Now start: Check `.agent_role` and read TASKS.md**

---

### ⚠️ CRITICAL TOKEN CONSTRAINTS:
- Iteration: 7 / 64k Token Budget
- Attempt: 1 (previous attempts may have partial progress)
- **Mandate:** Operate efficiently. Use partial edits, not full file rewrites when possible.
- **Output:** Be concise and action-oriented.


## CURRENT PROJECT STATE (Iteration 7)

```
# agentic-slide-filler

## Phase 1: Planning & Setup
- [x] Define technical architecture: select Python as base language, choose `python-pptx` for PPT manipulation, `openai` API (or `anthropic`) for AI generation, and `python-docx` for Word outline parsing; create system architecture diagram
- [x] Set up project structure with `src/`, `tests/`, `templates/`, `output/`, `docs/` directories; initialize Python virtual environment and `requirements.txt` with `python-pptx>=0.6.21`, `openai>=1.0.0`, `python-docx>=0.8.11`
- [x] Create configuration management: implement `config.yaml` for API keys, template paths, and output settings; add `.env.example` template with `OPENAI_API_KEY` placeholder
- [x] Establish Git repository with `.gitignore` for Python, IDE files, and sensitive configs; write initial `README.md` with project overview and setup instructions

## Phase 2: Template & Outline Processing
- [ ] Build PPT template parser: create `TemplateParser` class in `src/template_parser.py` that reads `.pptx` files, extracts slide layouts, placeholders, and shape types, returns structured template metadata
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
```

## NEXT TASK TO COMPLETE:
Build PPT template parser: create `TemplateParser` class in `src/template_parser.py` that reads `.pptx` files, extracts slide layouts, placeholders, and shape types, returns structured template metadata

**Instructions:** Complete this task. Mark [x] in TASKS.md when done. Create, modify, or delete files as needed. Execute commands as needed. Also update README.md to match this project (name, setup instructions, current progress). No permission needed—just act.
```

## OpenCode Output

```
[0m
> build · stepfun/step-3.5-flash:free
[0m
I'll build the PPT template parser component. Let me first explore the project structure and check what's already in place.
[0m→ [0mRead TASKS.md
[0m→ [0mRead requirements.txt
[0m
[0m$ [0mls -la
total 96
drwxr-xr-x 10 julien julien 4096 Mar 27 23:53 .
drwxr-xr-x 33 julien julien 4096 Mar 27 23:49 ..
-rw-r--r--  1 julien julien    8 Mar 27 23:50 .agent_role
-rw-r--r--  1 julien julien  181 Mar 27 23:49 .coderabbit.yaml
-rw-r--r--  1 julien julien  871 Mar 27 23:54 config.yaml
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 docs
-rw-r--r--  1 julien julien  254 Mar 27 23:54 .env.example
drwxr-xr-x  7 julien julien 4096 Mar 27 23:56 .git
drwxr-xr-x  3 julien julien 4096 Mar 27 23:49 .github
-rw-r--r--  1 julien julien  476 Mar 27 23:53 .gitignore
drwxr-xr-x  2 julien julien 4096 Mar 27 23:56 logs
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 output
-rw-r--r--  1 julien julien 9218 Mar 27 23:49 prompt.txt
-rw-r--r--  1 julien julien 5653 Mar 27 23:54 README.md
-rw-r--r--  1 julien julien   66 Mar 27 23:53 requirements.txt
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 src
-rw-r--r--  1 julien julien 3341 Mar 27 23:56 TASKS.md
-rw-r--r--  1 julien julien 3341 Mar 27 23:50 TASKS_original.md
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 templates
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 tests
-rw-r--r--  1 julien julien    6 Mar 27 23:50 .worker_persistent_mode
[0m
[0m$ [0mls -la src/ tests/
src/:
total 8
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 .
drwxr-xr-x 10 julien julien 4096 Mar 27 23:53 ..

tests/:
total 8
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 .
drwxr-xr-x 10 julien julien 4096 Mar 27 23:53 ..
[0m
[0m→ [0mRead README.md
[0m
[0m$ [0mls -la templates/
total 8
drwxr-xr-x  2 julien julien 4096 Mar 27 23:52 .
drwxr-xr-x 10 julien julien 4096 Mar 27 23:53 ..
[0m
[0m# [0mTodos
[ ] Design TemplateParser class structure and API
[ ] Implement template parsing with python-pptx
[ ] Create unit tests for TemplateParser
[ ] Create test fixtures (sample PPTX templates)
[ ] Run tests and verify functionality
[0m
Now I'll create the `TemplateParser` class. First, let me create a todo list for this task:
[0m← [0mWrite src/template_parser.py
Wrote file successfully.

LSP errors detected in this file, please fix:
<diagnostics file="/home/julien/Desktop/Free-Wiggum-opencode/projects/agentic-slide-filler/src/template_parser.py">
ERROR [8:10] Import "pptx" could not be resolved
ERROR [9:10] Import "pptx.enum.shapes" could not be resolved
ERROR [85:63] "slide_layouts" is not a known attribute of "None"
</diagnostics>
[0m
[0m# [0mTodos
[x] Design TemplateParser class structure and API
[x] Implement template parsing with python-pptx
[ ] Create unit tests for TemplateParser
[ ] Create test fixtures (sample PPTX templates)
[ ] Install dependencies and run tests
[0m
```

## TASKS.md After Iteration

```markdown
# agentic-slide-filler

## Phase 1: Planning & Setup
- [x] Define technical architecture: select Python as base language, choose `python-pptx` for PPT manipulation, `openai` API (or `anthropic`) for AI generation, and `python-docx` for Word outline parsing; create system architecture diagram
- [x] Set up project structure with `src/`, `tests/`, `templates/`, `output/`, `docs/` directories; initialize Python virtual environment and `requirements.txt` with `python-pptx>=0.6.21`, `openai>=1.0.0`, `python-docx>=0.8.11`
- [x] Create configuration management: implement `config.yaml` for API keys, template paths, and output settings; add `.env.example` template with `OPENAI_API_KEY` placeholder
- [x] Establish Git repository with `.gitignore` for Python, IDE files, and sensitive configs; write initial `README.md` with project overview and setup instructions

## Phase 2: Template & Outline Processing
- [ ] Build PPT template parser: create `TemplateParser` class in `src/template_parser.py` that reads `.pptx` files, extracts slide layouts, placeholders, and shape types, returns structured template metadata
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
```

**Completed at:** Fri Mar 27 11:57:28 PM EDT 2026
