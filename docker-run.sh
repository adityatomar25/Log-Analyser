#!/bin/bash

# Log Analyser Docker Management Script
# This script helps you build and run the Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to create .env file if it doesn't exist
setup_env() {
    if [ ! -f .env ]; then
        print_warning "No .env file found. Creating from template..."
        cp .env.template .env
        print_warning "Please edit .env file with your configuration before running!"
        return 1
    fi
    return 0
}

# Function to build containers
build_containers() {
    print_status "Building Docker containers..."
    docker-compose build --no-cache
    print_success "Containers built successfully"
}

# Function to start containers
start_containers() {
    print_status "Starting Log Analyser containers..."
    docker-compose up -d
    print_success "Containers started successfully"
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are healthy
    if docker-compose ps | grep -q "Up (healthy)"; then
        print_success "Services are healthy!"
        echo ""
        echo "🚀 Log Analyser is now running:"
        echo "   📊 Frontend: http://localhost:${FRONTEND_PORT:-3000}"
        echo "   🔧 Backend API: http://localhost:${BACKEND_PORT:-8000}"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
    else
        print_warning "Services may still be starting up. Check with: docker-compose ps"
    fi
}

# Function to stop containers
stop_containers() {
    print_status "Stopping Log Analyser containers..."
    docker-compose down
    print_success "Containers stopped"
}

# Function to show logs
show_logs() {
    docker-compose logs -f
}

# Function to show status
show_status() {
    print_status "Container status:"
    docker-compose ps
    echo ""
    print_status "Service health:"
    docker-compose exec backend curl -f http://localhost:8000/api/system_logs/status 2>/dev/null || print_warning "Backend not ready"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v
    docker system prune -f
    print_success "Cleanup completed"
}

# Main script
case "${1:-help}" in
    "build")
        check_docker
        build_containers
        ;;
    "start")
        check_docker
        if setup_env; then
            start_containers
        else
            print_error "Please configure .env file first!"
            exit 1
        fi
        ;;
    "stop")
        check_docker
        stop_containers
        ;;
    "restart")
        check_docker
        stop_containers
        if setup_env; then
            start_containers
        fi
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "clean")
        check_docker
        cleanup
        ;;
    "help"|*)
        echo "Log Analyser Docker Management Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  build    - Build Docker containers"
        echo "  start    - Start the application"
        echo "  stop     - Stop the application"
        echo "  restart  - Restart the application"
        echo "  logs     - Show container logs"
        echo "  status   - Show container status"
        echo "  clean    - Clean up Docker resources"
        echo "  help     - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 build    # Build containers"
        echo "  $0 start    # Start application"
        echo "  $0 logs     # View logs"
        ;;
esac
