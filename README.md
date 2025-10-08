# 🚀 Intelligent Log Analyzer & Alert Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **real-time, intelligent log analysis and monitoring system** that automates log collection, processing, and analysis from multiple sources. Leveraging **AWS Bedrock foundation models** for advanced anomaly detection and predictive insights to provide proactive monitoring and reduce system downtime.

## 📋 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

Traditional log analysis is often **time-consuming and reactive**. This project provides a **proactive, real-time, and intelligent** log monitoring solution designed for:

- **DevOps Engineers** & **Site Reliability Engineers (SREs)**
- **System Administrators** & **Developers**
- **IT firms, startups, and enterprises** managing distributed systems

### Target Use Cases
- Real-time anomaly detection and alerting
- Proactive system monitoring and reliability improvement
- Multi-source log aggregation and analysis
- Predictive insights for system maintenance

## ✨ Key Features

### 🔍 **Multi-Source Log Collection**
- 📂 **Local Files**: Monitor system logs, application logs, and custom log files
- ☁️ **AWS CloudWatch**: Automated stream selection and real-time collection
- 🌐 **REST APIs**: Flexible API log collection with authentication support
- 🖥️ **System Logs**: Syslog, Windows Event Logs support

### 🧠 **AI-Powered Analysis**
- 🤖 **AWS Bedrock Integration**: Advanced NLP models for anomaly detection
- 📊 **Pattern Recognition**: ML-based log classification and insights
- 🔮 **Predictive Analytics**: Proactive system health predictions
- 📈 **Real-time Processing**: < 2 second latency for log analysis

### 🚨 **Smart Alerting**
- 📧 **Email Notifications**: SMTP-based alert delivery
- 💬 **Slack Integration**: Real-time team notifications
- 🎯 **Intelligent Filtering**: Reduce alert fatigue with smart detection
- ⚡ **Real-time Dashboard**: Live monitoring and visualization

### 🎛️ **Advanced Dashboard**
- � **Interactive Visualizations**: Charts, graphs, and real-time metrics
- 🔍 **Advanced Search**: Full-text search with filtering capabilities
- 📱 **Responsive Design**: Modern, mobile-friendly interface
- 🎨 **Customizable Views**: Role-based access and personalized dashboards

### 🏗️ **Enterprise-Ready**
- 🔐 **Security**: Role-based authentication, SSL/TLS encryption
- 📈 **Scalability**: Handle 10,000+ log entries per minute
- 🐳 **Containerized**: Docker support for easy deployment
- 🔧 **Extensible**: Modular architecture for easy customization

## 🏛️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Log Sources   │───▶│  Collection Layer │───▶│ Processing Layer│
│                 │    │                  │    │                 │
│ • Local Files   │    │ • File Collector │    │ • Log Parser    │
│ • CloudWatch    │    │ • API Collector  │    │ • Normalizer    │
│ • REST APIs     │    │ • System Monitor │    │ • ML Pipeline   │
│ • System Logs   │    │ • Real-time      │    │ • AWS Bedrock   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Alert System │◀───│   Intelligence   │◀───│   Data Storage  │
│                 │    │     Layer        │    │                 │
│ • Email/SMTP    │    │ • Anomaly        │    │ • SQLite/Dev    │
│ • Slack Webhook │    │   Detection      │    │ • Elasticsearch │
│ • Dashboard     │    │ • Pattern Recog. │    │ • Real-time DB  │
│ • Real-time     │    │ • Predictive AI  │    │ • Search Index  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │  Web Dashboard  │
                       │                 │
                       │ • React.js UI   │
                       │ • FastAPI Backend│
                       │ • Real-time     │
                       │ • Visualizations│
                       └─────────────────┘
```

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python)
- **AI/ML**: AWS Bedrock, Scikit-learn
- **Database**: SQLite (dev), Elasticsearch (prod)
- **Authentication**: OAuth2, JWT tokens
- **API**: RESTful APIs with OpenAPI docs

#### Frontend  
- **Framework**: React.js 18+
- **Styling**: CSS3, Responsive design
- **State Management**: React Hooks
- **Charts**: Chart.js, D3.js integration
- **Build**: Webpack, Babel

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Cloud**: AWS (Bedrock, CloudWatch)
- **Monitoring**: Built-in metrics and health checks
- **Security**: SSL/TLS, Role-based access control

## ⚡ Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- AWS Account (for Bedrock features)
- Git

### 1-Minute Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/log-analyser.git
cd log-analyser

# Run with Docker (Recommended)
docker-compose up -d

# OR Run locally
./run-local.sh
```

Access the dashboard at: **http://localhost:3000**

## 📦 Installation

### Option 1: Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/log-analyser.git
cd log-analyser

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and settings

# Build and run
docker-compose up -d

