# Frontend Development Guidelines

## 🎯 Frontend Architecture Overview
Best practices for building modern, responsive React applications with TypeScript, emphasizing performance, accessibility, and maintainable component architecture. Optimized for real-time trading dashboard with sub-50ms WebSocket update rendering and comprehensive alert management interface.

### ⚛️ React & TypeScript Best Practices
- **Modern Components:** Use functional components with hooks exclusively
- **Type Safety:** Enable strict TypeScript checking for better code quality
- **Component Composition:** Small, focused components with single responsibilities
- **Custom Logic:** Extract business logic into reusable custom hooks
- **Error Boundaries:** Wrap critical components to prevent UI crashes from unhandled errors
- **Real-time Data:** Use WebSocket hooks for market data with automatic reconnection

### 🔄 Real-Time Data Management
```typescript
// WebSocket hook for real-time market data
const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      // Automatic reconnection with exponential backoff
      setTimeout(() => connect(), Math.min(1000 * Math.pow(2, retryCount), 30000));
    };
    setSocket(ws);
  }, [url]);
  
  return { socket, isConnected, connect };
};
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
- **Bundle Size:** Keep bundle size under 2MB initial load, <500KB per lazy-loaded route
- **Render Performance:** Optimize renders to maintain 60fps during high-frequency market updates
- **Memory Management:** Prevent memory leaks from WebSocket subscriptions and timers
- **Real-time Updates:** <50ms WebSocket update rendering for trading efficiency
- **Caching Strategy:** React Query for API caching and optimistic updates

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
src/frontend/               # Frontend directory (Create React App structure)
├── public/                 # Static assets
├── src/                    # Source code directory
│   ├── components/         # Reusable UI components
│   ├── Dashboard/          # Dashboard-specific components
│   │   ├── InstrumentWatchlist.tsx
│   │   └── RealTimeStatus.tsx
│   ├── Rules/              # Alert rule components
│   │   ├── AlertRuleForm.tsx
│   │   └── RuleList.tsx
│   ├── History/            # Alert history components
│   │   └── AlertHistory.tsx
│   ├── Health/             # System health components
│   │   └── SystemHealth.tsx
│   └── common/             # Generic reusable components
├── hooks/                  # Custom React hooks
│   ├── useWebSocket.ts     # WebSocket connection hook
│   └── useRealTimeData.ts  # Real-time data management
├── services/               # API and business logic
│   ├── apiClient.ts        # HTTP API client
│   └── websocketService.ts # WebSocket service
├── context/                # React context providers
│   └── WebSocketContext.tsx
├── types/                  # TypeScript type definitions
├── utils/                  # Utility functions
│   └── formatters.ts       # Data formatting utilities
├── styles/                 # Styles and CSS
├── constants/              # Application constants
├── App.tsx                 # Main application component
├── index.tsx               # Application entry point
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── CLAUDE.md               # This file
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
- **Backend Integration:** Connect to Phase 1 FastAPI endpoints (/api/health, /api/instruments, /api/rules, /api/alerts)
- **Real-time Features:** Connect to /ws/realtime WebSocket for market data and alerts
- **Performance Baselines:** Maintain Phase 1 backend performance while adding <50ms UI rendering
- **State Management:** Integrate with Phase 1 database schema and data models

#### Forward Compatibility
- **Component Library:** Build reusable components for future phases
- **API Abstraction:** Create service layers that can evolve
- **State Structure:** Design state management for future features
- **Performance Monitoring:** Establish metrics for optimization

### 🎯 Performance Targets

#### Loading Performance
- **First Contentful Paint:** < 200ms
- **Largest Contentful Paint:** < 1000ms
- **Time to Interactive:** < 2000ms
- **Bundle Size:** < 2MB initial, <500KB per route

#### Runtime Performance
- **Frame Rate:** Maintain 60fps during high-frequency market data updates
- **Memory Usage:** Keep memory usage under 100MB additional browser memory
- **API Response Handling:** Process API responses in < 100ms
- **Real-time Updates:** Display WebSocket market data within 50ms
- **User Interactions:** All user interactions respond within 100ms

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