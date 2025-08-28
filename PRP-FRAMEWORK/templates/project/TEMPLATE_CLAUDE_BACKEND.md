# Backend Development Guidelines

## 🎯 Backend Architecture Overview
Best practices for building robust, scalable backend applications with {BACKEND_FRAMEWORK}, emphasizing performance, maintainability, and proper API design. Integrates with Complex Multi-Phase PRP framework for systematic backend development across project phases.

### 🚀 Web Framework Best Practices
- **Async Operations:** Use `async/await` for all I/O operations (if applicable)
- **Dependency Injection:** Leverage framework's DI system for clean architecture
- **Route Organization:** Group routes logically by feature or resource
- **Request Validation:** Use schema validation for all request/response data
- **Exception Handling:** Implement global exception handlers and proper error responses

### 📊 Data Model Patterns
```{LANGUAGE_EXTENSION}
# Example data model with validation
{DATA_MODEL_EXAMPLE}
```

### ⚡ Performance Best Practices
- **Response Times:** Optimize for fast response times (<{RESPONSE_TIME_TARGET}ms for simple operations)
- **Database Operations:** Use {DATABASE_APPROACH} with proper connection pooling
- **Memory Management:** Monitor memory usage and implement caching strategies
- **Background Tasks:** Use framework's background task system for non-blocking operations
- **Performance Baselines:** Establish and maintain performance metrics across development phases
- **Phase Continuity:** Don't degrade performance established in previous phases

### 🔄 Event Processing Architecture
```{LANGUAGE_EXTENSION}
# Generic event processing pipeline
{EVENT_PROCESSING_EXAMPLE}
```

### 🗄️ Database Patterns
```{LANGUAGE_EXTENSION}
# Database operations with {DATABASE_TYPE}
{DATABASE_EXAMPLE}
```

### 🔌 WebSocket Management (if applicable)
```{LANGUAGE_EXTENSION}
# Real-time WebSocket connections
{WEBSOCKET_EXAMPLE}
```

### 🚦 API Design Standards

#### RESTful API Conventions
- **Resource Naming:** Use nouns, not verbs: `/api/users`, `/api/orders`
- **HTTP Methods:** Follow REST conventions (GET, POST, PUT, DELETE)
- **Response Formats:** Consistent JSON structure across all endpoints
- **Status Codes:** Use appropriate HTTP status codes
- **Versioning:** Include API version in URL: `/api/v1/users`

#### Response Format Standards
```{LANGUAGE_EXTENSION}
# Standard success response
{SUCCESS_RESPONSE_EXAMPLE}

# Standard error response  
{ERROR_RESPONSE_EXAMPLE}
```

### 🧪 Testing Guidelines

#### Unit Tests
- **Test Coverage:** Maintain {TEST_COVERAGE_TARGET}% test coverage
- **Test Structure:** Follow {TESTING_FRAMEWORK} best practices
- **Mock External Dependencies:** Use mocks for external APIs and services
- **Database Tests:** Use test database or in-memory database

#### Integration Tests
- **API Testing:** Test all endpoints with realistic payloads
- **Database Integration:** Test database operations and transactions
- **Error Scenarios:** Test error handling and edge cases

### 🔐 Security Implementation

#### Authentication & Authorization
- **Secure Authentication:** Implement {AUTH_METHOD}
- **Input Validation:** Validate all inputs to prevent injection attacks
- **Rate Limiting:** Implement rate limiting for API endpoints
- **CORS Configuration:** Configure CORS properly for frontend access

#### Data Protection
- **Sensitive Data:** Hash passwords and encrypt sensitive information
- **API Keys:** Store API keys securely using {SECRET_MANAGEMENT}
- **SQL Injection Prevention:** Use parameterized queries
- **XSS Protection:** Sanitize all user inputs

### 📋 Code Organization

#### Project Structure
```
{BACKEND_DIR}/
├── {MAIN_MODULE}/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── {DOMAIN}_models.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── {DOMAIN}_service.py
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   └── {DOMAIN}_routes.py
│   ├── database/            # Database utilities
│   │   ├── __init__.py
│   │   └── connection.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── tests/                   # Test files
├── requirements.txt         # Dependencies
└── CLAUDE.md               # This file (auto-copied)
```

#### Naming Conventions
- **Files:** Use snake_case for Python files
- **Classes:** Use PascalCase for class names
- **Functions:** Use snake_case for function names
- **Constants:** Use UPPER_SNAKE_CASE for constants
- **Database Tables:** Use snake_case for table names

### 📊 Monitoring & Logging

#### Logging Standards
```{LANGUAGE_EXTENSION}
# Structured logging example
{LOGGING_EXAMPLE}
```

