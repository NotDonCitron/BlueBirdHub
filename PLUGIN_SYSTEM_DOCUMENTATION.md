# BlueBirdHub Plugin System Documentation

## Overview

The BlueBirdHub Plugin System is a comprehensive, secure, and scalable architecture that enables third-party developers to extend BlueBirdHub's functionality while maintaining system stability and security. The system supports various plugin types including integrations, UI components, workflow automation, AI enhancements, and more.

## Architecture

### Core Components

1. **Plugin Manager** - Central coordination and lifecycle management
2. **Plugin Registry** - Metadata storage and plugin discovery
3. **Marketplace** - Plugin distribution and installation
4. **Security System** - Sandboxing and validation
5. **Event System** - Inter-plugin communication
6. **Permission Manager** - Access control and authorization
7. **Configuration Manager** - Settings and preferences
8. **Analytics Manager** - Usage tracking and monitoring

### Plugin Types Supported

- **Integration Plugins** - External service integrations (Slack, GitHub, Notion, etc.)
- **UI Component Plugins** - Custom interface elements and themes
- **Workflow Plugins** - Automation and business logic
- **AI Enhancement Plugins** - Machine learning and intelligent features
- **Data Processor Plugins** - Import/export and data transformation
- **Field Type Plugins** - Custom data types and validation
- **API Extension Plugins** - Additional REST endpoints
- **Background Service Plugins** - Long-running tasks and services
- **Schema Extension Plugins** - Database schema modifications
- **Authentication Provider Plugins** - Custom authentication methods

## Getting Started

### Plugin Development SDK

The BlueBirdHub Plugin SDK provides everything needed to develop plugins:

```python
from bluebirdhub.plugins.sdk import PluginBuilder, BaseIntegrationPlugin, ConfigType

# Create plugin manifest
builder = PluginBuilder("my-plugin", "My Awesome Plugin")
builder.version("1.0.0")
builder.description("Description of what my plugin does")
builder.author("Your Name", "your.email@example.com")
builder.type(PluginType.INTEGRATION)

# Add configuration options
builder.add_config("api_key", ConfigType.STRING, "API Key", required=True, secret=True)
builder.add_config("base_url", ConfigType.STRING, "Base URL", default_value="https://api.example.com")

# Define permissions needed
builder.add_permission("net.http", "HTTP requests", "network", "execute", required=True)

class MyPlugin(BaseIntegrationPlugin):
    async def initialize(self) -> bool:
        # Plugin initialization logic
        return True
    
    async def activate(self) -> bool:
        # Plugin activation logic
        return True
    
    async def authenticate(self) -> bool:
        # Authentication with external service
        api_key = await self.sdk.get_config("api_key")
        # ... authentication logic
        return True
    
    async def sync_data(self) -> bool:
        # Data synchronization logic
        return True

Plugin = MyPlugin
```

### Configuration Management

Plugins can define configuration schemas with validation:

```python
# String configuration with pattern validation
builder.add_config(
    "email", 
    ConfigType.STRING, 
    "Email address",
    pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    required=True
)

# Integer with range validation
builder.add_config(
    "timeout_seconds",
    ConfigType.INTEGER,
    "Request timeout",
    default_value=30,
    min_value=1,
    max_value=300
)

# Array with predefined choices
builder.add_config(
    "log_levels",
    ConfigType.ARRAY,
    "Enabled log levels",
    default_value=["info", "error"],
    choices=["debug", "info", "warn", "error"]
)
```

### Event System

Plugins can emit and listen to events for inter-plugin communication:

```python
# Listen to events
self.sdk.add_event_handler("task.created", self.handle_task_created)

# Emit events
await self.sdk.emit_event("user.notification", {
    "message": "Task completed successfully",
    "user_id": user_id
})

# Handle events
async def handle_task_created(self, event):
    task_data = event.data
    # Process the task creation event
```

### RPC Communication

Plugins can call methods on other plugins:

