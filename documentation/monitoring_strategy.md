# 📊 Monitoring Strategy for Document Intelligence Microservices

## 🏗️ Architecture Overview

Our monitoring system follows the industry-standard Prometheus pull-based architecture where each microservice exposes metrics endpoints that are scraped by a centralized Prometheus server.

```
┌─────────────────┐    HTTP GET /metrics    ┌─────────────────┐
│  Prometheus     │ ────────────────────────> │   Auth Service  │
│  Server Pod     │                          │   Pod           │
│                 │                          │ (Port 8000)     │
│ - Scrapes data  │                          │ /auth/metrics   │
│ - Stores data   │    HTTP GET /metrics    │                 │
│ - Queries data  │ ────────────────────────> ┌─────────────────┐
└─────────────────┘                          │ Text Extraction │
        │                                    │ Service Pod     │
        │                                    │ (Port 8001)     │
        │                                    │ /extract/metrics│
        │                 HTTP GET /metrics  └─────────────────┘
        │            ────────────────────────> ┌─────────────────┐
        │                                    │ Text Summary    │
        │                                    │ Service Pod     │
        │                                    │ (Port 8002)     │
        │                                    │ /health/metrics │
        └──────────────────────────────────> └─────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   Grafana Pod   │
            │                 │
            │ Queries         │
            │ Prometheus      │
            │ for dashboards  │
            └─────────────────┘
```

## 🎯 Metrics Strategy

### 📋 Golden Signals Framework

We'll implement the four golden signals of monitoring across all services:

1. **Latency**: How long it takes to service requests
2. **Traffic**: How much demand is being placed on the system
3. **Errors**: The rate of requests that fail
4. **Saturation**: How "full" the service is

## 🔍 Service-Specific Metrics

### 1. 🔐 Auth Service Metrics

**Endpoints to Monitor:**

- `POST /auth/register` - User registration
- `POST /auth/token` - JWT token generation (login)
- `GET /auth/users/me` - User profile retrieval
- `GET /auth/health` - Health check

**Business Metrics:**

```python
# User Registration Metrics
auth_registrations_total = Counter('auth_registrations_total', 'Total user registrations', ['status'])
auth_registration_duration = Histogram('auth_registration_duration_seconds', 'Time to complete registration')

# Authentication Metrics
auth_login_attempts_total = Counter('auth_login_attempts_total', 'Total login attempts', ['status', 'username'])
auth_token_generation_duration = Histogram('auth_token_generation_duration_seconds', 'JWT token generation time')
auth_active_sessions = Gauge('auth_active_sessions_total', 'Number of active user sessions')

# Database Metrics
auth_mysql_connections = Gauge('auth_mysql_connections_active', 'Active MySQL connections')
auth_mysql_query_duration = Histogram('auth_mysql_query_duration_seconds', 'MySQL query execution time', ['operation'])

# Security Metrics
auth_failed_login_attempts = Counter('auth_failed_login_attempts_total', 'Failed login attempts', ['username'])
auth_password_hash_duration = Histogram('auth_password_hash_duration_seconds', 'Password hashing time')
```

### 2. 📄 Text Extraction Service Metrics

**Endpoints to Monitor:**

- `POST /extract/image_text` - Image text extraction
- `GET /extract/document/{image_name}` - Document status retrieval
- `GET /extract/health` - Health check

**Business Metrics:**

