# New Project Skill — Claude Code Instructions

## Overview

**new-project-skill** is an end-to-end project automation skill that scaffolds, develops, tests, and deploys new Orcanos projects. It orchestrates the complete lifecycle from design review through production readiness.

**Repository**: `https://github.com/zoharp/new-project-skill`
**Location**: `C:\AI Projects\new-project-skill`

---

## What This Skill Does

When invoked in a project folder with `/design/design.md`:

1. **Scaffolds Project Structure** — Creates directories, documentation templates, and configuration files
2. **Design Review Phase** — Runs spec-review, implementation planning, and plan validation
3. **Code Generation** — Generates source code based on approved implementation plan
4. **Code Review** — Reviews code for quality, security, and correctness
5. **Database Setup** — Creates SQL scripts for database initialization
6. **Test Automation** — Writes 10+ automated tests and runs them
7. **Going Live** — Collects deployment info and creates environment config
8. **Release Management** — Initializes release notes and version tracking

---

## How to Use This Skill

### Prerequisites

Your project folder must exist with a design specification:

```
your-project-name/
└── design/
    └── design.md    (your project design specification)
```

### Invoking the Skill

Navigate to your project folder and run:

```bash
cd C:\path\to\your-project
npx claude
/new-project
```

Or trigger programmatically:

```bash
node C:\AI Projects\new-project-skill\index.js
```

### The Skill Execution Flow

1. **Validation** — Checks for `/design` folder and design.md file
2. **Scaffolding** — Creates project structure and documentation
3. **Logging** — Logs every step to `logs/` folder with timestamps
4. **Generation** — Creates all necessary files (CLAUDE.md, test templates, run scripts)
5. **Handoff** — Returns control to Claude AI for design review and code generation

---

## Output Files

The skill generates these files:

### Documentation (Project Root)

- **CLAUDE.md** — Project overview and Claude AI instructions
- **SCHEMA.md** — Database schema template (filled by Claude)
- **ARCHITECTURE.md** — System architecture template
- **SECURITY.md** — Security guidelines template
- **DEPLOYMENT.md** — Deployment guide template
- **TESTING.md** — Testing strategy template

### Design Phase Files (`/design`)

- **spec-review.md** — Specification review findings
- **implementation-plan.md** — Detailed implementation strategy
- **implementation-plan-review.md** — Plan validation results
- **code-review.md** — Code quality findings
- **database-setup.md** — SQL scripts for database creation

### Project Structure

- **`/src`** — Source code directory (to be filled by Claude)
- **`/tests`** — Test files with 11 placeholder tests
- **`/logs`** — Skill execution logs with timestamps

### Configuration & Scripts

- **`.env.example`** — Environment variables template
- **`release_notes.json`** — Release tracking (v0.1.0 initialized)
- **`run_dev.bat`** — Start development environment
- **`run_test.bat`** — Run test suite
- **`run_deploy.bat`** — Build for production

---

## Logging Architecture

Every step the skill performs is logged to `logs/` folder:

**Log File Format**: `skill-run-2026-06-09T14-30-45-123Z.log`

**Log Entry Format**: 
```
[2026-06-09T14:30:45.123Z] [STEP] 1: Initialization
[2026-06-09T14:30:45.234Z] 📁 Location: C:\projects\my-app
[2026-06-09T14:30:45.345Z] ✓ Created directory: src
[2026-06-09T14:30:46.456Z] ❌ ERROR: /design folder not found
```

**Log Types**:
- `[STEP] N: Description` — Major phase boundaries
- `✓ Message` — Successful operations
- `❌ ERROR: Message` — Errors and failures
- `[timestamp] Message` — Informational logs

---

## Skills Referenced

This skill works with and references these Claude skills (from `~/.claude/skills/`):

- **`spec-review`** — Reviews technical specifications for feasibility and completeness
- **`implementation-plan-review`** — Validates implementation plans before coding
- **`code-review`** — Reviews generated code for quality, security, and correctness
- **`release-management`** — Manages version numbers and release notes
- **`deploy`** — Handles GitHub commits and deployment automation
- **`test-automation`** — Assists with test suite setup and validation

---

## Project Folder Structure

After the skill runs, your project will have:

```
your-project/
├── CLAUDE.md                          # Project instructions
├── SCHEMA.md                          # Database schema
├── ARCHITECTURE.md                    # System architecture
├── SECURITY.md                        # Security guidelines
├── DEPLOYMENT.md                      # Deployment procedures
├── TESTING.md                         # Testing guide
├── README.md                          # Project overview (user-facing)
├── package.json                       # Node.js config (if applicable)
│
├── src/                               # Source code (to be created by Claude)
│   ├── index.js                       # Entry point
│   ├── api/                           # API endpoints
│   ├── models/                        # Data models
│   ├── services/                      # Business logic
│   └── config/                        # Configuration
│
├── tests/                             # Test suite
│   └── suite.test.js                  # 11+ tests (filled by Claude)
│
├── design/                            # Design documentation
│   ├── design.md                      # Original design specification
│   ├── spec-review.md                 # Claude's review findings
│   ├── implementation-plan.md         # Detailed implementation strategy
│   ├── implementation-plan-review.md  # Plan validation results
│   ├── code-review.md                 # Code review findings
│   └── database-setup.md              # SQL initialization scripts
│
├── logs/                              # Execution logs
│   ├── skill-run-2026-06-09T...log    # Timestamped logs
│   └── skill-run-2026-06-09T...log
│
├── .claude/                           # Claude Code config
│   └── settings.json                  # Project settings
│
├── .env.example                       # Environment template
├── .env                               # Environment config (created at runtime)
├── .gitignore                         # Git ignore rules
├── release_notes.json                 # Version & release tracking
│
├── run_dev.bat                        # Start development environment
├── run_test.bat                       # Run tests
└── run_deploy.bat                     # Build for production
```

---

## GitHub Integration

The skill automatically detects the folder name and generates the GitHub URL:

```
Folder: my-awesome-app
GitHub: https://github.com/zoharp/my-awesome-app
```

**Assumption**: The GitHub repository already exists. Create it first on GitHub.com if needed.

---

## Claude AI Workflow After Skill Runs

After the skill scaffolds the project, Claude AI performs these phases:

### Phase 1: Design Review (File: `/design/spec-review.md`)

```
1. Read /design/design.md
2. Run /spec-review with the design content
3. Save findings to /design/spec-review.md
4. Ask clarifying questions if needed
```

**Skills Used**: `/spec-review`

### Phase 2: Implementation Planning (File: `/design/implementation-plan.md`)

```
1. Read design.md and spec-review.md
2. Create detailed implementation plan with:
   - Phases and milestones
   - Task breakdown and dependencies
   - Resource requirements
   - Risk assessment and mitigation
   - Success criteria
3. Save to /design/implementation-plan.md
```

### Phase 3: Plan Validation (File: `/design/implementation-plan-review.md`)

```
1. Run /implementation-plan-review with implementation-plan.md
2. Validate feasibility, timeline, and dependencies
3. Save review results to /design/implementation-plan-review.md
4. Create revised implementation plan incorporating feedback
```

**Skills Used**: `/implementation-plan-review`

### Phase 4: Code Generation (Directory: `/src`)

```
1. Generate source code based on approved plan
2. Create directory structure matching architecture
3. Generate core files, APIs, models, services
4. Create configuration and example files
```

### Phase 5: Code Review (File: `/design/code-review.md`)

```
1. Run /code-review on all /src files
2. Check for:
   - Security vulnerabilities
   - Performance issues
   - Code quality and style
   - Best practices adherence
3. Save findings to /design/code-review.md
4. Fix all critical and major issues
```

**Skills Used**: `/code-review`

### Phase 6: Database Setup (File: `/design/database-setup.md`)

```
1. Design complete database schema
2. Create SQL scripts for:
   - CREATE TABLE statements
   - Indexes and constraints
   - Foreign key relationships
   - Seed data (if needed)
3. Format for copy-paste into Supabase/PostgreSQL
4. Save to /design/database-setup.md
```

### Phase 7: Test Automation (File: `/tests/suite.test.js`)

```
1. Write 10+ tests covering:
   - Core functionality
   - Edge cases
   - Integration points
   - Error handling
2. Run tests
3. Fix failures until all pass
```

### Phase 8: Going Live (Files: `.env`, `.env.example`)

```
1. Ask user for deployment configuration:
   - Supabase credentials
   - LLM API keys (if needed)
   - Application settings
2. Create .env file with provided values
3. Verify database setup
4. Create deployment checklist
```

### Phase 9: Release Management

```
1. Initialize release_notes.json
2. Document version strategy
3. Create release checklist
```

**Skills Used**: `/release-management`

---

## Key Configuration Points

### environment Variables (`.env.example`)

The skill creates a template with these sections:

```env
# Database Configuration
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# LLM Configuration (if applicable)
LLM_API_KEY=
LLM_MODEL=claude-opus-4-1

# Application Configuration
NODE_ENV=development
APP_URL=http://localhost:3000
APP_PORT=3000
APP_DEBUG=false
```

