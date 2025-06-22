#!/usr/bin/env python3
"""
SDK Generation Script for OrdnungsHub API

This script generates TypeScript and Python client SDKs from the OpenAPI specification.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

import requests
from loguru import logger


class SDKGenerator:
    """Generate client SDKs for different programming languages"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.output_dir = Path(__file__).parent.parent.parent.parent / "sdks"
        self.output_dir.mkdir(exist_ok=True)
    
    def fetch_openapi_spec(self) -> Dict[str, Any]:
        """Fetch OpenAPI specification from the running API"""
        try:
            response = requests.get(f"{self.api_base_url}/openapi.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch OpenAPI spec: {e}")
            raise
    
    def save_openapi_spec(self, spec: Dict[str, Any]) -> Path:
        """Save OpenAPI spec to temporary file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec, f, indent=2)
            return Path(f.name)
    
    def generate_typescript_sdk(self, spec_file: Path) -> bool:
        """Generate TypeScript/JavaScript SDK"""
        try:
            ts_output_dir = self.output_dir / "typescript"
            ts_output_dir.mkdir(exist_ok=True)
            
            # Use openapi-generator to create TypeScript client
            cmd = [
                "npx", "@openapitools/openapi-generator-cli", "generate",
                "-i", str(spec_file),
                "-g", "typescript-axios",
                "-o", str(ts_output_dir),
                "--additional-properties",
                "npmName=ordnungshub-api-client,npmVersion=0.1.0,supportsES6=true,withSeparateModelsAndApi=true"
            ]
            
            subprocess.run(cmd, check=True, cwd=ts_output_dir.parent)
            
            # Create enhanced TypeScript client with examples
            self._create_typescript_wrapper(ts_output_dir)
            
            logger.info(f"TypeScript SDK generated at: {ts_output_dir}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate TypeScript SDK: {e}")
            return False
    
    def generate_python_sdk(self, spec_file: Path) -> bool:
        """Generate Python SDK"""
        try:
            py_output_dir = self.output_dir / "python"
            py_output_dir.mkdir(exist_ok=True)
            
            # Use openapi-generator to create Python client
            cmd = [
                "npx", "@openapitools/openapi-generator-cli", "generate", 
                "-i", str(spec_file),
                "-g", "python",
                "-o", str(py_output_dir),
                "--additional-properties",
                "packageName=ordnungshub_client,projectName=ordnungshub-api-client,packageVersion=0.1.0"
            ]
            
            subprocess.run(cmd, check=True, cwd=py_output_dir.parent)
            
            # Create enhanced Python client with examples
            self._create_python_wrapper(py_output_dir)
            
            logger.info(f"Python SDK generated at: {py_output_dir}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate Python SDK: {e}")
            return False
    
    def _create_typescript_wrapper(self, output_dir: Path):
        """Create enhanced TypeScript client wrapper with examples"""
        wrapper_content = '''/**
 * OrdnungsHub API Client - Enhanced TypeScript SDK
 * 
 * This wrapper provides a more convenient interface for the OrdnungsHub API
 * with built-in authentication, error handling, and type safety.
 */

import { Configuration, DefaultApi, AuthenticationApi } from './api';
import { AxiosResponse } from 'axios';

export interface OrdnungsHubConfig {
  baseURL?: string;
  accessToken?: string;
}

export class OrdnungsHubClient {
  private config: Configuration;
  private authApi: AuthenticationApi;
  private defaultApi: DefaultApi;
  private accessToken?: string;

  constructor(config: OrdnungsHubConfig = {}) {
    this.config = new Configuration({
      basePath: config.baseURL || 'http://localhost:8000',
      accessToken: config.accessToken,
    });
    
    this.authApi = new AuthenticationApi(this.config);
    this.defaultApi = new DefaultApi(this.config);
    this.accessToken = config.accessToken;
  }

  /**
   * Authenticate with username and password
   */
  async login(username: string, password: string): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await this.authApi.login(formData);
      this.accessToken = response.data.access_token;
      
      // Update configuration with new token
      this.config = new Configuration({
        ...this.config,
        accessToken: this.accessToken,
      });
      
      this.authApi = new AuthenticationApi(this.config);
      this.defaultApi = new DefaultApi(this.config);
      
      return this.accessToken;
    } catch (error) {
      throw new Error(`Login failed: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Register a new user
   */
  async register(username: string, email: string, password: string): Promise<string> {
    try {
      const response = await this.authApi.register({
        username,
        email,
        password
      });
      
      this.accessToken = response.data.access_token;
      
      // Update configuration with new token
      this.config = new Configuration({
        ...this.config,
        accessToken: this.accessToken,
      });
      
      return this.accessToken;
    } catch (error) {
      throw new Error(`Registration failed: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Get current user information
   */
  async getCurrentUser() {
    if (!this.accessToken) {
      throw new Error('Not authenticated. Please login first.');
    }
    
    try {
      const response = await this.authApi.readUsersMe();
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get user info: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Get all workspaces
   */
  async getWorkspaces(skip: number = 0, limit: number = 100) {
    try {
      const response = await this.defaultApi.getWorkspaces(skip, limit);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get workspaces: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Create a new workspace
   */
  async createWorkspace(workspaceData: any) {
    try {
      const response = await this.defaultApi.createWorkspace(workspaceData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create workspace: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Get tasks for a workspace
   */
  async getTasks(workspaceId?: number, skip: number = 0, limit: number = 100) {
    try {
      const response = await this.defaultApi.getTasks(skip, limit, undefined, workspaceId);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get tasks: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.defaultApi.healthCheck();
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.response?.data?.detail || error.message}`);
    }
  }
}

export default OrdnungsHubClient;

// Example usage:
/*
import OrdnungsHubClient from './ordnungshub-client';

const client = new OrdnungsHubClient({
  baseURL: 'https://api.ordnungshub.com'
});

// Login
const token = await client.login('username', 'password');

// Get user info
const user = await client.getCurrentUser();

// Get workspaces
const workspaces = await client.getWorkspaces();

// Create workspace
const newWorkspace = await client.createWorkspace({
  name: 'My Workspace',
  description: 'A workspace for my projects'
});
*/
'''
        
        wrapper_file = output_dir / "ordnungshub-client.ts"
        wrapper_file.write_text(wrapper_content)
        
        # Create package.json
        package_json = {
            "name": "ordnungshub-api-client",
            "version": "0.1.0",
            "description": "TypeScript client SDK for OrdnungsHub API",
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "tsc",
                "prepublishOnly": "npm run build"
            },
            "dependencies": {
                "axios": "^1.6.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0",
                "@types/node": "^20.0.0"
            },
            "repository": {
                "type": "git",
                "url": "https://github.com/ordnungshub/api-client-ts"
            },
            "keywords": ["ordnungshub", "api", "client", "typescript", "workspace", "task-management"],
            "author": "OrdnungsHub Team",
            "license": "MIT"
        }
        
        package_file = output_dir / "package.json" 
        package_file.write_text(json.dumps(package_json, indent=2))
    
    def _create_python_wrapper(self, output_dir: Path):
        """Create enhanced Python client wrapper with examples"""
        wrapper_content = '''"""
