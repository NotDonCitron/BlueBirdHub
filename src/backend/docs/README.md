# OrdnungsHub API Documentation System

A comprehensive API documentation system with automated generation, validation, and client SDK creation.

## Overview

This documentation system provides:

- **Enhanced OpenAPI Specification**: Comprehensive API metadata with examples
- **Custom Swagger UI**: Branded interactive documentation interface
- **Client SDK Generation**: Automatic TypeScript and Python SDK generation
- **Documentation Validation**: Quality checks and consistency validation
- **CI/CD Integration**: Automated documentation testing and deployment

## Features

### 📋 Enhanced OpenAPI Configuration

- Detailed API metadata with contact information and terms
- Multiple server environments (local, staging, production)
- Comprehensive tag descriptions with external documentation links
- Security scheme definitions for JWT and API key authentication
- Common error response templates across all endpoints

### 🎨 Custom Swagger UI

- OrdnungsHub branded interface with custom styling
- Enhanced authentication testing capabilities
- Code examples in multiple languages
- Request/response interceptors for better debugging
- Mobile-responsive design

### 🔧 Client SDK Generation

#### TypeScript SDK
- **Location**: `sdks/typescript/`
- **Features**: 
  - Type-safe interfaces
  - Built-in authentication handling
  - Error handling with detailed messages
  - Axios-based HTTP client
  - Comprehensive examples

#### Python SDK
- **Location**: `sdks/python/`
- **Features**:
  - Pythonic interface design
  - Session-based authentication
  - Rich error handling
  - Requests-based HTTP client
  - Type hints and docstrings

### ✅ Documentation Validation

- **Endpoint Documentation Scoring**: Quality metrics for each endpoint
- **Schema Consistency Checks**: Validation of schema usage and definitions
- **Example Validation**: JSON format and structure validation
- **Parameter Consistency**: Naming pattern validation across endpoints

### 🚀 CI/CD Integration

- **GitHub Actions Workflow**: Automated validation on pull requests
- **Documentation Testing**: Endpoint availability and response validation
- **SDK Generation**: Automatic client library updates
- **Report Generation**: Comprehensive documentation quality reports

## Quick Start

### 1. Start the API Server

```bash
cd src/backend
python main.py
```

The API will be available at `http://localhost:8000` with documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### 2. Generate Client SDKs

```bash
# Install OpenAPI Generator (one-time setup)
npm install -g @openapitools/openapi-generator-cli

# Generate all SDKs
cd src/backend/docs
python generate_sdk.py
```

Generated SDKs will be available in the `sdks/` directory.

### 3. Validate Documentation

```bash
cd src/backend/docs

# Validate OpenAPI specification
python automation.py validate

# Check documentation coverage
python automation.py coverage

# Test API endpoints
python automation.py test

# Generate comprehensive report
python automation.py report
```

## Using the Client SDKs

### TypeScript/JavaScript

```typescript
import OrdnungsHubClient from './sdks/typescript/ordnungshub-client';

const client = new OrdnungsHubClient({
  baseURL: 'https://api.ordnungshub.com'
});

// Authenticate
const token = await client.login('username', 'password');

// Get user information
const user = await client.getCurrentUser();

// Create a workspace
const workspace = await client.createWorkspace({
  name: 'My New Workspace',
  description: 'A workspace for my projects'
});

// Get all workspaces
const workspaces = await client.getWorkspaces();
```

### Python

```python
from sdks.python.ordnungshub_client.enhanced_client import OrdnungsHubClient

# Initialize client
client = OrdnungsHubClient("https://api.ordnungshub.com")

# Authenticate
token = client.login("username", "password")

# Get user information
user = client.get_current_user()

# Create a workspace
workspace = client.create_workspace(
    name="My New Workspace",
    description="A workspace for my projects"
)

# Get all workspaces
workspaces = client.get_workspaces()
```

## Documentation Quality Metrics

The system tracks several quality metrics:

### Endpoint Documentation Score (0-100)
- **Summary**: 20 points for clear, descriptive summaries
- **Description**: 20 points for detailed descriptions
- **Parameters**: 15 points for parameter documentation
- **Request Body**: 10 points for request documentation
- **Responses**: 20 points for response documentation
- **Examples**: 10 points for request/response examples
- **Tags**: 5 points for proper categorization

### Coverage Metrics
- **Total Endpoints**: Number of API endpoints
- **Documented Endpoints**: Endpoints with adequate documentation
- **Coverage Percentage**: Overall documentation coverage
- **Missing Documentation**: List of endpoints needing improvement

