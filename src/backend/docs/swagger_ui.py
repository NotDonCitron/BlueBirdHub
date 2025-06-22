"""
Custom Swagger UI configuration for OrdnungsHub API
"""

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

def setup_custom_swagger_ui(app: FastAPI):
    """Setup custom Swagger UI with OrdnungsHub branding"""
    
    # Custom CSS for OrdnungsHub branding
    swagger_ui_css = """
    <style>
        .swagger-ui .topbar { 
            background-color: #1e40af; 
            border-bottom: 3px solid #3b82f6;
        }
        .swagger-ui .topbar .download-url-wrapper { 
            display: none; 
        }
        .swagger-ui .info .title {
            color: #1e40af;
            font-size: 36px;
            font-weight: bold;
        }
        .swagger-ui .info .description {
            color: #374151;
            font-size: 16px;
            line-height: 1.6;
        }
        .swagger-ui .scheme-container {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        .swagger-ui .opblock.opblock-get .opblock-summary-method {
            background: #10b981;
        }
        .swagger-ui .opblock.opblock-post .opblock-summary-method {
            background: #3b82f6;
        }
        .swagger-ui .opblock.opblock-put .opblock-summary-method {
            background: #f59e0b;
        }
        .swagger-ui .opblock.opblock-delete .opblock-summary-method {
            background: #ef4444;
        }
        .swagger-ui .btn.authorize {
            background-color: #1e40af;
            border-color: #1e40af;
        }
        .swagger-ui .btn.authorize:hover {
            background-color: #1d4ed8;
            border-color: #1d4ed8;
        }
        .swagger-ui .topbar .topbar-wrapper .link {
            content: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='30' viewBox='0 0 120 30'%3E%3Ctext x='10' y='20' fill='white' font-family='Arial, sans-serif' font-size='16' font-weight='bold'%3EOrdnungsHub%3C/text%3E%3C/svg%3E");
        }
        .swagger-ui .info .main .link {
            display: none;
        }
        .swagger-ui .topbar::after {
            content: "API Documentation";
            color: white;
            font-size: 14px;
            position: absolute;
            right: 20px;
            top: 15px;
        }
    </style>
    """
    
    # Custom JavaScript for enhanced functionality
    swagger_ui_js = """
    <script>
        window.onload = function() {
            // Add custom authentication helper
            const ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                // Custom request interceptor for better error handling
                requestInterceptor: function(request) {
                    // Add request timestamp for debugging
                    request.headers['X-Request-Time'] = new Date().toISOString();
                    return request;
                },
                // Custom response interceptor for better error messages
                responseInterceptor: function(response) {
                    if (response.status >= 400) {
                        console.log('API Error:', response);
                    }
                    return response;
                }
            });
            
            // Add authentication helper
            window.ui = ui;
            
            // Add custom authentication button functionality
            setTimeout(function() {
                const authButton = document.querySelector('.btn.authorize');
                if (authButton) {
                    authButton.addEventListener('click', function() {
                        console.log('Authentication dialog opened');
                    });
                }
            }, 1000);
        };
    </script>
    """
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI HTML with OrdnungsHub branding"""
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OrdnungsHub API Documentation</title>
            <link rel="icon" type="image/png" href="/favicon.png" />
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
            {swagger_ui_css}
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
            <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
            {swagger_ui_js}
        </body>
        </html>
        """)

def get_openapi_schema(app: FastAPI):
    """Enhanced OpenAPI schema with additional security definitions"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = app.openapi()
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service authentication"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]
    
    # Add custom extensions
    openapi_schema["x-logo"] = {
        "url": "https://ordnungshub.com/logo.png",
        "altText": "OrdnungsHub Logo"
    }
    
    # Add response examples for common error codes
    error_responses = {
        "400": {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Invalid request parameters"
                            }
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Could not validate credentials"
                            }
                        }
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Not enough permissions"
                            }
                        }
                    }
                }
            }
        },
        "404": {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Resource not found"
                            }
                        }
                    }
                }
            }
        },
        "422": {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "loc": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "msg": {"type": "string"},
                                        "type": {"type": "string"}
                                    }
                                },
                                "example": [
                                    {
                                        "loc": ["body", "name"],
                                        "msg": "field required",
                                        "type": "value_error.missing"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
        "500": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Internal server error occurred"
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Add common error responses to all paths
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "responses" in operation:
                for code, response in error_responses.items():
                    if code not in operation["responses"]:
                        operation["responses"][code] = response
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema