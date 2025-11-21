# Docker Hub Setup for Release Workflow

This document explains how to set up Docker Hub integration for the release workflow.

## Required Secrets

The release workflow requires the following GitHub repository secret to be configured:

### `DOCKERHUB_TOKEN`

This is a Docker Hub access token that allows the GitHub Actions workflow to push images to Docker Hub.

#### Creating a Docker Hub Access Token

1. **Log in to Docker Hub**
   - Go to [hub.docker.com](https://hub.docker.com)
   - Log in with the `markcallen` account

2. **Create Access Token**
   - Click on your username in the top right corner
   - Select "Account Settings"
   - Go to the "Security" tab
   - Click "New Access Token"
   - Give it a descriptive name like "GitHub Actions - cached-yfinance"
   - Select appropriate permissions (Read, Write, Delete for the repository)
   - Click "Generate"
   - **Important**: Copy the token immediately as it won't be shown again

3. **Add Secret to GitHub Repository**
   - Go to the GitHub repository settings
   - Navigate to "Secrets and variables" → "Actions"
   - Click "New repository secret"
   - Name: `DOCKERHUB_TOKEN`
   - Value: Paste the Docker Hub access token
   - Click "Add secret"

## Docker Hub Repository

The workflow pushes images to: `markcallen/cached-yfinance`

### Repository Setup

1. **Create Repository** (if not exists)
   - Go to Docker Hub
   - Click "Create Repository"
   - Name: `cached-yfinance`
   - Visibility: Public (recommended for open source)
   - Description: "A high-performance caching wrapper around yfinance"

2. **Repository Settings**
   - Add appropriate description and README
   - Link to the GitHub repository
   - Set up automated builds (optional, as we're using GitHub Actions)

## Image Tags

The workflow automatically creates the following tags:

- `markcallen/cached-yfinance:latest` - Latest release
- `markcallen/cached-yfinance:v1.0.0` - Full version tag
- `markcallen/cached-yfinance:1.0.0` - Semantic version
- `markcallen/cached-yfinance:1.0` - Major.minor version
- `markcallen/cached-yfinance:1` - Major version

## Multi-Architecture Support

The workflow builds images for:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, including Apple Silicon)

This ensures compatibility across different platforms and cloud providers.

## Workflow Triggers

The Docker build and push happens automatically when:
1. A new tag is pushed that matches the pattern `v*` (e.g., `v1.0.0`, `v2.1.3`)
2. The Python package build and release steps complete successfully

## Troubleshooting

### Authentication Issues
- Verify the `DOCKERHUB_TOKEN` secret is correctly set
- Ensure the token has appropriate permissions
- Check that the token hasn't expired

### Build Failures
- Check the GitHub Actions logs for detailed error messages
- Verify the Dockerfile is valid and builds locally
- Ensure all required files are included in the build context

### Multi-Architecture Issues
- ARM64 builds may take longer than AMD64
- Some dependencies might not be available for all architectures
- Check the build logs for architecture-specific errors

## Testing

To test the Docker setup locally:

```bash
# Build multi-architecture image locally (requires Docker Buildx)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t test-image .

# Test the image
docker run --rm -e TICKER=AAPL -v $(pwd)/test-cache:/cache test-image
```

## Security Considerations

- The Docker Hub token should have minimal required permissions
- Regularly rotate access tokens
- Monitor Docker Hub for any unauthorized access
- Consider using Docker Hub's vulnerability scanning features