```python
# Document Processing Metrics
extraction_requests_total = Counter('extraction_requests_total', 'Total extraction requests', ['status', 'user_id'])
extraction_processing_duration = Histogram('extraction_processing_duration_seconds', 'Time to extract text from image')
extraction_image_size_bytes = Histogram('extraction_image_size_bytes', 'Size of uploaded images')

# OpenAI API Metrics
extraction_openai_requests_total = Counter('extraction_openai_requests_total', 'OpenAI API calls', ['model', 'status'])
extraction_openai_duration = Histogram('extraction_openai_duration_seconds', 'OpenAI API response time')
extraction_openai_tokens_used = Counter('extraction_openai_tokens_used_total', 'Total tokens consumed', ['model'])
extraction_openai_cost_estimate = Counter('extraction_openai_cost_estimate_total', 'Estimated OpenAI costs in USD')

# MongoDB Metrics
extraction_mongodb_connections = Gauge('extraction_mongodb_connections_active', 'Active MongoDB connections')
extraction_mongodb_operation_duration = Histogram('extraction_mongodb_operation_duration_seconds', 'MongoDB operation time', ['operation'])
extraction_documents_stored_total = Counter('extraction_documents_stored_total', 'Documents stored in MongoDB')

# Redis Cache Metrics
extraction_redis_operations_total = Counter('extraction_redis_operations_total', 'Redis operations', ['operation', 'result'])
extraction_cache_hit_ratio = Gauge('extraction_cache_hit_ratio', 'Cache hit ratio percentage')
extraction_redis_connections = Gauge('extraction_redis_connections_active', 'Active Redis connections')

# SQS Metrics
extraction_sqs_messages_sent_total = Counter('extraction_sqs_messages_sent_total', 'Messages sent to SQS', ['status'])
extraction_sqs_send_duration = Histogram('extraction_sqs_send_duration_seconds', 'Time to send SQS message')

# File Processing Metrics
extraction_file_validation_duration = Histogram('extraction_file_validation_duration_seconds', 'File validation time')
extraction_base64_encoding_duration = Histogram('extraction_base64_encoding_duration_seconds', 'Image encoding time')
```

### 3. 📝 Text Summarization Service Metrics (Background Worker)

**Endpoints to Monitor:**

- `GET /health` - Health check (only HTTP endpoint)

**Business Metrics:**

```python
# SQS Worker Metrics
summarization_sqs_messages_received_total = Counter('summarization_sqs_messages_received_total', 'SQS messages received')
summarization_sqs_messages_processed_total = Counter('summarization_sqs_messages_processed_total', 'SQS messages processed', ['status'])
summarization_sqs_poll_duration = Histogram('summarization_sqs_poll_duration_seconds', 'SQS polling time')
summarization_message_processing_duration = Histogram('summarization_message_processing_duration_seconds', 'Time to process one message')

# Queue Health Metrics
summarization_queue_depth = Gauge('summarization_queue_depth', 'Current SQS queue depth')
summarization_message_age_seconds = Histogram('summarization_message_age_seconds', 'Age of messages when processed')
summarization_dlq_messages = Gauge('summarization_dlq_messages_total', 'Messages in Dead Letter Queue')

# OpenAI API Metrics
summarization_openai_requests_total = Counter('summarization_openai_requests_total', 'OpenAI summarization calls', ['status'])
summarization_openai_duration = Histogram('summarization_openai_duration_seconds', 'OpenAI summarization time')
summarization_openai_tokens_used = Counter('summarization_openai_tokens_used_total', 'Tokens used for summarization')
summarization_text_length_chars = Histogram('summarization_text_length_chars', 'Character count of text being summarized')
summarization_summary_length_chars = Histogram('summarization_summary_length_chars', 'Character count of generated summaries')

# MongoDB Update Metrics
summarization_mongodb_updates_total = Counter('summarization_mongodb_updates_total', 'MongoDB document updates', ['status'])
summarization_mongodb_update_duration = Histogram('summarization_mongodb_update_duration_seconds', 'Time to update MongoDB document')

# Worker Health Metrics
summarization_worker_restarts_total = Counter('summarization_worker_restarts_total', 'Worker process restarts')
summarization_concurrent_jobs = Gauge('summarization_concurrent_jobs', 'Number of jobs being processed concurrently')
```

## 🚀 Standard FastAPI Metrics

All services will include these standard web server metrics via `prometheus-fastapi-instrumentator`:

```python
# HTTP Request Metrics (Auto-generated)
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration')
http_request_size_bytes = Histogram('http_request_size_bytes', 'HTTP request size')
http_response_size_bytes = Histogram('http_response_size_bytes', 'HTTP response size')

# Application Metrics
app_info = Info('app_info', 'Application information')
app_uptime_seconds = Counter('app_uptime_seconds_total', 'Application uptime')
app_memory_usage_bytes = Gauge('app_memory_usage_bytes', 'Application memory usage')
app_cpu_usage_ratio = Gauge('app_cpu_usage_ratio', 'Application CPU usage ratio')
```

