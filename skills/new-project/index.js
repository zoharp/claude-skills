#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import readline from 'readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = process.cwd();
const designFolder = path.join(projectRoot, 'design');
const logsDir = path.join(projectRoot, 'logs');

// Create logs directory if it doesn't exist
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const logFile = path.join(logsDir, `skill-run-${new Date().toISOString().replace(/[:.]/g, '-')}.log`);

// Helper: Prompt user for input
function promptUser(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

function log(message) {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] ${message}`;
  console.log(message);
  fs.appendFileSync(logFile, logEntry + '\n');
}

function logStep(step, description) {
  const entry = `\n${'='.repeat(60)}\n[STEP] ${step}: ${description}\n${'='.repeat(60)}`;
  console.log(entry);
  fs.appendFileSync(logFile, entry + '\n');
}

function logError(message) {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] ❌ ERROR: ${message}`;
  console.error(logEntry);
  fs.appendFileSync(logFile, logEntry + '\n');
}

function logSuccess(message) {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] ✓ ${message}`;
  console.log(logEntry);
  fs.appendFileSync(logFile, logEntry + '\n');
}

logStep('1', 'Initialization');
log(`🚀 Starting new project: ${path.basename(projectRoot)}`);
log(`📁 Location: ${projectRoot}`);
log(`📝 Log file: ${logFile}`);

if (!fs.existsSync(designFolder)) {
  logError('/design folder not found in current directory');
  process.exit(1);
}

const designFiles = fs.readdirSync(designFolder).filter(f => f.endsWith('.md'));
if (designFiles.length === 0) {
  logError('No markdown file found in /design folder');
  process.exit(1);
}

const designFile = designFiles[0];
const designContent = fs.readFileSync(path.join(designFolder, designFile), 'utf-8');
const projectName = path.basename(projectRoot);
const repoUrl = `https://github.com/zoharp/${projectName}`;

log(`📖 Design: ${designFile}`);
log(`🔗 GitHub: ${repoUrl}`);

logStep('2', 'Creating project directory structure');
// Create directories
const dirs = ['src', 'tests', 'design', '.claude'];
dirs.forEach(dir => {
  const dirPath = path.join(projectRoot, dir);
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    logSuccess(`Created directory: ${dir}`);
  } else {
    log(`Directory already exists: ${dir}`);
  }
});

// Prompt for Supabase credentials and create .env
(async () => {
  if (!fs.existsSync(path.join(projectRoot, '.env'))) {
    logStep('2.5', 'Configuring Supabase credentials');
    console.log('(Get these from: supabase.com → your project → Settings → API)\n');

    const supabaseUrl = await promptUser(
      'Enter VITE_SUPABASE_URL (or press Enter to skip): '
    );
    const supabaseKey = await promptUser(
      'Enter VITE_SUPABASE_ANON_KEY (or press Enter to skip): '
    );

    const envContent = `# Supabase Configuration
VITE_SUPABASE_URL=${supabaseUrl || 'https://your-project.supabase.co'}
VITE_SUPABASE_ANON_KEY=${supabaseKey || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}

# Development Settings
VITE_APP_ENV=development
VITE_DEBUG=false

# Application URL
VITE_APP_URL=http://localhost:3000
`;

    fs.writeFileSync(path.join(projectRoot, '.env'), envContent);
    logSuccess('Created .env with your configuration');
  }
}).catch(err => logError(err.message));

// CLAUDE.md
const claudeContent = `# ${projectName}

Generated: ${new Date().toISOString()}

## GitHub Repository
${repoUrl}

## Skills
- spec-review: Technical specification review
- implementation-plan-review: Implementation plan validation
- code-review: Code quality and correctness review
- release-management: Version and release notes management
- deploy: Deployment automation

## Documentation Files
- CLAUDE.md (this file) - Project overview
- SCHEMA.md - Database schema definition
- ARCHITECTURE.md - System architecture
- SECURITY.md - Security guidelines
- DEPLOYMENT.md - Deployment procedures
- TESTING.md - Testing guide

## Design Documentation (/design folder)
- ${designFile} - Project design specification
- spec-review.md - Specification review results
- implementation-plan.md - Implementation strategy
- implementation-plan-review.md - Plan validation results
- code-review.md - Code review findings
- database-setup.md - Database initialization scripts

## Quick Start
\`\`\`bash
npm install
.\\run_dev.bat          # Start development
.\\run_test.bat         # Run tests
.\\run_deploy.bat       # Build for production
\`\`\`

## Project Structure
\`\`\`
${projectName}/
├── src/                  # Source code
├── tests/               # Test files
├── design/              # Design documents and reviews
├── .claude/             # Claude Code config
├── CLAUDE.md            # This file
├── SCHEMA.md            # Database schema
├── ARCHITECTURE.md      # Architecture docs
├── SECURITY.md          # Security guidelines
├── DEPLOYMENT.md        # Deployment guide
├── TESTING.md           # Testing guide
├── .env.example         # Environment template
├── release_notes.json   # Release notes
├── run_dev.bat          # Development startup
├── run_test.bat         # Test runner
└── run_deploy.bat       # Deployment script
\`\`\`
`;

