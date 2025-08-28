# Frontend Development Guidelines

## 🎯 Frontend Architecture Overview
Best practices for building modern, responsive {FRONTEND_FRAMEWORK} applications with {FRONTEND_LANGUAGE}, emphasizing performance, accessibility, and maintainable component architecture. Integrates with Complex Multi-Phase PRP framework for systematic frontend development across project phases.

### ⚛️ Framework & Language Best Practices
- **Modern Components:** Use {COMPONENT_PATTERN} exclusively
- **Type Safety:** Enable strict type checking for better code quality
- **Component Composition:** Small, focused components with single responsibilities
- **Custom Logic:** Extract business logic into reusable {LOGIC_PATTERN}
- **Error Boundaries:** Wrap critical components to prevent UI crashes from unhandled errors

### 🔄 Real-Time Data Management
```{FRONTEND_LANGUAGE_EXTENSION}
// Real-time data connection example
{REALTIME_DATA_EXAMPLE}
```

### 🎨 Styling and UI Standards

#### Component Styling
```{STYLE_LANGUAGE}
/* Example styling approach with {STYLING_METHOD} */
{STYLING_EXAMPLE}
```

#### Responsive Design
- **Mobile First:** Design for mobile devices first, then scale up
- **Breakpoints:** Use consistent breakpoints across the application
- **Fluid Layouts:** Use flexible grid systems and relative units
- **Touch Targets:** Ensure touch targets are at least 44px for accessibility

#### Design System
- **Color Palette:** Use a consistent color palette across the application
- **Typography:** Maintain consistent font sizes and line heights
- **Spacing:** Use a standardized spacing scale (e.g., 4px, 8px, 16px, 32px)
- **Icons:** Use a consistent icon library

### 🔌 API Integration

#### HTTP Client Configuration
```{FRONTEND_LANGUAGE_EXTENSION}
// API client setup
{API_CLIENT_EXAMPLE}
```

#### State Management
```{FRONTEND_LANGUAGE_EXTENSION}
// State management pattern
{STATE_MANAGEMENT_EXAMPLE}
```

### 🚀 Performance Optimization

#### Code Splitting
```{FRONTEND_LANGUAGE_EXTENSION}
// Lazy loading example
{LAZY_LOADING_EXAMPLE}
```

#### Optimization Strategies
- **Bundle Size:** Keep bundle size under {BUNDLE_SIZE_TARGET}
- **Render Performance:** Optimize renders to maintain 60fps
- **Memory Management:** Prevent memory leaks from subscriptions and timers
- **Image Optimization:** Use appropriate image formats and lazy loading
- **Caching Strategy:** Implement effective caching for API calls and static assets

### 📱 User Experience Guidelines

#### Loading States
```{FRONTEND_LANGUAGE_EXTENSION}
// Loading state management
{LOADING_STATE_EXAMPLE}
```

#### Error Handling
```{FRONTEND_LANGUAGE_EXTENSION}
// Error boundary implementation
{ERROR_HANDLING_EXAMPLE}
```

#### Accessibility Standards
- **Semantic HTML:** Use appropriate HTML elements for their intended purpose
- **ARIA Labels:** Provide descriptive labels for screen readers
- **Keyboard Navigation:** Ensure all interactive elements are keyboard accessible
- **Color Contrast:** Maintain WCAG AA color contrast ratios
- **Focus Management:** Provide clear focus indicators and logical tab order

### 🧪 Testing Guidelines

#### Component Testing
```{FRONTEND_LANGUAGE_EXTENSION}
// Component test example
{COMPONENT_TEST_EXAMPLE}
```

#### Integration Testing
- **User Interactions:** Test user workflows and interactions
- **API Integration:** Test API calls and data handling
- **Real-time Features:** Test WebSocket connections and real-time updates
- **Error Scenarios:** Test error states and recovery

#### Testing Strategy
- **Unit Tests:** Test individual components and utilities
- **Integration Tests:** Test component interactions and data flow
- **E2E Tests:** Test complete user workflows
- **Visual Regression Tests:** Test UI consistency across changes

### 📋 Code Organization

#### Project Structure
```
{FRONTEND_DIR}/
├── public/                  # Static assets
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Generic components
│   │   └── {DOMAIN}/        # Domain-specific components
│   ├── hooks/              # Custom hooks/composables
│   ├── services/           # API and business logic
│   ├── types/              # Type definitions
│   ├── utils/              # Utility functions
│   ├── styles/             # Global styles and themes
│   ├── constants/          # Application constants
│   └── {ENTRY_POINT}       # Application entry point
├── tests/                  # Test files
├── {CONFIG_FILES}          # Configuration files
└── CLAUDE.md              # This file (auto-copied)
```

#### Naming Conventions
- **Components:** Use PascalCase for component names
- **Files:** Use kebab-case or PascalCase for component files
- **Variables:** Use camelCase for variables and functions
- **Constants:** Use UPPER_SNAKE_CASE for constants
- **CSS Classes:** Use kebab-case or BEM methodology