```python
# Call another plugin's method
result = await self.sdk.call_rpc(
    "slack-integration", 
    "send_message", 
    channel="#general", 
    message="Hello from my plugin!"
)

# Expose methods for other plugins to call
async def my_public_method(self, param1: str, param2: int) -> str:
    """This method can be called by other plugins via RPC"""
    return f"Processed {param1} with {param2}"
```

### Permission System

Plugins must declare and request permissions:

```python
# Check permissions before sensitive operations
if await self.sdk.check_permission("fs.write", "/path/to/file"):
    # Write file
    pass
else:
    # Handle permission denied
    pass

# Track permission usage
await self.sdk.track_feature_usage("file_write_operation")
```

## Security Features

### Sandboxing

Plugins run in isolated environments with:
- Memory limits (default: 256MB)
- CPU limits (default: 50%)
- Network restrictions
- File system access controls
- Execution timeouts

### Code Validation

All plugin code is automatically scanned for:
- Dangerous function calls (`exec`, `eval`, etc.)
- Unauthorized imports
- Security vulnerabilities
- Malicious patterns

### Permission Model

Fine-grained permissions control access to:
- File system operations
- Network requests
- Database operations
- API endpoints
- User data
- System configuration

## Installation and Marketplace

### Plugin Installation

```bash
# Install from marketplace
curl -X POST "/api/v1/plugins/marketplace/install" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"plugin_id": "slack-integration", "version": "1.2.0"}'

# Install from file
curl -X POST "/api/v1/plugins/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@my-plugin.zip"
```

### Plugin Package Format

Plugins are distributed as ZIP archives containing:

```
my-plugin.zip
├── plugin.json          # Plugin manifest
├── plugin.py           # Main plugin code
├── requirements.txt    # Python dependencies
├── README.md          # Plugin documentation
├── LICENSE            # License file
└── assets/            # Static assets
    ├── icon.png
    └── screenshots/
```

### Plugin Manifest (plugin.json)

```json
{
  "id": "my-plugin",
  "name": "My Awesome Plugin",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": "Author Name",
  "author_email": "author@example.com",
  "homepage": "https://github.com/author/my-plugin",
  "repository": "https://github.com/author/my-plugin",
  "plugin_type": "integration",
  "entry_point": "MyPlugin",
  "module_path": "plugin",
  "bluebirdHub_version": ">=1.0.0",
  "python_version": ">=3.8",
  "permissions": [
    {
      "permission": "net.http",
      "scope": "global",
      "description": "Make HTTP requests",
      "required": true
    }
  ],
  "dependencies": [],
  "tags": ["integration", "api"],
  "category": "productivity"
}
```

## API Reference

### Plugin Management APIs

- `GET /api/v1/plugins` - List all plugins
- `GET /api/v1/plugins/{id}` - Get plugin details
- `POST /api/v1/plugins/{id}/activate` - Activate plugin
- `POST /api/v1/plugins/{id}/deactivate` - Deactivate plugin
- `DELETE /api/v1/plugins/{id}` - Uninstall plugin

### Configuration APIs

- `GET /api/v1/plugins/{id}/config` - Get plugin configuration
- `POST /api/v1/plugins/{id}/config` - Update plugin configuration
- `GET /api/v1/plugins/{id}/config/schema` - Get configuration schema

### Marketplace APIs

- `GET /api/v1/plugins/marketplace/search` - Search marketplace
- `POST /api/v1/plugins/marketplace/install` - Install from marketplace
- `GET /api/v1/plugins/marketplace/updates` - Check for updates

### Analytics APIs

- `GET /api/v1/plugins/{id}/analytics` - Get plugin analytics
- `GET /api/v1/plugins/analytics/overview` - System overview
- `GET /api/v1/plugins/analytics/alerts` - Get system alerts

## Example Plugins

### 1. Slack Integration Plugin

Provides Slack integration with features:
- Task notifications
- File upload notifications
- Workspace sharing alerts
- Two-way synchronization
- Custom message sending

### 2. GitHub Integration Plugin