Update `.env.example` as needed, then copy to `.env` and fill in values.

### Run Scripts (Windows Batch)

- **`run_dev.bat`** — Kills node.exe, installs deps, starts backend, opens browser
- **`run_test.bat`** — Runs `npm test`
- **`run_deploy.bat`** — Runs `npm run build` and reports success/failure

### Package.json Scripts

Expected npm scripts in generated projects:

```json
{
  "scripts": {
    "dev": "node src/index.js",
    "test": "jest",
    "build": "npm run build",
    "start": "node build/index.js"
  }
}
```

---

## When to Modify This Skill

Edit `index.js` when:

1. **Changing File Templates** — Update the template strings in index.js
2. **Adding New Generated Files** — Add to the `docs` object or create new sections
3. **Modifying Logging** — Edit `log()`, `logStep()`, `logSuccess()`, `logError()` functions
4. **Adjusting Directory Structure** — Modify the `dirs` array or add new directories
5. **Changing Log Location** — Update the `logsDir` path

---

## Troubleshooting

### Skill Fails: "/design folder not found"

**Cause**: Project folder doesn't have a `/design` subdirectory

**Fix**:
```bash
mkdir design
# Create your design.md in this folder
```

### Files Already Exist

**Behavior**: The skill checks if files exist before writing. Existing files are skipped.

**Fix**: Delete conflicting files or rename them before running the skill again.

### Logs Not Writing

**Cause**: `logs/` directory can't be created (permission issue)

**Fix**: Check folder permissions or run as administrator

---

## Maintenance & Updates

### Updating File Templates

To change what files the skill generates:

1. Open `C:\AI Projects\new-project-skill\index.js`
2. Find the relevant template string (e.g., `claudeContent`, `docs`, `specReview`)
3. Edit the template
4. Test by running the skill in a test project

### Adding New Generated Files

Example: Add a `CI.md` file for CI/CD documentation:

```javascript
// In the docs object, add:
'CI.md': `# Continuous Integration

[CI configuration content]
`,

// Then in the summary section, add:
log('  ✓ CI.md - CI/CD documentation');
```

---

## Design File Requirements

Your `/design/design.md` should include:

```markdown
# Project Design

## Overview
What the project does and why

## Technology Stack
Languages, frameworks, databases, APIs

## Features & Requirements
List of features and user stories

## Data Model
Database tables and relationships

## API Specification
Endpoints, request/response formats

## Security Requirements
Authentication, authorization, data protection

## Deployment
Target environment, CI/CD strategy

## Testing Strategy
Unit tests, integration tests, E2E tests

## Success Criteria
How to know the project is complete
```

---

## Integration with GitHub

**Repository Format**:
```
https://github.com/zoharp/[project-folder-name]
```

**Assumption**: Repository must exist before running the skill.

**Setup**:
1. Create repository on GitHub.com
2. Clone locally to `C:\path\to\project`
3. Create `/design/design.md`
4. Run `/new-project` skill

---

## Release Notes Management

The skill initializes `release_notes.json` in v0.1.0 format:

```json
{
  "version": "0.1.0",
  "releases": [
    {
      "version": "0.1.0",
      "date": "2026-06-09T...",
      "type": "initial",
      "features": [...],
      "bugFixes": [],
      "notes": "Initial project setup"
    }
  ]
}
```

Use `/release-management` skill to update versions and add release notes.

---

## Next Steps

1. **Create your project folder** with `/design/design.md`
2. **Run `/new-project`** from the project folder
3. **Answer questions** Claude asks during design review
4. **Review design documents** in `/design` folder
5. **Approve implementation plan** before coding begins
6. **Monitor test execution** and fix failures
7. **Review deployment configuration**
8. **Deploy using run scripts**

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/new-project` | Scaffold and initialize project |
| `/spec-review` | Review design specification |
| `/implementation-plan-review` | Validate implementation plan |
| `/code-review` | Review generated code |
| `/release-management` | Update versions and release notes |
| `.\run_dev.bat` | Start development environment |
| `.\run_test.bat` | Run test suite |
| `.\run_deploy.bat` | Build for production |

---

## Support & Issues

- **Logs**: Check `logs/` folder for detailed execution records
- **Skill Errors**: Review the skill-run-*.log file with timestamps
- **Design Issues**: Review `/design/spec-review.md` for findings
- **Code Issues**: Check `/design/code-review.md` for issues

---

Generated by new-project-skill automation framework
