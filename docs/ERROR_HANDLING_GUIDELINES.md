# Error Handling Guidelines - OrdnungsHub

## 🎯 Ziele

1. **Benutzerfreundlichkeit**: Klare, verständliche Fehlermeldungen
2. **Ausfallsicherheit**: Graceful Degradation bei Fehlern
3. **Debugging**: Umfassende Logging und Monitoring
4. **Recovery**: Automatische Wiederherstellung wo möglich

## 🏗️ Architektur

### Frontend Error Handling Stack

```
┌─────────────────────────────────────┐
│           React Components          │
├─────────────────────────────────────┤
│          Error Boundaries           │
├─────────────────────────────────────┤
│         useErrorHandler Hook        │
├─────────────────────────────────────┤
│          Circuit Breaker            │
├─────────────────────────────────────┤
│          Error Logger               │
├─────────────────────────────────────┤
│         API Manager                 │
└─────────────────────────────────────┘
```

### Backend Error Handling Stack

```
┌─────────────────────────────────────┐
│         FastAPI Endpoints           │
├─────────────────────────────────────┤
│      Error Handler Middleware       │
├─────────────────────────────────────┤
│       Validation Middleware         │
├─────────────────────────────────────┤
│          Database Layer             │
├─────────────────────────────────────┤
│           Loguru Logger             │
└─────────────────────────────────────┘
```

## 📋 Error Kategorien

### 1. **Network Errors**
- Verbindungsabbrüche
- Timeouts
- DNS Auflösungsfehler

**Handling:**
```typescript
try {
  const response = await apiCall();
} catch (error) {
  if (error.name === 'NetworkError') {
    showMessage('Verbindungsfehler. Bitte überprüfen Sie Ihre Internetverbindung.');
    // Retry nach Delay
  }
}
```

### 2. **API Errors**
- 4xx Client Errors
- 5xx Server Errors
- Rate Limiting

**Handling:**
```typescript
const apiBreaker = CircuitBreakerFactory.getBreaker('api');

const result = await apiBreaker.execute(
  () => fetch('/api/data'),
  () => getCachedData() // Fallback
);
```

### 3. **Validation Errors**
- Input Validation
- Business Logic Validation
- Schema Validation

**Handling:**
```python
@app.post("/api/workspaces")
async def create_workspace(workspace: WorkspaceCreateValidation):
    try:
        # Validation erfolgt automatisch durch Pydantic
        result = await workspace_service.create(workspace)
        return result
    except ValidationError as e:
        return ValidationResponse(valid=False, errors=e.errors)
```

### 4. **Business Logic Errors**
- Unauthorized Access
- Resource Not Found
- Constraint Violations

**Handling:**
```python
try:
    workspace = db.query(Workspace).filter(id=workspace_id).first()
    if not workspace:
        raise HTTPException(404, "Workspace not found")
except Exception as e:
    logger.error(f"Business logic error: {e}")
    raise
```

## 🛠️ Implementation Patterns

### Frontend Patterns

#### 1. Error Boundary Pattern
```typescript
// Wrap kritische Komponenten
<ErrorBoundary fallback={<ErrorFallback />}>
  <CriticalComponent />
</ErrorBoundary>
```

#### 2. Hook Pattern für API Calls
```typescript
const useApiCall = (endpoint: string) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { handleError } = useErrorHandler();

  const execute = async (params?: any) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await apiManager.request(endpoint, params);
      setData(result);
      
    } catch (err) {
      const message = handleError(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, execute };
};
```

#### 3. Circuit Breaker Pattern
```typescript
const apiBreaker = CircuitBreakerFactory.getBreaker('backend', {
  failureThreshold: 5,
  resetTimeout: 60000,
  onStateChange: (state) => {
    if (state === CircuitState.OPEN) {
      notifyUser('Backend temporarily unavailable');
    }
  }
});
```

### Backend Patterns

#### 1. Structured Exception Handling
```python
class BusinessLogicError(Exception):
    def __init__(self, message: str, code: str, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}

@app.exception_handler(BusinessLogicError)
async def business_logic_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "code": exc.code,
            "details": exc.details
        }
    )
```

#### 2. Database Error Handling
```python
async def create_workspace(workspace_data: dict):
    try:
        async with db.transaction():
            workspace = Workspace(**workspace_data)
            db.add(workspace)
            await db.commit()
            return workspace
    except IntegrityError as e:
        await db.rollback()
        if 'UNIQUE constraint failed' in str(e):
            raise BusinessLogicError(
                "Workspace with this name already exists",
                "DUPLICATE_NAME"
            )
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error: {e}")
        raise
```

## 📊 Monitoring & Observability

### Error Tracking
```typescript
// Frontend
errorLogger.logError(error, {
  component: 'WorkspaceList',
  action: 'create_workspace',
  userId: currentUser.id,
  workspaceData: sensitiveDataRemoved(data)
});
```

```python
# Backend
logger.error(
    "Failed to create workspace",
    extra={
        "user_id": user.id,
        "workspace_data": workspace_data,
        "error_type": type(e).__name__,
        "request_id": request.state.request_id
    }
)
```

