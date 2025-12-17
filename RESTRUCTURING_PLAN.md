# Project Restructuring Plan

## Current Structure
```
market-research-agent/
├── src/
├── examples/
├── outputs/
├── venv/
├── README.md
├── requirements.txt
├── setup.sh
├── .env
├── .env.example
├── .gitignore
└── Documentation files (*.md)
```

## Proposed New Structure
```
agentic-samples/  (or samples/)
├── README.md                           # Overview of all samples
├── .gitignore                          # Root gitignore
├── requirements.txt                    # Common dependencies (optional)
│
└── samples/
    │
    ├── market-research-agent/          # Sample 1
    │   ├── README.md                   # Sample-specific README
    │   ├── src/
    │   ├── examples/
    │   ├── outputs/
    │   ├── requirements.txt
    │   ├── setup.sh
    │   ├── .env.example
    │   └── docs/                       # Sample-specific documentation
    │       ├── AGENTIC_ORCHESTRATOR.md
    │       ├── AGENTIC_AGENT_ARCHITECTURE.md
    │       ├── AGENTIC_REFACTORING_SUMMARY.md
    │       ├── CHANGELOG.md
    │       ├── MIGRATION_GUIDE.md
    │       ├── QUICKSTART.md
    │       └── ...
    │
    ├── sample-2/                       # Placeholder for future sample
    │   └── README.md
    │
    └── sample-3/                       # Placeholder for future sample
        └── README.md
```

## Implementation Steps

### Phase 1: Create New Structure (Non-Destructive)
1. Create `samples/` directory
2. Create `samples/market-research-agent/` directory
3. Copy all project files into the new location

### Phase 2: Organize Files
1. Move documentation files into `samples/market-research-agent/docs/`
2. Keep core project files in `samples/market-research-agent/`
3. Create root-level README explaining the samples

### Phase 3: Update References
1. Update import paths if needed
2. Update documentation references
3. Update .gitignore paths

### Phase 4: Clean Up
1. Remove old files from root (after verification)
2. Create placeholder for future samples

## Benefits

1. **Scalability**: Easy to add new samples
2. **Organization**: Clear separation between samples
3. **Discoverability**: Users can explore multiple examples
4. **Flexibility**: Each sample can have its own dependencies

## Migration for Users

Users currently cloning the repo would need to:
```bash
# Old
git clone <repo> market-research-agent
cd market-research-agent

# New
git clone <repo> agentic-samples
cd agentic-samples/samples/market-research-agent
```

Or we could keep the repo name as `market-research-agent` and just have the internal structure be sample-based.