Connects with GitHub for:
- Issue synchronization
- Repository monitoring
- Automatic issue creation from tasks
- Webhook integration
- Pull request tracking

### 3. AI Task Assistant Plugin

AI-powered productivity features:
- Intelligent task suggestions
- Smart scheduling
- Completion time prediction
- Dependency detection
- Workload optimization

## Monitoring and Analytics

### Plugin Health Monitoring

The system continuously monitors:
- Plugin performance metrics
- Error rates and exceptions
- Resource usage (CPU, memory)
- API response times
- User engagement

### Alerting System

Automatic alerts for:
- Performance degradation
- Security violations
- Resource limit breaches
- Plugin failures
- Dependency issues

### Usage Analytics

Track and analyze:
- Feature usage patterns
- User adoption rates
- Performance trends
- Error patterns
- Popular plugins

## Best Practices

### Development Guidelines

1. **Follow the SDK patterns** - Use provided base classes and helpers
2. **Handle errors gracefully** - Implement proper error handling and logging
3. **Respect resource limits** - Be mindful of memory and CPU usage
4. **Use semantic versioning** - Follow semver for version numbering
5. **Document thoroughly** - Provide clear documentation and examples

### Security Considerations

1. **Minimize permissions** - Only request necessary permissions
2. **Validate inputs** - Always validate user inputs and external data
3. **Secure credentials** - Use the secret configuration type for sensitive data
4. **Audit dependencies** - Regularly review third-party dependencies
5. **Test security** - Include security testing in your development process

### Performance Optimization

1. **Async operations** - Use async/await for I/O operations
2. **Efficient data structures** - Choose appropriate data structures
3. **Cache strategically** - Implement caching for expensive operations
4. **Monitor resources** - Track and optimize resource usage
5. **Profile regularly** - Use profiling tools to identify bottlenecks

## Troubleshooting

### Common Issues

1. **Plugin won't activate**
   - Check logs for initialization errors
   - Verify all required permissions are granted
   - Ensure dependencies are available

2. **Configuration errors**
   - Validate configuration against schema
   - Check for required fields
   - Verify data types and constraints

3. **Permission denied**
   - Review requested permissions
   - Check user has admin rights to grant permissions
   - Verify permission scope matches usage

4. **Performance issues**
   - Monitor resource usage metrics
   - Check for memory leaks
   - Optimize database queries and API calls

### Debug Mode

Enable debug mode for detailed logging:

```python
# In plugin code
self.logger.setLevel(logging.DEBUG)
self.logger.debug("Detailed debug information")

# Via configuration
await self.sdk.set_config("debug_mode", True)
```

### Health Checks

Monitor plugin health:

```bash
# Get plugin health status
curl "/api/v1/plugins/my-plugin" | jq '.health'

# Get system health overview
curl "/api/v1/plugins/health"
```

## Contributing

### Plugin Marketplace Submission

To submit a plugin to the marketplace:

1. Develop and test your plugin thoroughly
2. Create comprehensive documentation
3. Package following the standard format
4. Submit for security review
5. Provide support and maintenance

### Community Guidelines

- Follow coding standards and best practices
- Provide helpful documentation and examples
- Respond to user feedback and issues
- Keep plugins updated and secure
- Contribute to the plugin ecosystem

## Support and Resources

- **Documentation**: [https://docs.bluebirdhub.com/plugins](https://docs.bluebirdhub.com/plugins)
- **SDK Reference**: [https://sdk.bluebirdhub.com](https://sdk.bluebirdhub.com)
- **Community Forum**: [https://community.bluebirdhub.com](https://community.bluebirdhub.com)
- **GitHub Repository**: [https://github.com/bluebirdhub/plugins](https://github.com/bluebirdhub/plugins)
- **Support Email**: [plugins@bluebirdhub.com](mailto:plugins@bluebirdhub.com)

## License

The BlueBirdHub Plugin System is released under the MIT License. Individual plugins may have their own licensing terms.