logStep('3', 'Creating main documentation files');
fs.writeFileSync(path.join(projectRoot, 'CLAUDE.md'), claudeContent);
logSuccess('Created CLAUDE.md');

// Documentation files
const docs = {
  'SCHEMA.md': `# Database Schema

## Overview
[Schema will be generated by Claude AI based on design]

## Tables
[Table definitions will be added]

## Relationships
[Relationship mappings will be added]

## Indexes
[Index definitions will be added]
`,
  'ARCHITECTURE.md': `# System Architecture

## Overview
[Architecture diagram and description will be added by Claude AI]

## Components
[Component descriptions will be added]

## Data Flow
[Data flow diagrams will be added]

## Integration Points
[Integration details will be added]
`,
  'SECURITY.md': `# Security Guidelines

## Authentication
[Authentication strategy will be defined]

## Authorization
[Authorization rules will be defined]

## Data Protection
[Data protection measures will be defined]

## Compliance
[Compliance requirements will be addressed]
`,
  'DEPLOYMENT.md': `# Deployment Guide

## Prerequisites
[Prerequisites will be listed]

## Environment Setup
[Setup instructions will be provided]

## Deployment Steps
[Step-by-step deployment process]

## Post-Deployment
[Post-deployment verification steps]

## Rollback Procedure
[Rollback procedures will be documented]
`,
  'TESTING.md': `# Testing Guide

## Test Structure
- Unit tests: /tests/unit/
- Integration tests: /tests/integration/
- E2E tests: /tests/e2e/

## Running Tests
\`npm test\`

## Test Coverage
[Coverage requirements will be defined]

## Continuous Integration
[CI configuration details]
`,
};

Object.entries(docs).forEach(([name, content]) => {
  const fpath = path.join(projectRoot, name);
  if (!fs.existsSync(fpath)) {
    fs.writeFileSync(fpath, content);
    logSuccess(`Created ${name}`);
  } else {
    log(`File already exists: ${name}`);
  }
});

// Design phase documents
logStep('4', 'Creating design phase documents');

const specReview = `# Specification Review

Generated: ${new Date().toISOString()}
Reviewer: Claude AI

## Design Specification

\`\`\`markdown
${designContent}
\`\`\`

## Review Checklist
- [ ] Architecture clarity and feasibility
- [ ] Technology stack appropriateness
- [ ] API/Interface design
- [ ] Database design
- [ ] Security considerations
- [ ] Performance requirements
- [ ] Scalability approach
- [ ] Error handling strategy
- [ ] Deployment approach
- [ ] Testing strategy

## Findings
[Detailed findings will be added by Claude AI]

## Issues
- Critical: [None identified initially]
- Major: [None identified initially]
- Minor: [None identified initially]

## Recommendations
[Recommendations will be provided by Claude AI]

## Sign-off
Status: Pending Claude AI Review
`;

fs.writeFileSync(path.join(designFolder, 'spec-review.md'), specReview);
logSuccess('Created spec-review.md');

const implPlan = `# Implementation Plan

Generated: ${new Date().toISOString()}
Planner: Claude AI

## Phase 1: Foundation & Setup
- Project initialization
- Build tool configuration
- Version control setup
- CI/CD pipeline configuration
- Development environment setup

## Phase 2: Core Development
[Detailed phases will be added by Claude AI based on design]

## Phase 3: Integration
[Integration tasks will be defined]

## Phase 4: Testing
[Testing phases will be defined]

## Phase 5: Deployment
[Deployment procedures will be defined]

## Timeline
[Timeline will be created by Claude AI]

## Resource Requirements
[Resources will be identified by Claude AI]

## Risk Assessment
- Risks: [Will be identified by Claude AI]
- Mitigation: [Mitigation strategies will be provided]

## Success Criteria
[Success criteria will be defined by Claude AI]

## Dependencies
[External dependencies will be listed]

## Assumptions
[Key assumptions will be documented]
`;

fs.writeFileSync(path.join(designFolder, 'implementation-plan.md'), implPlan);
logSuccess('Created implementation-plan.md');