## 🏗️ Infrastructure Components

### Prometheus Server Configuration

```yaml
# Deployed as a single replica in doc-intel-app namespace
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-server
  namespace: doc-intel-app
spec:
  replicas: 1
  # ... configuration details
```

**Scrape Configuration:**

```yaml
scrape_configs:
  - job_name: "auth-service"
    static_configs:
      - targets: ["auth-service.doc-intel-app.svc.cluster.local:8000"]
    metrics_path: "/metrics"
    scrape_interval: 15s

  - job_name: "text-extraction-service"
    static_configs:
      - targets:
          ["text-extraction-service.doc-intel-app.svc.cluster.local:8001"]
    metrics_path: "/metrics"
    scrape_interval: 15s

  - job_name: "text-summarization-service"
    static_configs:
      - targets:
          ["text-summarization-service.doc-intel-app.svc.cluster.local:8002"]
    metrics_path: "/metrics"
    scrape_interval: 15s
```

### Grafana Configuration

- **Single replica deployment**
- **Persistent storage** for dashboards and configuration
- **Prometheus data source** pre-configured
- **Email alerting** to: kritiagrawal2597@gmail.com

## 📊 Implementation Phases

### Phase 1: Application Instrumentation

1. Add `prometheus-fastapi-instrumentator` to all service requirements
2. Implement custom business metrics in each service
3. Expose `/metrics` endpoints on all services
4. Test metrics endpoints locally

### Phase 2: Prometheus Deployment

1. Deploy Prometheus server using Helm chart
2. Configure scraping for all three services
3. Set up persistent storage for metrics data
4. Verify metrics collection

### Phase 3: Grafana Setup

1. Deploy Grafana with persistent storage
2. Configure Prometheus as data source
3. Import/create initial dashboards
4. Set up email alerting configuration

### Phase 4: Alerting Rules

1. Define critical alerting rules
2. Configure AlertManager for email notifications
3. Test alert routing to kritiagrawal2597@gmail.com
4. Set up escalation policies

## 🔔 Alerting Strategy

### Critical Alerts (Immediate Email)

- **Service Down**: Any service health check failing
- **High Error Rate**: >5% error rate for 5 minutes
- **OpenAI API Issues**: API calls failing consistently
- **Database Connection Loss**: Unable to connect to MySQL/MongoDB
- **Queue Backup**: >100 messages in summarization queue

### Warning Alerts (Daily Digest)

- **High Latency**: P95 response time >2 seconds
- **Resource Usage**: CPU/Memory >80% for 10 minutes
- **Cache Performance**: Redis hit ratio <70%
- **Queue Processing Slow**: Message age >5 minutes

## 💰 Cost Monitoring

- **OpenAI Token Usage**: Track tokens per service and per user
- **AWS Resource Utilization**: Monitor RDS, DocumentDB, SQS usage
- **Infrastructure Costs**: Track EKS cluster resource consumption

## 🎯 SLOs (Service Level Objectives)

- **Availability**: 99.5% uptime for all services
- **Latency**: P95 response time <2 seconds for all endpoints
- **Error Rate**: <1% error rate for all services
- **Processing Time**: Text extraction <30 seconds, summarization <60 seconds

## 📈 Dashboard Categories

### 1. Executive Dashboard

- System health overview
- Business KPIs (documents processed, users registered)
- Cost metrics and trends

### 2. Service Health Dashboard

- Individual service metrics
- Dependency health (OpenAI, databases, queues)
- Error rates and patterns

### 3. Infrastructure Dashboard

- Kubernetes cluster metrics
- Database performance
- Queue depths and processing rates

### 4. Business Analytics Dashboard

- User activity patterns
- Document processing trends
- API usage statistics

---

This monitoring strategy provides comprehensive observability into our Document Intelligence platform while maintaining simplicity and cost-effectiveness. The next step is to implement the application instrumentation across all three microservices.