### Consistency Checks
- **Schema Usage**: Validation of schema references
- **Parameter Naming**: Consistent naming patterns
- **Response Formats**: Standardized error responses

## File Structure

```
src/backend/docs/
├── README.md                 # This documentation
├── __init__.py              # Package initialization
├── swagger_ui.py            # Custom Swagger UI configuration
├── generate_sdk.py          # SDK generation script
├── automation.py            # CI/CD automation tools
├── validation.py            # Documentation validation tools
└── documentation_report.json # Latest validation report

sdks/
├── typescript/              # TypeScript client SDK
│   ├── api/                # Generated API clients
│   ├── models/             # Type definitions
│   ├── ordnungshub-client.ts # Enhanced client wrapper
│   └── package.json        # npm package configuration
└── python/                 # Python client SDK
    ├── ordnungshub_client/ # Generated Python package
    ├── setup.py           # pip package configuration
    └── README.md          # Python SDK documentation

.github/workflows/
└── api-documentation.yml   # GitHub Actions workflow
```

## Configuration

### Environment Variables

```bash
# API Configuration
API_BASE_URL=http://localhost:8000  # Base URL for API

# Documentation Settings
DOCS_BRAND_NAME=OrdnungsHub         # Brand name for Swagger UI
DOCS_BRAND_COLOR=#1e40af            # Primary brand color
DOCS_SUPPORT_EMAIL=api-support@ordnungshub.com

# SDK Generation
SDK_OUTPUT_DIR=./sdks               # Output directory for SDKs
TYPESCRIPT_PACKAGE_NAME=ordnungshub-api-client
PYTHON_PACKAGE_NAME=ordnungshub-client
```

### Customization

#### Swagger UI Styling

Edit `swagger_ui.py` to customize:
- Brand colors and styling
- Logo and branding elements
- Custom JavaScript functionality
- Request/response interceptors

#### SDK Templates

Modify the SDK generation templates in `generate_sdk.py`:
- Client wrapper interfaces
- Authentication handling
- Error handling patterns
- Package metadata

## CI/CD Pipeline

The GitHub Actions workflow (`api-documentation.yml`) automatically:

1. **Validates** OpenAPI specification on code changes
2. **Tests** API endpoints for availability and correctness
3. **Generates** client SDKs and uploads as artifacts
4. **Creates** documentation reports with quality metrics
5. **Deploys** documentation to GitHub Pages (on main branch)

### Workflow Triggers

- **Push** to main or develop branches (backend changes)
- **Pull Request** to main branch (documentation validation)
- **Manual** workflow dispatch for on-demand generation

### Artifacts

- **API SDKs**: Generated TypeScript and Python clients
- **Documentation Report**: Quality metrics and validation results
- **OpenAPI Specification**: Latest API schema definition

## Troubleshooting

### Common Issues

#### SDK Generation Fails
```bash
# Ensure OpenAPI Generator is installed
npm install -g @openapitools/openapi-generator-cli

# Check API server is running
curl http://localhost:8000/health

# Verify OpenAPI spec is valid
python automation.py validate
```

#### Documentation Validation Errors
```bash
# Check specific validation issues
python validation.py endpoints  # Endpoint documentation
python validation.py schemas    # Schema consistency
python validation.py examples   # Example validation

# Generate detailed report
python validation.py report
```

#### Custom Swagger UI Not Loading
- Verify `swagger_ui.py` imports correctly
- Check CSS/JS syntax in custom styling
- Ensure API server restart after configuration changes

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Adding New Endpoints

1. **Document thoroughly**: Include summary, description, examples
2. **Follow naming conventions**: Consistent parameter and response naming
3. **Add comprehensive examples**: Request and response examples
4. **Update tags**: Proper categorization for documentation
5. **Test documentation**: Run validation tools before committing

### Documentation Standards

- **Summaries**: 10-50 characters, action-oriented
- **Descriptions**: 50+ characters, explain purpose and usage
- **Examples**: Real-world, working examples
- **Error Responses**: Include all possible error scenarios
- **Parameters**: Describe purpose, format, and constraints

### Quality Gates

All documentation changes must pass:
- ✅ OpenAPI specification validation
- ✅ 80%+ documentation coverage
- ✅ All endpoint tests passing
- ✅ SDK generation success
- ✅ No schema consistency errors

## Support

- **Documentation Issues**: Open an issue with the `documentation` label
- **SDK Problems**: Include client type (TypeScript/Python) and error logs
- **API Questions**: Refer to the interactive Swagger UI documentation
- **Feature Requests**: Use the `enhancement` label for new documentation features

---

For more information, visit the [OrdnungsHub Documentation Portal](https://docs.ordnungshub.com).