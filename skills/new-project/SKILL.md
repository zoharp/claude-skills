---
name: new-project
description: End-to-end project creation - design review, implementation planning, code generation, testing, database setup, and deployment configuration for Orcanos environment
license: MIT
revision: 1.0
---

# New Project Skill

Create, code, test, and deploy complete new projects in Orcanos environment end-to-end.

## Prerequisites

Your project folder must contain:
```
your-project/
└── design/
    └── design.md    (your project design specification)
```

## Full Lifecycle Workflow

This skill automates the complete project creation process:

1. **Setup** — Create project structure and scaffold
2. **Design Phase** — Review spec, create & validate implementation plan
3. **Code Phase** — Generate code, review, and fix issues
4. **Database** — Create database setup SQL scripts
5. **Testing** — Write 10+ automated tests, run, and fix
6. **Deployment** — Setup deployment configuration
7. **Release** — Initialize release notes and version management

---

## Phase 1: Project Initialization

### Step 1.1: Scaffold Project Structure

Run the Node.js initialization script to create the project structure:

```bash
node "C:\AI Projects\new-project-skill\index.js"
```

This creates:
- Directory structure (`src/`, `tests/`, `design/`, `.claude/`)
- Documentation files (`CLAUDE.md`, `SCHEMA.md`, `ARCHITECTURE.md`, etc.)
- Design phase templates (`spec-review.md`, `implementation-plan.md`, etc.)
- Test suite template (`tests/suite.test.js`)
- Run scripts (`run_dev.bat`, `run_test.bat`, `run_deploy.bat`)
- Configuration template (`.env.example`)
- Release notes file (`release_notes.json`)

### Step 1.2: Confirm Project Setup

Verify all files were created successfully. You should see:
- ✓ CLAUDE.md
- ✓ SCHEMA.md, ARCHITECTURE.md, SECURITY.md, DEPLOYMENT.md, TESTING.md
- ✓ design/spec-review.md
- ✓ design/implementation-plan.md
- ✓ design/implementation-plan-review.md
- ✓ design/code-review.md
- ✓ design/database-setup.md
- ✓ tests/suite.test.js
- ✓ run_dev.bat, run_test.bat, run_deploy.bat
- ✓ .env.example
- ✓ release_notes.json

---

## Phase 2: Design Review & Planning

### Step 2.1: Read and Analyze Design

Read the design specification from `/design/design.md`:

**Task**: Read the design file and understand:
- Project overview and goals
- Technology stack and architecture
- Features and requirements
- Data model and database needs
- API specifications
- Security requirements
- Deployment strategy
- Testing requirements

### Step 2.2: Run Specification Review

Use the `/spec-review` skill to review the design specification.

**Instructions for Claude**:
1. Read the design file from `/design/design.md`
2. Execute `/spec-review` with the design content
3. Analyze:
   - Architecture clarity and feasibility
   - Technology stack appropriateness
   - API/interface design
   - Database design
   - Security considerations
   - Performance requirements
   - Scalability approach
   - Error handling strategy
   - Testing strategy
4. Save the spec review results to `/design/spec-review.md`
5. Include findings, issues, and recommendations

### Step 2.3: Ask Clarifying Questions (if needed)

If the design is incomplete or ambiguous, ask the user questions about:
- Missing technology decisions
- Unclear feature requirements
- Database schema specifics
- API endpoint details
- Security/compliance needs
- Performance targets

### Step 2.4: Create Implementation Plan

Based on the design and spec review results:

**Task**: Create a detailed implementation plan:
1. Break down into phases (Foundation, Core Features, Integration, Testing, Deployment)
2. Identify all tasks and subtasks
3. Map dependencies between tasks
4. Estimate timeline
5. Identify resource requirements
6. Assess risks and mitigation strategies
7. Define success criteria
8. List external dependencies
9. Document key assumptions

Save to `/design/implementation-plan.md`

### Step 2.5: Run Implementation Plan Review

Use the `/implementation-plan-review` skill to validate the implementation plan.

**Instructions for Claude**:
1. Execute `/implementation-plan-review` with the implementation plan
2. Check:
   - Feasibility of all phases
   - Completeness of coverage
   - Proper task sequencing and dependencies
   - Resource adequacy
   - Timeline realism
   - Risk identification and mitigation
   - Rollback strategy adequacy
   - Testing coverage
3. Save results to `/design/implementation-plan-review.md`
4. Include critical issues, major issues, and recommendations

### Step 2.6: Revise Implementation Plan

Based on the plan review:

**Task**: Update `/design/implementation-plan.md`:
1. Incorporate recommendations from the plan review
2. Adjust timeline if needed
3. Add missing phases or tasks
4. Clarify dependencies
5. Enhance risk mitigation strategies
6. Update success criteria

---

## Phase 3: Code Generation & Review

### Step 3.1: Generate Source Code

Based on the approved implementation plan:

**Task**: Generate complete source code:
1. Create `/src` directory structure matching the architecture
2. Generate core application files
3. Implement features according to design
4. Create configuration files
5. Setup build and run configurations
6. Create example files and boilerplate code
7. Document code structure

Follow the technology stack specified in design (Node.js, React, FastAPI, etc.)

### Step 3.2: Run Code Review

Use the `/code-review` skill to review generated code.

**Instructions for Claude**:
1. Execute `/code-review` on all source files in `/src`
2. Review for:
   - Correctness and logic errors
   - Code quality and style
   - Security vulnerabilities
   - Performance issues
   - Test coverage gaps
   - Documentation completeness
   - Best practices adherence
3. Save findings to `/design/code-review.md`
4. Categorize as Critical, Major, or Minor issues

### Step 3.3: Fix Code Issues

Based on code review findings:

**Task**: Fix all identified issues:
1. Address all Critical issues immediately
2. Fix Major issues
3. Address Minor issues where practical
4. Re-run code review if significant changes were made
5. Update code comments and documentation

---

## Phase 4: Database Setup

### Step 4.1: Design Database Schema

Based on the design and architecture:

**Task**: Create comprehensive database schema:
1. Define all tables with columns and types
2. Specify primary keys and constraints
3. Create foreign key relationships
4. Design indexes for performance
5. Add check constraints and defaults
6. Plan for data validation
7. Consider future scalability

### Step 4.2: Generate SQL Scripts

**Task**: Create `/design/database-setup.md` with:
1. Complete SQL CREATE TABLE statements
2. Index definitions
3. Foreign key relationships
4. Seed data (if applicable)
5. Migration scripts (if needed)
6. Clear comments in SQL (using `--`) so user can copy-paste directly
7. Instructions for execution:
   - Copy SQL from the file
   - Paste into database editor (Supabase, PostgreSQL, etc.)
   - Execute queries
   - Verify tables created

Format should be easily copy-pasteable into Supabase SQL editor or PostgreSQL client.

---

## Phase 5: Test Automation

### Step 5.1: Analyze Testing Requirements

**Task**: Based on design and code:
1. Identify test categories needed:
   - Unit tests (functions, utilities)
   - Integration tests (components, APIs)
   - End-to-end tests (workflows)
2. Identify critical paths to test
3. Plan for test coverage targets
4. Plan test data and fixtures

### Step 5.2: Write Automated Tests

**Task**: Create comprehensive test suite:
1. Expand `/tests/suite.test.js` with actual test implementations
2. Write minimum 10 tests covering:
   - Core functionality
   - Edge cases
   - Error handling
   - Integration points
   - API endpoints
3. Organize tests into logical suites
4. Use clear, descriptive test names
5. Include assertions and expected results
6. Add test setup and teardown if needed

### Step 5.3: Run Tests

**Task**: Execute test suite:
1. Run all tests: `npm test` or `.\run_test.bat`
2. Report test results:
   - Passing tests
   - Failing tests
   - Code coverage percentage
3. Document any issues found

### Step 5.4: Fix Test Failures

**Task**: If tests fail:
1. Identify root causes
2. Fix code to pass tests
3. Rerun tests
4. Continue until all tests pass
5. Document any issues and resolutions

---

## Phase 6: Development Environment Setup

### Step 6.1: Create Run Scripts

The index.js script already created these. Verify and enhance if needed:

- **run_dev.bat** — Start development environment
  - Kill existing processes
  - Install dependencies
  - Start backend
  - Open browser
  - Display ready message

- **run_test.bat** — Run test suite
  - Execute npm test

- **run_deploy.bat** — Build for production
  - Run npm run build
  - Report success/failure

### Step 6.2: Create Environment Configuration

Update `.env.example`:
1. List all required environment variables
2. Provide example values
3. Add comments explaining each variable
4. Include:
   - Database credentials (SUPABASE_URL, keys, etc.)
   - LLM API keys (if needed)
   - Application settings
   - Other service credentials

---

## Phase 7: Going Live Configuration

### Step 7.1: Collect Deployment Information

**Ask the user to provide**:
1. Supabase credentials:
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - SUPABASE_SERVICE_ROLE_KEY

2. LLM configuration (if needed):
   - LLM_API_KEY
   - LLM_MODEL