const planReview = `# Implementation Plan Review

Generated: ${new Date().toISOString()}
Reviewer: Claude AI

## Plan Assessment
- [ ] Feasibility: Is the plan achievable?
- [ ] Completeness: Are all aspects covered?
- [ ] Sequencing: Are dependencies properly ordered?
- [ ] Resource Adequacy: Are resources sufficient?
- [ ] Timeline Realism: Is the timeline realistic?
- [ ] Risk Coverage: Are risks identified and mitigated?
- [ ] Rollback Strategy: Is rollback plan adequate?
- [ ] Testing Coverage: Is testing comprehensive?

## Critical Issues
[Issues will be identified by Claude AI]

## Major Issues
[Issues will be identified by Claude AI]

## Recommendations
[Recommendations will be provided by Claude AI]

## Revised Plan Actions
[Actions from recommendations will be listed]

## Approval Status
Status: Pending Claude AI Review
`;

fs.writeFileSync(path.join(designFolder, 'implementation-plan-review.md'), planReview);
logSuccess('Created implementation-plan-review.md');

// Code review template
const codeReview = `# Code Review Report

Generated: ${new Date().toISOString()}
Reviewer: Claude AI

## Files Reviewed
[Generated code files will be listed]

## Review Findings

### Critical Issues
[Critical issues will be identified]

### Major Issues
[Major issues will be identified]

### Minor Issues
[Minor issues will be identified]

## Code Quality Metrics
- Complexity: [Will be assessed]
- Maintainability: [Will be assessed]
- Test Coverage: [Will be assessed]
- Security: [Will be assessed]

## Recommendations
[Recommendations will be provided by Claude AI]

## Sign-off
Status: Pending Claude AI Review
`;

fs.writeFileSync(path.join(designFolder, 'code-review.md'), codeReview);
logSuccess('Created code-review.md');

// Database setup
const dbSetup = `# Database Setup

Generated: ${new Date().toISOString()}

## Instructions
1. Copy SQL queries below
2. Paste into your database editor (Supabase SQL, PostgreSQL, etc.)
3. Execute the queries
4. Verify tables are created

## SQL Scripts

\`\`\`sql
-- Database initialization script
-- Generated by Claude AI based on design

-- Example table structure (will be generated based on design):
-- CREATE TABLE users (
--   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   email VARCHAR(255) UNIQUE NOT NULL,
--   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Claude AI will generate actual SQL based on design
\`\`\`

## Tables to Create
[Table definitions will be generated by Claude AI]

## Indexes
[Index definitions will be generated by Claude AI]

## Relationships
[Foreign key relationships will be defined]

## Initial Data
[Seed data scripts if needed]

## Verification
After running SQL:
- [ ] All tables created successfully
- [ ] All indexes created
- [ ] All relationships established
`;

fs.writeFileSync(path.join(designFolder, 'database-setup.md'), dbSetup);
logSuccess('Created database-setup.md');

// Test suite
logStep('5', 'Creating test suite');
const testDir = path.join(projectRoot, 'tests');
if (!fs.existsSync(testDir)) fs.mkdirSync(testDir, { recursive: true });

const testFile = path.join(testDir, 'suite.test.js');
const testContent = `// Test Suite
// Generated: ${new Date().toISOString()}
// Claude AI will create 10+ tests based on design

describe('Project Tests', () => {
  describe('Test Suite 1', () => {
    test('test 1', () => {
      expect(true).toBe(true);
    });

    test('test 2', () => {
      expect(true).toBe(true);
    });

    test('test 3', () => {
      expect(true).toBe(true);
    });
  });

  describe('Test Suite 2', () => {
    test('test 4', () => {
      expect(true).toBe(true);
    });

    test('test 5', () => {
      expect(true).toBe(true);
    });

    test('test 6', () => {
      expect(true).toBe(true);
    });
  });

  describe('Test Suite 3', () => {
    test('test 7', () => {
      expect(true).toBe(true);
    });

    test('test 8', () => {
      expect(true).toBe(true);
    });

    test('test 9', () => {
      expect(true).toBe(true);
    });
  });

  describe('Test Suite 4', () => {
    test('test 10', () => {
      expect(true).toBe(true);
    });

    test('test 11', () => {
      expect(true).toBe(true);
    });
  });

  // Claude AI will add actual test implementations
  // based on design specifications
});
`;

fs.writeFileSync(testFile, testContent);
logSuccess('Created tests/suite.test.js (11 test placeholders)');

// Run scripts
logStep('6', 'Creating run scripts');

const runDevBat = `@echo off
REM Development environment startup script
REM Generated: ${new Date().toISOString()}

echo Starting development environment...

REM Kill any existing Node processes
taskkill /F /IM node.exe 2>nul

REM Create .env from .env.example if it doesn't exist
if not exist .env (
  echo Creating .env file...
  copy .env.example .env
  echo Please update .env with your configuration
)

REM Install dependencies if node_modules doesn't exist
if not exist node_modules (
  echo Installing dependencies...
  npm install
)

REM Start backend
echo Starting backend...
start "Backend" npm run dev

REM Wait for backend to start
timeout /t 3 /nobreak

REM Open browser
echo Opening browser...
timeout /t 2 /nobreak
start http://localhost:3000

echo.
echo ✓ Development environment started!
echo.
echo Press Ctrl+C in this window to stop, or close the backend window.
echo.
`;

