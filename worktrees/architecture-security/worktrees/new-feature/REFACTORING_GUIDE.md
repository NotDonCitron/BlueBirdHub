# OrdnungsHub - Refactored Monorepo Structure

## Overview

The project has been refactored into a monorepo structure that clearly separates desktop and web deployments while sharing core functionality.

## New Structure

```
ordnungshub/
├── packages/
│   ├── core/                    # Shared components, hooks, utils, types
│   ├── desktop/                 # Electron desktop application
│   ├── web/                     # Web application (Vite + React)
│   └── backend/                 # Python FastAPI backend
├── package.json                 # Workspace root configuration
├── pnpm-workspace.yaml          # Workspace definition
└── tsconfig.json               # Root TypeScript configuration
```

## Package Details

### @ordnungshub/core
- **Purpose**: Shared React components, hooks, utilities, and types
- **Technology**: TypeScript, React
- **Build**: TypeScript compilation to `dist/`
- **Exports**: All reusable UI components and business logic

### @ordnungshub/desktop
- **Purpose**: Electron desktop application
- **Technology**: Electron, React, TypeScript, Webpack
- **Build**: Webpack bundles for main, preload, and renderer processes
- **Target**: Native desktop app with full system access

### @ordnungshub/web
- **Purpose**: Web application for browser deployment
- **Technology**: Vite, React, TypeScript
- **Build**: Optimized web bundle with code splitting
- **Target**: Modern browsers with web-only features

### @ordnungshub/backend
- **Purpose**: Python FastAPI backend (unchanged)
- **Technology**: Python, FastAPI, SQLAlchemy
- **Build**: Direct Python execution
- **Target**: API server for both desktop and web clients

## Development Commands

### Setup
```bash
# Install all dependencies
pnpm install

# Install dependencies for specific package
pnpm --filter @ordnungshub/web install
```

### Development
```bash
# Start all packages in development mode
pnpm dev

# Start specific environments
pnpm dev:web          # Web app (localhost:3000)
pnpm dev:desktop      # Desktop app
pnpm dev:backend      # Backend API (localhost:8001)
```

### Building
```bash
# Build all packages
pnpm build

# Build specific packages
pnpm build:core       # Shared core library
pnpm build:web        # Web application
pnpm build:desktop    # Desktop application
```

### Production
```bash
# Start production builds
pnpm start:web        # Serve built web app
pnpm start:desktop    # Launch desktop app
pnpm start:backend    # Production backend server
```

## Key Benefits

1. **Clear Separation**: Desktop and web apps are completely separate with shared core
2. **Code Reuse**: Common components and logic in the core package
3. **Independent Deployment**: Each target can be deployed separately
4. **Better DX**: Dedicated tools for each platform (Vite for web, Webpack for Electron)
5. **Type Safety**: Full TypeScript support with project references
6. **Workspace Management**: Efficient dependency management with pnpm workspaces

## Migration Notes

- Original `src/` directory structure has been moved to `packages/`
- Backend code moved to `packages/backend/src/`
- Frontend React components moved to `packages/core/src/components/`
- Electron-specific code in `packages/desktop/`
- Web-specific code and routing in `packages/web/`
- All build configurations updated for new structure

## Next Steps

1. Install dependencies: `pnpm install`
2. Test desktop build: `pnpm dev:desktop`  
3. Test web build: `pnpm dev:web`
4. Test backend: `pnpm dev:backend`
5. Update CI/CD pipelines for new structure
6. Update deployment scripts for web and desktop targets