### 🔒 Security Implementation

#### Input Validation
```{FRONTEND_LANGUAGE_EXTENSION}
// Input validation example
{INPUT_VALIDATION_EXAMPLE}
```

#### Security Best Practices
- **XSS Prevention:** Sanitize user inputs and use safe HTML rendering
- **CSRF Protection:** Implement CSRF tokens for state-changing operations
- **Secure Storage:** Store sensitive data securely (avoid localStorage for tokens)
- **Content Security Policy:** Implement CSP headers
- **Dependency Security:** Regularly audit and update dependencies

### 📊 Analytics and Monitoring

#### Performance Monitoring
```{FRONTEND_LANGUAGE_EXTENSION}
// Performance tracking example
{PERFORMANCE_MONITORING_EXAMPLE}
```

#### User Analytics
- **User Interactions:** Track important user actions and flows
- **Performance Metrics:** Monitor Core Web Vitals and loading times
- **Error Tracking:** Implement error reporting and monitoring
- **A/B Testing:** Set up infrastructure for feature testing

### 🔄 Phase Integration Guidelines

#### Context Continuity
- **Backend Integration:** Use actual API endpoints from backend phases
- **Real-time Features:** Connect to actual WebSocket endpoints
- **Performance Baselines:** Maintain UI performance from previous phases
- **State Management:** Integrate with established data patterns

#### Forward Compatibility
- **Component Library:** Build reusable components for future phases
- **API Abstraction:** Create service layers that can evolve
- **State Structure:** Design state management for future features
- **Performance Monitoring:** Establish metrics for optimization

### 🎯 Performance Targets

#### Loading Performance
- **First Contentful Paint:** < {FCP_TARGET}ms
- **Largest Contentful Paint:** < {LCP_TARGET}ms
- **Time to Interactive:** < {TTI_TARGET}ms
- **Bundle Size:** < {BUNDLE_SIZE_TARGET}KB

#### Runtime Performance
- **Frame Rate:** Maintain 60fps during interactions
- **Memory Usage:** Keep memory usage under {MEMORY_TARGET}MB
- **API Response Handling:** Process API responses in < {API_PROCESSING_TARGET}ms
- **Real-time Updates:** Display real-time data within {REALTIME_TARGET}ms

### ✅ Frontend Definition of Done
- [ ] All components render correctly across target browsers
- [ ] Responsive design works on mobile, tablet, and desktop
- [ ] Accessibility standards met (WCAG AA)
- [ ] Performance targets achieved
- [ ] Error handling implemented for all user flows
- [ ] Unit and integration tests passing
- [ ] Code follows established conventions
- [ ] Documentation updated for new components
- [ ] Security best practices implemented

---

## Template Customization Variables
Replace these placeholders when creating a new project:

- `{FRONTEND_FRAMEWORK}` - e.g., "React", "Vue.js", "Angular", "Svelte"
- `{FRONTEND_LANGUAGE}` - e.g., "TypeScript", "JavaScript"
- `{COMPONENT_PATTERN}` - e.g., "functional components with hooks", "composition API", "reactive components"
- `{LOGIC_PATTERN}` - e.g., "custom hooks", "composables", "services"
- `{FRONTEND_LANGUAGE_EXTENSION}` - e.g., "typescript", "javascript", "jsx", "vue"
- `{REALTIME_DATA_EXAMPLE}` - Framework-specific real-time data example
- `{STYLE_LANGUAGE}` - e.g., "scss", "css", "styled-components"
- `{STYLING_METHOD}` - e.g., "CSS Modules", "Styled Components", "Tailwind CSS"
- `{STYLING_EXAMPLE}` - Styling approach example
- `{API_CLIENT_EXAMPLE}` - HTTP client setup example
- `{STATE_MANAGEMENT_EXAMPLE}` - State management pattern example
- `{LAZY_LOADING_EXAMPLE}` - Code splitting/lazy loading example
- `{BUNDLE_SIZE_TARGET}` - Bundle size target in KB
- `{LOADING_STATE_EXAMPLE}` - Loading state management example
- `{ERROR_HANDLING_EXAMPLE}` - Error handling implementation
- `{COMPONENT_TEST_EXAMPLE}` - Component testing example
- `{FRONTEND_DIR}` - Frontend directory name
- `{DOMAIN}` - Your business domain
- `{ENTRY_POINT}` - Application entry point file
- `{CONFIG_FILES}` - Configuration files list
- `{INPUT_VALIDATION_EXAMPLE}` - Input validation implementation
- `{PERFORMANCE_MONITORING_EXAMPLE}` - Performance monitoring setup
- `{FCP_TARGET}` - First Contentful Paint target in ms
- `{LCP_TARGET}` - Largest Contentful Paint target in ms
- `{TTI_TARGET}` - Time to Interactive target in ms
- `{MEMORY_TARGET}` - Memory usage target in MB
- `{API_PROCESSING_TARGET}` - API response processing target in ms
- `{REALTIME_TARGET}` - Real-time data display target in ms