OrdnungsHub API Client - Enhanced Python SDK

This wrapper provides a more convenient interface for the OrdnungsHub API
with built-in authentication, error handling, and Pythonic interfaces.
"""

import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin


class OrdnungsHubClient:
    """
    Enhanced Python client for OrdnungsHub API
    
    Examples:
        >>> client = OrdnungsHubClient("https://api.ordnungshub.com")
        >>> token = client.login("username", "password")
        >>> workspaces = client.get_workspaces()
        >>> user = client.get_current_user()
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", access_token: Optional[str] = None):
        """
        Initialize the OrdnungsHub client
        
        Args:
            base_url: Base URL of the OrdnungsHub API
            access_token: Optional JWT access token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        
        if access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {access_token}"
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated API request"""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get('detail', str(e))
            except:
                error_detail = str(e)
            
            raise OrdnungsHubAPIError(f"API request failed: {error_detail}", e.response)
        except requests.exceptions.RequestException as e:
            raise OrdnungsHubAPIError(f"Request failed: {str(e)}")
    
    def login(self, username: str, password: str) -> str:
        """
        Authenticate with username and password
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            JWT access token
            
        Raises:
            OrdnungsHubAPIError: If authentication fails
        """
        data = {
            "username": username,
            "password": password
        }
        
        response = self._make_request(
            "POST", 
            "/auth/login",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        
        # Update session headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })
        
        return self.access_token
    
    def register(self, username: str, email: str, password: str) -> str:
        """
        Register a new user account
        
        Args:
            username: Desired username
            email: User's email address
            password: User's password
            
        Returns:
            JWT access token
            
        Raises:
            OrdnungsHubAPIError: If registration fails
        """
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        response = self._make_request("POST", "/auth/register", json=data)
        token_data = response.json()
        self.access_token = token_data["access_token"]
        
        # Update session headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })
        
        return self.access_token
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current user information
        
        Returns:
            User profile data
            
        Raises:
            OrdnungsHubAPIError: If not authenticated or request fails
        """
        if not self.access_token:
            raise OrdnungsHubAPIError("Not authenticated. Please login first.")
        
        response = self._make_request("GET", "/auth/me")
        return response.json()
    
    def get_workspaces(self, skip: int = 0, limit: int = 100, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get user's workspaces
        
        Args:
            skip: Number of workspaces to skip (pagination)
            limit: Maximum number of workspaces to return
            user_id: Optional user ID filter
            
        Returns:
            List of workspace data
        """
        params = {"skip": skip, "limit": limit}
        if user_id:
            params["user_id"] = user_id
        
        response = self._make_request("GET", "/workspaces/", params=params)
        return response.json()
    
    def create_workspace(self, name: str, description: str = "", theme: str = "default", **kwargs) -> Dict[str, Any]:
        """
        Create a new workspace
        
        Args:
            name: Workspace name
            description: Workspace description
            theme: Workspace theme
            **kwargs: Additional workspace parameters
            
        Returns:
            Created workspace data
        """
        data = {
            "name": name,
            "description": description,
            "theme": theme,
            **kwargs
        }
        
        response = self._make_request("POST", "/workspaces/", json=data)
        return response.json()
    
    def get_workspace(self, workspace_id: int) -> Dict[str, Any]:
        """
        Get a specific workspace
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            Workspace data
        """
        response = self._make_request("GET", f"/workspaces/{workspace_id}")
        return response.json()
    
    def update_workspace(self, workspace_id: int, **updates) -> Dict[str, Any]:
        """
        Update a workspace
        
        Args:
            workspace_id: Workspace ID
            **updates: Fields to update
            
        Returns:
            Updated workspace data
        """
        response = self._make_request("PUT", f"/workspaces/{workspace_id}", json=updates)
        return response.json()
    
    def delete_workspace(self, workspace_id: int) -> Dict[str, str]:
        """
        Delete a workspace
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            Deletion confirmation
        """
        response = self._make_request("DELETE", f"/workspaces/{workspace_id}")
        return response.json()
    
    def get_tasks(self, skip: int = 0, limit: int = 100, workspace_id: Optional[int] = None, 
                  status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tasks with optional filtering
        
        Args:
            skip: Number of tasks to skip (pagination)
            limit: Maximum number of tasks to return
            workspace_id: Filter by workspace ID
            status: Filter by task status
            priority: Filter by task priority
            
        Returns:
            List of task data
        """
        params = {"skip": skip, "limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        
        response = self._make_request("GET", "/tasks/", params=params)
        return response.json()
    
    def health_check(self) -> Dict[str, str]:
        """
        Check API health status
        
        Returns:
            Health status information
        """
        response = self._make_request("GET", "/health")
        return response.json()


class OrdnungsHubAPIError(Exception):
    """Exception raised for OrdnungsHub API errors"""
    
    def __init__(self, message: str, response: Optional[requests.Response] = None):
        super().__init__(message)
        self.response = response


# Example usage:
if __name__ == "__main__":
    # Initialize client
    client = OrdnungsHubClient("http://localhost:8000")
    
    try:
        # Health check
        health = client.health_check()
        print(f"API Health: {health}")
        
        # Register or login
        try:
            token = client.register("testuser", "test@example.com", "testpassword")
            print(f"Registered successfully: {token[:20]}...")
        except OrdnungsHubAPIError:
            token = client.login("testuser", "testpassword")
            print(f"Logged in successfully: {token[:20]}...")
        
        # Get user info
        user = client.get_current_user()
        print(f"Current user: {user['username']} ({user['email']})")
        
        # Get workspaces
        workspaces = client.get_workspaces()
        print(f"Found {len(workspaces)} workspaces")
        
        # Create a workspace
        new_workspace = client.create_workspace(
            name="Test Workspace",
            description="A test workspace created via Python SDK"
        )
        print(f"Created workspace: {new_workspace['name']}")
        
    except OrdnungsHubAPIError as e:
        print(f"API Error: {e}")
'''
        
        wrapper_file = output_dir / "ordnungshub_client" / "enhanced_client.py"
        wrapper_file.parent.mkdir(exist_ok=True)
        wrapper_file.write_text(wrapper_content)
        
        # Create setup.py
        setup_content = '''from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ordnungshub-api-client",
    version="0.1.0",
    author="OrdnungsHub Team",
    author_email="api-support@ordnungshub.com",
    description="Python client SDK for OrdnungsHub API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ordnungshub/api-client-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    keywords="ordnungshub api client workspace task-management",
    project_urls={
        "Bug Reports": "https://github.com/ordnungshub/api-client-python/issues",
        "Source": "https://github.com/ordnungshub/api-client-python",
        "Documentation": "https://docs.ordnungshub.com/python-sdk",
    },
)
'''
        
        setup_file = output_dir / "setup.py"
        setup_file.write_text(setup_content)
    
    def generate_all_sdks(self) -> bool:
        """Generate all client SDKs"""
        try:
            logger.info("Fetching OpenAPI specification...")
            spec = self.fetch_openapi_spec()
            spec_file = self.save_openapi_spec(spec)
            
            logger.info("Generating TypeScript SDK...")
            ts_success = self.generate_typescript_sdk(spec_file)
            
            logger.info("Generating Python SDK...")
            py_success = self.generate_python_sdk(spec_file)
            
            # Clean up temporary file
            os.unlink(spec_file)
            
            if ts_success and py_success:
                logger.info("All SDKs generated successfully!")
                return True
            else:
                logger.warning("Some SDKs failed to generate")
                return False
                
        except Exception as e:
            logger.error(f"SDK generation failed: {e}")
            return False


if __name__ == "__main__":
    generator = SDKGenerator()
    success = generator.generate_all_sdks()
    exit(0 if success else 1)