#### Performance Monitoring
- **Response Time Tracking:** Log response times for all endpoints
- **Error Rate Monitoring:** Track error rates and investigate anomalies
- **Resource Usage:** Monitor CPU, memory, and database connection usage
- **Custom Metrics:** Implement business-specific performance metrics

### 🔄 Phase Integration Guidelines

#### Context Continuity
- **Previous Phase APIs:** Use actual implementation details from previous phases
- **Database Schema:** Extend existing schema without breaking changes
- **Performance Baselines:** Maintain or improve performance from previous phases
- **Integration Points:** Document new APIs for future phase consumption

#### Forward Compatibility
- **API Versioning:** Design APIs to support future enhancements
- **Database Migrations:** Plan schema evolution strategy
- **Event Hooks:** Create extension points for future phases
- **Performance Monitoring:** Establish metrics for future optimization

### 🧱 Architecture Patterns

#### Clean Architecture
- **Domain Layer:** Core business logic independent of frameworks
- **Application Layer:** Use cases and application-specific business rules  
- **Infrastructure Layer:** External concerns (database, web, external APIs)
- **Interface Layer:** Controllers, presenters, and gateways

#### Dependency Management
- **Inversion of Control:** Depend on abstractions, not concretions
- **Single Responsibility:** Each module should have one reason to change
- **Open/Closed Principle:** Open for extension, closed for modification

### 🎯 Performance Targets

#### Response Time Goals
- **Simple Queries:** < {SIMPLE_QUERY_TARGET}ms
- **Complex Operations:** < {COMPLEX_OPERATION_TARGET}ms
- **File Operations:** < {FILE_OPERATION_TARGET}ms
- **External API Calls:** < {EXTERNAL_API_TARGET}ms

#### Throughput Goals
- **Concurrent Requests:** Handle {CONCURRENT_REQUESTS_TARGET} concurrent requests
- **Database Connections:** Optimize connection pool for {DB_CONNECTIONS_TARGET} connections
- **Memory Usage:** Keep memory usage under {MEMORY_USAGE_TARGET}MB

### ✅ Backend Definition of Done
- [ ] All API endpoints implemented and tested
- [ ] Database schema and operations optimized
- [ ] Authentication and authorization working
- [ ] Error handling and logging implemented
- [ ] Performance targets met
- [ ] Security best practices followed
- [ ] Unit and integration tests passing
- [ ] API documentation updated
- [ ] Phase integration points documented

---

## Template Customization Variables
Replace these placeholders when creating a new project:

- `{BACKEND_FRAMEWORK}` - e.g., "FastAPI", "Django", "Express.js", "Spring Boot"
- `{LANGUAGE_EXTENSION}` - e.g., "python", "javascript", "typescript", "java"
- `{DATA_MODEL_EXAMPLE}` - Framework-specific data model example
- `{RESPONSE_TIME_TARGET}` - e.g., "100", "200", "50"
- `{DATABASE_APPROACH}` - e.g., "async operations", "ORM queries", "raw SQL with pooling"
- `{DATABASE_TYPE}` - e.g., "SQLite", "PostgreSQL", "MongoDB", "MySQL"
- `{DATABASE_EXAMPLE}` - Database operation example in your tech stack
- `{WEBSOCKET_EXAMPLE}` - WebSocket implementation example (if needed)
- `{SUCCESS_RESPONSE_EXAMPLE}` - Standard success response format
- `{ERROR_RESPONSE_EXAMPLE}` - Standard error response format
- `{TEST_COVERAGE_TARGET}` - e.g., "90", "85", "95"
- `{TESTING_FRAMEWORK}` - e.g., "pytest", "Jest", "JUnit"
- `{AUTH_METHOD}` - e.g., "JWT tokens", "OAuth 2.0", "session-based auth"
- `{SECRET_MANAGEMENT}` - e.g., "environment variables", "Azure Key Vault", "AWS Secrets Manager"
- `{BACKEND_DIR}` - Backend directory name
- `{MAIN_MODULE}` - Main module name
- `{DOMAIN}` - Your business domain, e.g., "trading", "users", "orders"
- `{LOGGING_EXAMPLE}` - Logging implementation example
- `{SIMPLE_QUERY_TARGET}` - Simple query response time target in ms
- `{COMPLEX_OPERATION_TARGET}` - Complex operation response time target in ms
- `{FILE_OPERATION_TARGET}` - File operation response time target in ms
- `{EXTERNAL_API_TARGET}` - External API call response time target in ms
- `{CONCURRENT_REQUESTS_TARGET}` - Number of concurrent requests to handle
- `{DB_CONNECTIONS_TARGET}` - Optimal number of database connections
- `{MEMORY_USAGE_TARGET}` - Memory usage target in MB