# Performance Guidelines

> Performance targets and optimization guidelines for this project.

## Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Initial load | < 3s | Lighthouse / manual |
| API response | < 500ms | Backend logs |
| UI interaction | < 100ms | User perception |
| Memory usage | < 200MB | Task manager |

## Optimization Principles

1. **Measure first, optimize second**: Don't optimize without data
2. **Lazy load**: Load heavy resources only when needed
3. **Debounce**: Debounce rapid user inputs (300ms default)
4. **Cache wisely**: Cache computed values, avoid unnecessary re-computation
5. **Minimize re-renders**: Use appropriate reactivity patterns

## Common Patterns

### Debouncing User Input

```
[Example: debounce pattern for your framework]
```

### Lazy Loading

```
[Example: lazy loading pattern for your framework]
```

### Virtual Scrolling

```
[Example: virtual scrolling for large lists]
```

## Anti-Patterns (Avoid)

- Synchronous blocking operations in UI thread
- Unbounded list rendering
- Un-debounced API calls on input change
- Re-computing derived values without memoization
