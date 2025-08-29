# Shared Code Development Guidelines

## 🎯 Shared Code Architecture Overview
Best practices for building reusable, type-safe shared code libraries that serve multiple components (frontend, backend, mobile, etc.). Emphasizes consistency, maintainability, and proper abstraction patterns. Integrates with Complex Multi-Phase PRP framework for systematic shared code development.

### 🔗 Shared Code Principles
- **Single Source of Truth:** Define types, constants, and utilities once
- **Framework Agnostic:** Keep shared code independent of specific frameworks
- **Type Safety:** Provide comprehensive type definitions for all shared elements
- **Backward Compatibility:** Maintain compatibility across component versions
- **Documentation:** Thoroughly document all shared interfaces and utilities

### 📋 Core Shared Components

#### Type Definitions
```{SHARED_LANGUAGE_EXTENSION}
// Core domain types
{TYPE_DEFINITIONS_EXAMPLE}
```

#### Constants and Configuration
```{SHARED_LANGUAGE_EXTENSION}
// Application constants
{CONSTANTS_EXAMPLE}
```

#### Utility Functions
```{SHARED_LANGUAGE_EXTENSION}
// Common utility functions
{UTILITIES_EXAMPLE}
```

#### Validation Schemas
```{SHARED_LANGUAGE_EXTENSION}
// Shared validation schemas
{VALIDATION_EXAMPLE}
```

### 🏗️ Code Organization

#### Project Structure
```
{SHARED_DIR}/
├── types/                  # Type definitions
│   ├── index.{EXT}        # Main type exports
│   ├── {DOMAIN}.{EXT}     # Domain-specific types
│   └── api.{EXT}          # API interface types
├── constants/             # Application constants
│   ├── index.{EXT}        # Main constant exports
│   ├── config.{EXT}       # Configuration constants
│   └── {DOMAIN}.{EXT}     # Domain constants
├── utils/                 # Utility functions
│   ├── index.{EXT}        # Main utility exports
│   ├── validation.{EXT}   # Validation utilities
│   ├── formatting.{EXT}   # Data formatting
│   └── {DOMAIN}.{EXT}     # Domain utilities
├── schemas/               # Validation schemas
│   ├── index.{EXT}        # Main schema exports
│   └── {DOMAIN}.{EXT}     # Domain schemas
├── interfaces/            # Interface definitions
│   ├── index.{EXT}        # Main interface exports
│   └── {DOMAIN}.{EXT}     # Domain interfaces
├── enums/                 # Enumeration definitions
│   ├── index.{EXT}        # Main enum exports
│   └── {DOMAIN}.{EXT}     # Domain enums
└── CLAUDE.md             # This file (auto-copied)
```

### 🔄 API Interface Standards

#### Request/Response Types
```{SHARED_LANGUAGE_EXTENSION}
// Standard API interfaces
{API_INTERFACES_EXAMPLE}
```

#### Error Handling Types
```{SHARED_LANGUAGE_EXTENSION}
// Error type definitions
{ERROR_TYPES_EXAMPLE}
```

### 📊 Data Model Standards

#### Domain Models
```{SHARED_LANGUAGE_EXTENSION}
// Core domain models
{DOMAIN_MODELS_EXAMPLE}
```

#### Temporal Data Patterns
```{SHARED_LANGUAGE_EXTENSION}
// Time-based data structures
{TEMPORAL_DATA_EXAMPLE}
```

### 🔧 Utility Library Design

#### Data Transformation
```{SHARED_LANGUAGE_EXTENSION}
// Data transformation utilities
{DATA_TRANSFORMATION_EXAMPLE}
```

#### Validation Helpers
```{SHARED_LANGUAGE_EXTENSION}
// Validation utility functions
{VALIDATION_HELPERS_EXAMPLE}
```

#### Formatting Utilities
```{SHARED_LANGUAGE_EXTENSION}
// Data formatting functions
{FORMATTING_UTILITIES_EXAMPLE}
```

### 🧪 Testing Shared Code

#### Type Testing
```{SHARED_LANGUAGE_EXTENSION}
// Type safety tests
{TYPE_TESTING_EXAMPLE}
```

#### Utility Testing
```{SHARED_LANGUAGE_EXTENSION}
// Utility function tests
{UTILITY_TESTING_EXAMPLE}
```

#### Compatibility Testing
- **Frontend Compatibility:** Test shared code works with frontend components
- **Backend Compatibility:** Validate backend can consume shared types
- **Version Compatibility:** Test backward compatibility across versions
- **Cross-Platform:** Ensure code works across different environments

### 📦 Package Management

#### Export Strategy
```{SHARED_LANGUAGE_EXTENSION}
// Main index file exports
{EXPORT_STRATEGY_EXAMPLE}
```

#### Versioning Strategy
- **Semantic Versioning:** Follow semver for all shared code changes
- **Breaking Changes:** Document and communicate breaking changes clearly
- **Deprecation:** Provide deprecation warnings before removing features
- **Migration Guides:** Create guides for major version upgrades

### 🔒 Security Considerations

#### Data Sanitization
```{SHARED_LANGUAGE_EXTENSION}
// Security utilities
{SECURITY_UTILITIES_EXAMPLE}
```

