#!/bin/bash

# Log Analyser Docker Setup Validation Script
# This script validates your Docker setup and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "🐳 Log Analyser Docker Setup Validation"
echo "========================================"
echo ""

# Check if Docker is installed
print_status "Checking if Docker is installed..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker installed: $DOCKER_VERSION"
else
    print_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi

# Check if Docker Compose is available
print_status "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose available: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    print_success "Docker Compose (built-in) available: $COMPOSE_VERSION"
else
    print_error "Docker Compose is not available."
    exit 1
fi

# Check if Docker is running
print_status "Checking if Docker daemon is running..."
if docker info &> /dev/null; then
    print_success "Docker daemon is running"
else
    print_warning "Docker daemon is not running. Please start Docker Desktop."
    echo "         You can continue with the setup, but you'll need to start Docker to run containers."
fi

# Check required files
print_status "Checking required files..."

REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile.backend"
    "dashboard-frontend/Dockerfile.frontend"
    "dashboard-frontend/nginx.conf"
    "requirements.txt"
    ".env.template"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found: $file"
    else
        print_error "Missing: $file"
        exit 1
    fi
done

# Check .env file
print_status "Checking environment configuration..."
if [ -f ".env" ]; then
    print_success "Found .env configuration file"
    
    # Check for sensitive values still using template defaults
    if grep -q "your-" .env; then
        print_warning "Found template values in .env - please update with your actual configuration"
    fi
else
    print_warning "No .env file found. You'll need to create one from .env.template"
    echo "         Run: cp .env.template .env"
fi

# Check port availability
print_status "Checking default ports availability..."

check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port ($service) is already in use"
        echo "         Consider using different ports in .env file"
    else
        print_success "Port $port ($service) is available"
    fi
}

check_port 3000 "Frontend"
check_port 8000 "Backend"

# Check disk space
print_status "Checking disk space..."
AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
REQUIRED_SPACE=2097152  # 2GB in KB

if [ "$AVAILABLE_SPACE" -gt "$REQUIRED_SPACE" ]; then
    print_success "Sufficient disk space available ($(($AVAILABLE_SPACE / 1024 / 1024))GB free)"
else
    print_warning "Low disk space. Docker build may fail. Consider freeing up space."
fi

# Check system resources
print_status "Checking system requirements..."

# Check available RAM
if command -v free &> /dev/null; then
    AVAILABLE_RAM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$AVAILABLE_RAM" -ge 8 ]; then
        print_success "Sufficient RAM available (${AVAILABLE_RAM}GB)"
    else
        print_warning "Limited RAM (${AVAILABLE_RAM}GB). Consider increasing Docker memory allocation."
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TOTAL_RAM=$(sysctl -n hw.memsize)
    TOTAL_RAM_GB=$((TOTAL_RAM / 1024 / 1024 / 1024))
    if [ "$TOTAL_RAM_GB" -ge 8 ]; then
        print_success "Sufficient RAM available (${TOTAL_RAM_GB}GB)"
    else
        print_warning "Limited RAM (${TOTAL_RAM_GB}GB). Monitor performance during operation."
    fi
fi

echo ""
echo "🔧 Setup Recommendations:"
echo "========================"
echo ""

if [ ! -f ".env" ]; then
    echo "1. Create environment configuration:"
    echo "   cp .env.template .env"
    echo "   nano .env  # Edit with your settings"
    echo ""
fi

echo "2. Start Docker Desktop if not running"
echo ""

echo "3. Build and run the application:"
echo "   ./docker-run.sh build"
echo "   ./docker-run.sh start"
echo ""

echo "4. Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""

echo "📚 For detailed instructions, see DOCKER_README.md"
echo ""

print_success "Validation completed! Your Docker setup looks good."
