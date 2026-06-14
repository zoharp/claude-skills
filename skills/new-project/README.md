# New Project Skill

Automated end-to-end project setup for Orcanos environment.

## Overview

This skill automates the entire project creation workflow:
1. **Design Review** — Spec review and implementation planning
2. **Code Generation** — Code creation and review
3. **Testing** — Automated test suite setup and execution
4. **Database** — SQL setup scripts
5. **Deployment** — Environment configuration and deployment
6. **Release Management** — Version tracking and release notes

## Installation

Copy this folder to `C:\Users\zohar\.claude\skills\new-project`

Or use directly from current location:
```bash
node C:\AI Projects\new-project-skill\index.js
```

## Usage

Navigate to your project folder and run:

```bash
npx claude
/new-project
```

Or directly:
```bash
node path/to/new-project-skill/index.js
```

## Requirements

Your project folder must have:
```
your-project/
├── design/
│   └── design.md    (your project design specification)
```

## What It Creates

The skill generates:

### Documentation
- `CLAUDE.md` — Project overview and configuration
- `SCHEMA.md` — Database schema template
- `ARCHITECTURE.md` — Architecture template
- `SECURITY.md` — Security guidelines template
- `DEPLOYMENT.md` — Deployment guide template
- `TESTING.md` — Testing guide template

### Design Phase Files (in /design)
- `spec-review.md` — Specification review
- `implementation-plan.md` — Implementation strategy
- `implementation-plan-review.md` — Plan validation
- `code-review.md` — Code review template
- `database-setup.md` — SQL setup scripts

### Project Structure
- `/src` — Source code directory
- `/tests` — Test files with 11+ test placeholders
- `.env.example` — Environment configuration template
- `release_notes.json` — Release tracking

### Run Scripts (Windows .bat files)
- `run_dev.bat` — Start development environment
- `run_test.bat` — Run test suite
- `run_deploy.bat` — Build for production

## Workflow

1. **Create project folder** with `/design/design.md`
2. **Run the skill** — Creates all structure and templates
3. **Claude AI completes**:
   - Spec review and recommendations
   - Implementation planning and validation
   - Code generation and review
   - Test suite expansion
   - Database schema generation
   - Release notes management
4. **Deploy** — Use run scripts and generated configs

## Configuration

The skill reads from your project's `/design/design.md` file and generates all necessary configuration files.

After generation:
1. Update `.env.example` with your values → `.env`
2. Configure database connection in `.env`
3. Run `.\run_dev.bat` to start
4. Run `.\run_test.bat` to test

## GitHub Integration

The skill automatically:
- Detects folder name as GitHub repo name
- Generates format: `https://github.com/zoharp/[folder-name]`
- Updates CLAUDE.md with correct repo URL

Assumes GitHub repository already exists.

## Skills Used

This skill references and works with:
- `/spec-review` — Specification review
- `/implementation-plan-review` — Plan validation
- `/code-review` — Code quality review
- `/release-management` — Version management
- `/deploy` — Deployment automation

## Environment

- Windows PowerShell / Batch scripts
- Node.js 18+ (for running npm scripts)
- Git (for version control)
- Supabase or PostgreSQL (for database)

## Design File Format

Your `/design/design.md` should contain:
- Project overview
- Technology stack
- Features and requirements
- Database needs
- API specifications
- Deployment requirements
- Security requirements
- Testing strategy

See example in this skill's parent directory.

## Next Steps After Generation

1. Review generated documentation in `/design` folder
2. Answer any questions Claude AI asks during review
3. Run through implementation plan validation
4. Generate code based on approved plan
5. Write and run tests
6. Setup database
7. Configure for deployment
8. Deploy!

---

Generated files are ready for Claude AI to enhance and complete.