fs.writeFileSync(path.join(projectRoot, 'run_dev.bat'), runDevBat);
logSuccess('Created run_dev.bat');

const runTestBat = `@echo off
REM Test runner script
REM Generated: ${new Date().toISOString()}

echo Running test suite...
npm test
`;

fs.writeFileSync(path.join(projectRoot, 'run_test.bat'), runTestBat);
logSuccess('Created run_test.bat');

const runDeployBat = `@echo off
REM Deployment script
REM Generated: ${new Date().toISOString()}

echo Building for production...
npm run build

if %ERRORLEVEL% NEQ 0 (
  echo Build failed!
  exit /b 1
)

echo.
echo ✓ Build complete! Ready for deployment.
echo.
`;

fs.writeFileSync(path.join(projectRoot, 'run_deploy.bat'), runDeployBat);
logSuccess('Created run_deploy.bat');

// Environment template
logStep('7', 'Creating environment template');

const envTemplate = `# Environment Configuration Template
# Copy to .env and fill in your actual values

# Database Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# LLM Configuration (if needed)
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=claude-opus-4-1

# Application Configuration
NODE_ENV=development
APP_URL=http://localhost:3000
APP_PORT=3000
APP_DEBUG=false

# Other Configuration
# Add additional environment variables as needed
# based on your design specifications
`;

fs.writeFileSync(path.join(projectRoot, '.env.example'), envTemplate);
logSuccess('Created .env.example');

// Release notes
logStep('8', 'Creating release notes');

const releaseNotes = {
  version: '0.1.0',
  releases: [
    {
      version: '0.1.0',
      date: new Date().toISOString(),
      type: 'initial',
      features: [
        'Project structure initialization',
        'Documentation framework setup',
        'Design review templates',
        'Implementation planning',
        'Code review framework',
        'Test suite initialization',
        'Development environment scripts',
      ],
      bugFixes: [],
      notes: 'Initial project setup generated by new-project-skill automation',
    },
  ],
};

fs.writeFileSync(
  path.join(projectRoot, 'release_notes.json'),
  JSON.stringify(releaseNotes, null, 2)
);
logSuccess('Created release_notes.json');

// Install dependencies
logStep('8.5', 'Installing npm dependencies');
try {
  log('Running: npm install');
  execSync('npm install', { cwd: projectRoot, stdio: 'inherit' });
  logSuccess('npm dependencies installed successfully');
} catch (error) {
  logError('npm install encountered an issue. Please run "npm install" manually.');
}

// Summary
logStep('9', 'Initialization Summary');

log('\n' + '='.repeat(60));
log('✅ PROJECT INITIALIZATION COMPLETE');
log('='.repeat(60));
log('\n📁 Generated Files:');
log('  ✓ CLAUDE.md - Project overview');
log('  ✓ SCHEMA.md - Database schema');
log('  ✓ ARCHITECTURE.md - System architecture');
log('  ✓ SECURITY.md - Security guidelines');
log('  ✓ DEPLOYMENT.md - Deployment guide');
log('  ✓ TESTING.md - Testing guide');
log('  ✓ design/spec-review.md');
log('  ✓ design/implementation-plan.md');
log('  ✓ design/implementation-plan-review.md');
log('  ✓ design/code-review.md');
log('  ✓ design/database-setup.md');
log('  ✓ tests/suite.test.js (11 placeholder tests)');
log('  ✓ run_dev.bat - Development startup');
log('  ✓ run_test.bat - Test runner');
log('  ✓ run_deploy.bat - Build script');
log('  ✓ .env.example - Environment template');
log('  ✓ .env - Auto-created with your configuration');
log('  ✓ release_notes.json - Release tracking');
log('  ✓ node_modules/ - Dependencies installed');

log('\n📋 Next Steps:');
log('  1. Claude AI will review the design specification');
log('  2. Implementation plan will be created and validated');
log('  3. Code will be generated based on the plan');
log('  4. Automated tests will be written and executed');
log('  5. Database setup scripts will be prepared');
log('  6. Configuration for going live will be collected');
log('  7. Release notes will be updated');

log('\n⚙️  Manual Steps:');
log('  1. Update .env.example with actual values → .env');
log('  2. Copy database-setup.md SQL to your database');
log('  3. Run .\\run_dev.bat to start development');
log('  4. Run .\\run_test.bat to test the project');

log('\n🔗 Repository: ' + repoUrl);
log('📁 Location: ' + projectRoot);
log('📝 Log file: ' + logFile);
log('\n');
