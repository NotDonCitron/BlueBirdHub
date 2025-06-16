# setup-tdd.ps1
# This script sets up the testing environment for TDD
# Run this script in an elevated PowerShell session if you encounter permission issues

# Set error handling
$ErrorActionPreference = "Stop"

# Function to check if a command exists
function Command-Exists {
    param ($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Warning "This script requires administrator privileges to install packages."
    Write-Host "Please run this script in an elevated PowerShell window (Run as Administrator)." -ForegroundColor Yellow
    exit 1
}

# Check for Node.js and npm
if (-not (Command-Exists "node" -or Command-Exists "node.exe")) {
    Write-Error "Node.js is not installed. Please install Node.js from https://nodejs.org/ and try again."
    exit 1
}

if (-not (Command-Exists "npm" -or Command-Exists "npm.cmd")) {
    Write-Error "npm is not found. Please ensure Node.js is installed correctly."
    exit 1
}

Write-Host "Setting up TDD environment..." -ForegroundColor Cyan

# Navigate to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Install global packages if needed
$globalPackages = @("jest", "jest-cli")
foreach ($pkg in $globalPackages) {
    if (-not (npm list -g $pkg --depth=0 2>$null)) {
        Write-Host "Installing global package: $pkg" -ForegroundColor Yellow
        npm install -g $pkg
    }
}

# Install project dependencies
Write-Host "Installing project dependencies..." -ForegroundColor Yellow

# Create a temporary package.json for installation
try {
    $originalPackageJson = Get-Content -Path "$projectRoot\package.json" -Raw | ConvertFrom-Json
    $tempPackageJson = $originalPackageJson.PSObject.Copy()
    
    # Remove the problematic package temporarily
    if ($tempPackageJson.dependencies.PSObject.Properties['@anthropic-ai/claude-code']) {
        $tempPackageJson.dependencies.PSObject.Properties.Remove('@anthropic-ai/claude-code')
        $tempPackageJson | ConvertTo-Json -Depth 10 | Set-Content -Path "$projectRoot\package.json" -Force
    }
    
    # Install dev dependencies
    $devDependencies = @(
        "jest-watch-typeahead",
        "jest-junit",
        "@testing-library/react",
        "@testing-library/jest-dom",
        "@testing-library/user-event",
        "jest-environment-jsdom",
        "identity-obj-proxy"
    )
    
    # Install each dev dependency individually to handle errors
    foreach ($dep in $devDependencies) {
        try {
            Write-Host "Installing $dep..." -ForegroundColor Yellow
            npm install --save-dev $dep
        }
        catch {
            Write-Warning "Failed to install $dep : $_"
        }
    }
    
    # Restore original package.json
    $originalPackageJson | ConvertTo-Json -Depth 10 | Set-Content -Path "$projectRoot\package.json" -Force
}
catch {
    # Ensure we restore the original package.json on error
    if ($originalPackageJson) {
        $originalPackageJson | ConvertTo-Json -Depth 10 | Set-Content -Path "$projectRoot\package.json" -Force
    }
    Write-Error "Error during dependency installation: $_"
    exit 1
}

# Create test setup file if it doesn't exist
$setupTestsPath = "$projectRoot\src\setupTests.js"
if (-not (Test-Path $setupTestsPath)) {
    @"
// Jest setup file
import '@testing-library/jest-dom';

// Mock any global browser APIs or other modules here
// For example:
// global.fetch = require('jest-fetch-mock');

// Add any other test setup code here
"@ | Set-Content -Path $setupTestsPath
    
    Write-Host "Created test setup file at $setupTestsPath" -ForegroundColor Green
}

# Create a sample test file if none exists
$sampleTestPath = "$projectRoot\src\__tests__\example.test.js"
if (-not (Test-Path "$projectRoot\src\__tests__")) {
    New-Item -ItemType Directory -Path "$projectRoot\src\__tests__" | Out-Null
}

if (-not (Test-Path $sampleTestPath)) {
    @"
/**
 * @jest-environment jsdom
 */

describe('Example Test Suite', () => {
    it('should pass a simple test', () => {
        expect(true).toBe(true);
    });

    it('should test a simple function', () => {
        const sum = (a, b) => a + b;
        expect(sum(2, 3)).toBe(5);
    });
});
"@ | Set-Content -Path $sampleTestPath
    
    Write-Host "Created sample test file at $sampleTestPath" -ForegroundColor Green
}

# Add test scripts to package.json if they don't exist
$packageJson = Get-Content -Path "$projectRoot\package.json" -Raw | ConvertFrom-Json
$scripts = @{
    "test" = "jest"
    "test:watch" = "jest --watch"
    "test:coverage" = "jest --coverage"
    "test:update" = "jest --updateSnapshot"
}

$needsUpdate = $false
foreach ($key in $scripts.Keys) {
    if (-not $packageJson.scripts.PSObject.Properties[$key]) {
        $packageJson.scripts | Add-Member -MemberType NoteProperty -Name $key -Value $scripts[$key] -Force
        $needsUpdate = $true
    }
}

if ($needsUpdate) {
    $packageJson | ConvertTo-Json -Depth 10 | Set-Content -Path "$projectRoot\package.json"
    Write-Host "Updated package.json with test scripts" -ForegroundColor Green
}

# Run the tests
Write-Host "Running tests to verify setup..." -ForegroundColor Cyan
try {
    npm test
    Write-Host "`n🎉 TDD setup completed successfully!" -ForegroundColor Green
    Write-Host "You can now start writing tests in the 'src/__tests__' directory."
    Write-Host "Use 'npm test' to run tests or 'npm run test:watch' for watch mode." -ForegroundColor Cyan
}
catch {
    Write-Error "Tests failed to run. Please check the error messages above."
    exit 1
}

# Instructions for WSL (if needed)
Write-Host "`nIf you encounter Windows-specific issues, consider using WSL (Windows Subsystem for Linux)." -ForegroundColor Yellow
Write-Host "1. Install WSL: wsl --install"
Write-Host "2. Set up a Linux distribution from Microsoft Store"
Write-Host "3. Run your Node.js project in the WSL environment"

Write-Host "`nFor more information, refer to the TDD_GUIDE.md file in your project root." -ForegroundColor Cyan