### Metrics Collection
```typescript
// Performance Metrics
const startTime = performance.now();
try {
  await apiCall();
  metrics.recordSuccess('api_call', performance.now() - startTime);
} catch (error) {
  metrics.recordError('api_call', error.type);
}
```

## 🔄 Recovery Strategies

### 1. Automatic Retry
```typescript
const retryConfig = {
  attempts: 3,
  delay: 1000,
  backoff: 2,
  retryCondition: (error) => error.status >= 500
};

await retry(apiCall, retryConfig);
```

### 2. Fallback Data
```typescript
try {
  return await fetchLiveData();
} catch (error) {
  logger.warn('Using cached data due to API failure');
  return getCachedData();
}
```

### 3. Graceful Degradation
```typescript
const FeatureComponent = () => {
  if (isServiceUnavailable) {
    return <FeaturePlaceholder message="Feature temporarily unavailable" />;
  }
  
  return <FullFeature />;
};
```

## 🚨 Alerting Strategy

### Critical Errors (Immediate Alert)
- Database connection loss
- Authentication service down
- High error rate (>10 errors/minute)
- Circuit breaker open state

### Warning Level (Monitor)
- Single API endpoint failures
- Slow response times (>5s)
- Validation error spikes

### Info Level (Log Only)
- User input validation errors
- Successful retry attempts
- Circuit breaker state changes

## 🧪 Testing Error Scenarios

### Unit Tests
```typescript
describe('WorkspaceService', () => {
  it('handles network errors gracefully', async () => {
    mockApi.reject(new NetworkError());
    
    const result = await workspaceService.create(data);
    
    expect(result.error).toBe('Verbindungsfehler');
    expect(showNotification).toHaveBeenCalledWith('error');
  });
});
```

### E2E Tests
```typescript
test('shows error message on API failure', async ({ page }) => {
  await page.route('**/api/**', route => route.abort());
  
  await page.click('[data-testid="create-btn"]');
  
  await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
});
```

### Chaos Engineering
```typescript
// Randomly inject failures for resilience testing
if (Math.random() < 0.1 && process.env.NODE_ENV === 'development') {
  throw new Error('Chaos Engineering: Random failure');
}
```

## 📚 Best Practices

### ✅ DO
- Verwende spezifische Error Types
- Logge Errors mit Context
- Zeige benutzerfreundliche Nachrichten
- Implementiere Retry Logic für transiente Fehler
- Teste Error Scenarios
- Überwache Error Rates

### ❌ DON'T
- Ignoriere Errors (silent failures)
- Zeige technische Details an Benutzer
- Logge sensitive Daten
- Verwende generische "Something went wrong" Messages
- Vergesse Loading States
- Blockiere UI bei Fehlern

### User Experience Guidelines

#### Error Messages
```typescript
// ✅ Gut
"Verbindung fehlgeschlagen. Bitte überprüfen Sie Ihre Internetverbindung und versuchen Sie es erneut."

// ❌ Schlecht  
"Error: NetworkError at line 42"
```

#### Loading States
```typescript
// ✅ Zeige Progress
<Button disabled={isLoading}>
  {isLoading ? 'Erstelle Workspace...' : 'Erstellen'}
</Button>

// ❌ Keine Indication
<Button onClick={create}>Erstellen</Button>
```

#### Recovery Actions
```typescript
// ✅ Gib Optionen
<ErrorMessage>
  Fehler beim Laden. 
  <Button onClick={retry}>Erneut versuchen</Button>
  <Button onClick={goBack}>Zurück</Button>
</ErrorMessage>
```

## 🔧 Development Workflow

### 1. **Implementierung**
- Error Handling von Anfang an mitdenken
- Positive und negative Pfade testen
- Error Boundaries um kritische Komponenten

### 2. **Testing** 
- Unit Tests für Error Scenarios
- E2E Tests für Error Flows
- Manual Testing mit Chaos Engineering

### 3. **Monitoring**
- Error Dashboard einrichten
- Alerts konfigurieren
- Performance Monitoring aktivieren

### 4. **Iteration**
- Error Patterns analysieren
- User Feedback einarbeiten
- Recovery Mechanismen verbessern

---

## 📞 Support & Troubleshooting

### Debug Tools
- `window.errorLogger.getErrors()` - Frontend Error History
- `window.apiManager.getMetrics()` - API Call Statistics
- `window.circuitBreaker.getMetrics()` - Circuit Breaker Status

### Log Analysis
```bash
# Backend Error Analysis
grep "ERROR" logs/ordnungshub.log | tail -100

# Frontend Error Export
curl http://localhost:8000/api/logs/frontend-errors
```

### Performance Analysis
```bash
# API Response Times
grep "Request" logs/ordnungshub.log | awk '{print $NF}' | sort -n
```

Diese Guidelines helfen dabei, ein robustes und benutzerfreundliches Error Handling System zu implementieren und zu warten.