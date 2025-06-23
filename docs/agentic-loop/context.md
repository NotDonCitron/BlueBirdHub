# Agentic Loop Framework - Context

## Overview

This is a minimal, high-fidelity Agentic Loop Framework designed to tackle complex tasks with minimal role bloat. The framework consists of three core agents working together in a tight feedback loop.

## Core Principles

1. **Single-brain overview** – One Orchestrator owns the big picture
2. **Few, powerful agents** – Reuse the same Specialist prompt for parallelism instead of inventing many micro-roles
3. **Tight feedback** – A dedicated Evaluator grades outputs (0-100) and suggests concrete fixes until quality ≥ TARGET_SCORE
4. **Shared context** – Every agent receives the same context so no information is siloed
5. **Repo-aware** – The Orchestrator decides whether to align to the current repo or create a generic loop
6. **Explicit imperatives** – Use labels "You Must" or "Important" for non-negotiable steps; permit extra compute with "Think hard" / "ultrathink"

## Three Core Agents

### 1. Orchestrator (Atlas)
- **Role**: Coordinates everything and owns the big picture
- **Responsibilities**: 
  - Parse context and requirements
  - Decide repo-specific vs generic flow
  - Spawn parallel Specialist agents
  - Manage iteration cycles based on Evaluator feedback
  - Consolidate final outputs

### 2. Specialist (Mercury)
- **Role**: Multi-disciplinary expert who can research, code, write, and test
- **Responsibilities**:
  - Execute assigned tasks with full context
  - Acknowledge uncertainties instead of hallucinating
  - Use TDD when coding
  - Deliver clean, self-contained outputs
  - Tag intensive reasoning with "ultrathink"

### 3. Evaluator (Apollo)
- **Role**: Critically grade outputs and provide concrete feedback
- **Responsibilities**:
  - Score outputs 0-100 against quality standards
  - Identify strengths and weaknesses
  - Provide specific, actionable feedback
  - Make APPROVE/ITERATE decisions

## Workflow Process

1. **Bootstrap**: Create shared context document
2. **Orchestration**: Atlas coordinates and spawns tasks
3. **Specialization**: Mercury agents execute in parallel
4. **Evaluation**: Apollo grades outputs and provides feedback
5. **Iteration**: Repeat 2-4 until TARGET_SCORE achieved (default: 90)
6. **Consolidation**: Atlas merges and finalizes outputs

## Quality Standards

- **TARGET_SCORE**: 90+ (configurable)
- **Iteration Limit**: 3 cycles maximum
- **Output Format**: Structured markdown with clear sections
- **Documentation**: All decisions and reasoning preserved

## File Structure

```
./docs/<TASK>/
├── context.md          # This file - shared by all agents
├── specialist.md       # Mercury agent definition
├── evaluator.md        # Apollo agent definition
└── README.md          # Task-specific documentation

./.claude/commands/
└── <TASK>.md          # Atlas orchestrator commands

./outputs/<TASK>_<TIMESTAMP>/
├── phase1/            # Initial specialist outputs
├── phase2/            # Refined outputs after feedback
├── phase3/            # Final iteration if needed
└── final/             # Consolidated deliverables
```

## Usage Instructions

### For Task Execution

1. **Initialize Task**: Create task-specific context
2. **Configure Agents**: Set TARGET_SCORE and parallelism level
3. **Execute Loop**: Run orchestrator commands
4. **Monitor Progress**: Check phase outputs and evaluations
5. **Retrieve Results**: Final outputs in ./outputs/<TASK>_<TIMESTAMP>/final/

### For Framework Extension

1. **Maintain Three Roles**: Never add additional agent types
2. **Preserve Context Sharing**: All agents must receive same context
3. **Follow Naming**: Atlas, Mercury, Apollo for consistency
4. **Document Changes**: Update this context file for modifications

## Configuration Parameters

- **TASK**: Task name (provided by user)
- **REPO_PATH**: Absolute path to repository (if applicable)
- **PARALLELISM**: Number of parallel Specialist instances (1-3)
- **TARGET_SCORE**: Minimum quality threshold (default: 90)
- **MAX_ITERATIONS**: Maximum iteration cycles (default: 3)

## Success Criteria

A task is considered complete when:
1. Evaluator score ≥ TARGET_SCORE
2. All deliverables are in ./outputs/<TASK>_<TIMESTAMP>/final/
3. No merge conflicts or incomplete outputs
4. Documentation is updated and consistent

## Error Handling

- **Missing Context**: Specialists must request clarification
- **Merge Conflicts**: Orchestrator reallocates work to avoid conflicts
- **Quality Issues**: Evaluator provides specific feedback for iteration
- **Resource Limits**: Graceful degradation with clear error messages

## Framework Metadata

- **Version**: 1.0
- **Last Updated**: 2025-06-23
- **Core Philosophy**: Minimal roles, maximum coordination
- **Primary Use Cases**: Complex software development, research analysis, content creation

---

*This context is shared by all agents to ensure consistent understanding and execution of the Agentic Loop Framework.*