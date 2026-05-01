# Coding Style

> Code style conventions for this project.
> Extends common coding-style.md with project-specific rules.

## General

- **Immutability**: Create new objects, never mutate existing ones
- **File size**: Prefer 200-400 lines, max 800 lines per file
- **Function size**: Prefer < 50 lines per function
- **Nesting depth**: Max 4 levels
- **No hardcoded values**: Use constants or config
- **No emojis in code**: Emojis may not render correctly in terminals

## Frontend ([Framework])

- Use Composition API / functional style
- Component naming: PascalCase
- File naming: kebab-case
- Props: define with validation
- Events: use explicit emit declarations
- Template: keep logic in script, not template

## Backend ([Language])

- Type hints on all public functions
- Docstrings on complex functions (not obvious ones)
- Error handling at every boundary
- No global mutable state

## CSS / Styling

- Use Tailwind utility classes as primary
- Component-specific styles in scoped `<style>` blocks
- Follow mobile-first responsive design
- Use CSS custom properties for theme colors

## Import Order

1. External packages
2. Internal modules
3. Relative imports
4. Styles (if applicable)