# Check status
docker-compose ps
```

### Option 2: Local Development Setup

#### Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file with your settings

# Run backend
python -m uvicorn dashboard:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd dashboard-frontend

# Install dependencies
npm install

# Start development server
npm start
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-v2

# Alert Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
ALERT_RECIPIENT=alerts@yourcompany.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook

# Database Configuration
DATABASE_URL=sqlite:///logs.db
ELASTICSEARCH_URL=http://localhost:9200

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
```

### Log Sources Configuration

Edit `config.yaml`:

```yaml
log_source: "local"  # Options: local, cloudwatch, api

# Local file configuration
local_files:
  - path: "logs/app1.log"
    format: "text"
  - path: "logs/app2.log"
    format: "json"

# CloudWatch configuration
cloudwatch:
  log_group: "/aws/lambda/my-function"
  region: "us-east-1"
  auto_discover: true

# API configuration
api_sources:
  - url: "https://api.example.com/logs"
    method: "GET"
    headers:
      Authorization: "Bearer your-token"
    interval: 60
```

## 🚀 Usage

### Starting the System

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Dashboard Access

1. **Open Browser**: Navigate to `http://localhost:3000`
2. **Login**: Use default credentials (admin/password)
3. **Configure Sources**: Set up your log sources in the dashboard
4. **Monitor**: View real-time logs and alerts

### API Usage

The system provides RESTful APIs for programmatic access:

```bash
# Get log analytics
curl "http://localhost:8000/api/anomalies"

# Get system status
curl "http://localhost:8000/api/system/status"

# Search logs
curl "http://localhost:8000/api/logs?query=error&limit=100"
```

### CLI Commands

```bash
# Health check
python health-check.py

# Manual log processing
python -c "from processor.parser import process_logs; process_logs()"

# Generate sample data
python log_generator.py --count 1000
```

## � API Documentation

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/logs` | GET | Retrieve processed logs |
| `/api/anomalies` | GET | Get detected anomalies |
| `/api/alerts/pause` | POST | Pause/resume alerts |
| `/api/bedrock/insights` | GET | AI-generated insights |
| `/api/system/status` | GET | System health status |

### Authentication

```bash
# Get authentication token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/logs"
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for Swagger UI documentation.

## 🐳 Deployment

### Production Deployment

#### Docker Compose (Simple)
```bash
# Production configuration
cp docker-compose.prod.yml docker-compose.yml

# Deploy
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3
```

#### Kubernetes (Advanced)
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -l app=log-analyser
```

#### Cloud Deployment
- **AWS ECS**: Use provided task definitions
- **Google Cloud Run**: Deploy with Cloud Build
- **Azure Container Instances**: Use ARM templates

### Performance Tuning

#### High-Volume Environments
- **Elasticsearch**: For log storage and search
- **Redis**: For caching and session management
- **Load Balancing**: Multiple backend instances
- **Database Sharding**: Distribute log data

#### Monitoring
- **Health Checks**: Built-in endpoint monitoring
- **Metrics**: Prometheus-compatible metrics
- **Logging**: Structured JSON logging
- **Alerting**: Integration with monitoring tools

## 📈 Performance Requirements

- **Latency**: < 2 seconds for log processing
- **Throughput**: 10,000+ log entries per minute
- **Availability**: 99%+ uptime
- **Scalability**: Horizontal scaling support
- **Storage**: Configurable retention policies

## 🔒 Security Features

- **Authentication**: Role-based access control
- **Encryption**: SSL/TLS for all communications
- **API Security**: Token-based authentication
- **Data Privacy**: Configurable data retention
- **Audit Trail**: Comprehensive activity logging

## 🐛 Troubleshooting

### Common Issues

**Backend Won't Start**
```bash
# Check Python environment
python --version
pip list

# Check dependencies
pip install -r requirements.txt

# Check logs
tail -f logs/app.log
```

**Frontend Build Errors**
```bash
# Clear cache
npm ci
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+
```

**AWS Bedrock Issues**
```bash
# Verify credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/log-analyser/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/log-analyser/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/log-analyser/wiki)

## 🙏 Acknowledgments

- **AWS Bedrock** for AI/ML capabilities
- **FastAPI** for the amazing Python framework
- **React** community for frontend tools
- **Open Source** contributors and maintainers

## �️ Roadmap

### Version 2.0 (Planned)
- [ ] **Grafana Integration**: Advanced visualization
- [ ] **Prometheus Metrics**: Enhanced monitoring
- [ ] **Multi-tenancy**: Support for multiple organizations
- [ ] **Advanced ML**: Custom model training
- [ ] **Mobile App**: iOS/Android companion app

### Long-term Goals
- [ ] **Edge Computing**: IoT device log collection  
- [ ] **Blockchain Logs**: Cryptocurrency transaction monitoring
- [ ] **Video Analytics**: Log analysis from video streams
- [ ] **Voice Alerts**: Audio notification system

---

<div align="center">

**⭐ Star this repository if you find it helpful!**


</div>