3. Application settings:
   - APP_URL (production URL)
   - APP_PORT
   - NODE_ENV

4. Other service credentials as needed

### Step 7.2: Create .env File

**Task**:
1. Copy `.env.example` to `.env`
2. Populate with user-provided values
3. Verify all required variables are set
4. Warn about any missing values

### Step 7.3: Verify Database Setup

**Ask the user to**:
1. Acknowledge they've run the SQL scripts from `/design/database-setup.md`
2. Confirm all tables were created successfully
3. Verify database connection parameters are correct in `.env`

---

## Phase 8: Release Management

### Step 8.1: Initialize Release Tracking

The index.js created `release_notes.json`. Update it with:
1. Initial version number (0.1.0)
2. Release date
3. Features list from implementation plan
4. Bug fixes (if any)
5. Release notes text

### Step 8.2: Setup Version Management

**Task**:
1. Ensure version in `release_notes.json` matches package.json
2. Document versioning strategy:
   - Semantic versioning rules
   - When to bump major/minor/patch
   - Release process
3. Create CHANGELOG guidelines

### Step 8.3: Document Release Process

Add to `/design` folder:
- Release checklist
- Deployment steps
- Rollback procedures
- Communication plan

---

## Phase 9: Final Verification

### Step 9.1: Complete Project Checklist

Verify all components are in place:

**Documentation** ✓
- [ ] CLAUDE.md updated with project info
- [ ] SCHEMA.md with database design
- [ ] ARCHITECTURE.md with system design
- [ ] SECURITY.md with security guidelines
- [ ] DEPLOYMENT.md with deployment steps
- [ ] TESTING.md with test guide

**Design Documents** ✓
- [ ] spec-review.md with findings
- [ ] implementation-plan.md with strategy
- [ ] implementation-plan-review.md with validation
- [ ] code-review.md with findings and fixes
- [ ] database-setup.md with SQL scripts

**Code & Tests** ✓
- [ ] Source code in `/src` directory
- [ ] Test suite in `/tests` with 10+ tests
- [ ] All tests passing
- [ ] Code review findings resolved

**Configuration** ✓
- [ ] .env file created and populated
- [ ] .env.example with all variables
- [ ] release_notes.json initialized
- [ ] Run scripts created and tested

**Deployment** ✓
- [ ] Database tables created
- [ ] Environment variables configured
- [ ] Dev environment working (.\run_dev.bat)
- [ ] Tests passing (.\run_test.bat)
- [ ] Build succeeds (.\run_deploy.bat)

### Step 9.2: Final Report

Generate a summary report:
1. List all created files and their purpose
2. Summarize design decisions
3. List any known issues or TODO items
4. Provide next steps for deployment
5. Provide GitHub repository information

---

## Quick Reference: Running the Skill

```bash
cd C:\path\to\your\project
npx claude
/new-project
```

The skill will then:
1. Run index.js to scaffold the project
2. Guide you through design review
3. Generate implementation plan
4. Generate code
5. Create tests
6. Setup database
7. Configure deployment
8. Initialize release tracking

---

## Troubleshooting

**If design file is missing:**
- Create `/design/design.md` with your project specification
- Include overview, tech stack, features, requirements

**If a phase fails:**
- Review the relevant .md file in `/design` folder
- Check error messages and logs
- Rerun the specific phase

**If tests fail:**
- Check `/design/code-review.md` for issues
- Fix code and rerun tests
- Ensure all dependencies are installed

**For deployment issues:**
- Verify `.env` file is configured correctly
- Check database connection parameters
- Review `/design/database-setup.md` for SQL errors
- Check logs in run scripts

---

## Success Criteria

Project is ready when:
✓ All files created and populated
✓ Design review completed with recommendations
✓ Implementation plan created and validated
✓ Code generated and reviewed
✓ All tests passing (10+ tests)
✓ Database schema created
✓ Deployment configuration complete
✓ Release notes initialized
✓ Run scripts tested and working
✓ README and documentation complete

---

## Next Steps After Completion

1. **Deploy to development environment**
   - Run `.\run_dev.bat`
   - Test features manually
   - Verify database connectivity

2. **Deploy to production**
   - Run `.\run_deploy.bat`
   - Configure production .env
   - Execute SQL in production database
   - Monitor for issues

3. **Release to users**
   - Update release notes with actual release date
   - Tag version in git
   - Deploy to production
   - Communicate release to team

4. **Ongoing maintenance**
   - Monitor application logs
   - Track bugs and issues
   - Plan next features
   - Update documentation as needed