#### Sensitive Data Handling
- **No Hardcoded Secrets:** Never include secrets in shared code
- **Data Masking:** Provide utilities for masking sensitive information
- **Input Validation:** Comprehensive validation for all shared functions
- **Audit Trail:** Log usage of security-sensitive utilities

### ⚡ Performance Guidelines

#### Optimization Strategies
- **Tree Shaking:** Ensure shared code supports tree shaking
- **Lazy Loading:** Support lazy loading of heavy utilities
- **Memory Efficiency:** Optimize memory usage in shared utilities
- **Computation Caching:** Cache expensive computations appropriately

#### Performance Monitoring
```{SHARED_LANGUAGE_EXTENSION}
// Performance monitoring utilities
{PERFORMANCE_MONITORING_EXAMPLE}
```

### 🔄 Phase Integration Guidelines

#### Context Continuity
- **Type Evolution:** Extend types without breaking existing usage
- **Utility Enhancement:** Add new utilities while maintaining existing APIs
- **Backward Compatibility:** Ensure previous phase implementations continue working
- **Documentation Updates:** Keep shared code documentation current

#### Forward Compatibility
- **Extensible Design:** Design types and interfaces for future extension
- **Plugin Architecture:** Support plugin patterns for future enhancements
- **Configuration Points:** Provide configuration options for different use cases
- **Version Strategy:** Plan version evolution for future phases

### 📋 Code Quality Standards

#### Naming Conventions
- **Types:** Use PascalCase for type and interface names
- **Constants:** Use UPPER_SNAKE_CASE for constants
- **Functions:** Use camelCase for function names
- **Files:** Use kebab-case or camelCase for file names
- **Namespaces:** Use descriptive namespace organization

#### Documentation Standards
```{SHARED_LANGUAGE_EXTENSION}
// Documentation example
{DOCUMENTATION_EXAMPLE}
```

### 🔍 Code Review Guidelines

#### Review Checklist
- [ ] Types are properly defined and exported
- [ ] Utility functions have comprehensive error handling
- [ ] Breaking changes are documented and justified
- [ ] Test coverage includes edge cases
- [ ] Performance implications considered
- [ ] Security implications reviewed
- [ ] Documentation is clear and complete
- [ ] Backward compatibility maintained

### ✅ Shared Code Definition of Done
- [ ] All types are properly defined and exported
- [ ] Utility functions have comprehensive tests
- [ ] Documentation is complete and accurate
- [ ] No breaking changes without migration path
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] Frontend and backend compatibility validated
- [ ] Version compatibility tested
- [ ] Code review approved

### 🎯 Quality Targets

#### Code Coverage
- **Unit Tests:** > {TEST_COVERAGE_TARGET}% coverage
- **Type Coverage:** > {TYPE_COVERAGE_TARGET}% type coverage
- **Integration Tests:** All major utilities tested with consuming components

#### Performance Targets
- **Bundle Size:** Keep shared library under {SHARED_BUNDLE_TARGET}KB
- **Load Time:** Shared code imports should complete in < {IMPORT_TIME_TARGET}ms
- **Memory Usage:** Utilities should use < {UTILITY_MEMORY_TARGET}KB memory
- **Computation Speed:** Core utilities should execute in < {UTILITY_SPEED_TARGET}ms

---

## Template Customization Variables
Replace these placeholders when creating a new project:

- `{SHARED_LANGUAGE_EXTENSION}` - e.g., "typescript", "javascript", "python"
- `{TYPE_DEFINITIONS_EXAMPLE}` - Core type definitions for your domain
- `{CONSTANTS_EXAMPLE}` - Application constants example
- `{UTILITIES_EXAMPLE}` - Common utility functions example
- `{VALIDATION_EXAMPLE}` - Validation schema example
- `{SHARED_DIR}` - Shared code directory name
- `{EXT}` - File extension, e.g., "ts", "js", "py"
- `{DOMAIN}` - Your business domain
- `{API_INTERFACES_EXAMPLE}` - API interface definitions
- `{ERROR_TYPES_EXAMPLE}` - Error type definitions
- `{DOMAIN_MODELS_EXAMPLE}` - Domain model examples
- `{TEMPORAL_DATA_EXAMPLE}` - Time-based data structure examples
- `{DATA_TRANSFORMATION_EXAMPLE}` - Data transformation utilities
- `{VALIDATION_HELPERS_EXAMPLE}` - Validation helper functions
- `{FORMATTING_UTILITIES_EXAMPLE}` - Data formatting functions
- `{TYPE_TESTING_EXAMPLE}` - Type safety testing example
- `{UTILITY_TESTING_EXAMPLE}` - Utility function testing example
- `{EXPORT_STRATEGY_EXAMPLE}` - Main export file structure
- `{SECURITY_UTILITIES_EXAMPLE}` - Security utility functions
- `{PERFORMANCE_MONITORING_EXAMPLE}` - Performance monitoring utilities
- `{DOCUMENTATION_EXAMPLE}` - Documentation format example
- `{TEST_COVERAGE_TARGET}` - Unit test coverage target percentage
- `{TYPE_COVERAGE_TARGET}` - Type coverage target percentage
- `{SHARED_BUNDLE_TARGET}` - Bundle size target in KB
- `{IMPORT_TIME_TARGET}` - Import time target in ms
- `{UTILITY_MEMORY_TARGET}` - Memory usage target in KB
- `{UTILITY_SPEED_TARGET}` - Utility execution speed target in ms