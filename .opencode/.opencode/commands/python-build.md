---
description: Fix Python build, type check, and lint errors
agent: python-build-resolver
subtask: true
model: openai/gpt-5.3-codex
---

# Python Build Command

Fix Python build, type check, and lint errors: $ARGUMENTS

## Your Task

1. **Run Python checks**: `python -m py_compile`, `ruff check .`, `mypy .`
2. **Fix errors** one by one
3. **Verify fixes** don't introduce new errors

## Common Python Errors

### Syntax Errors
```
SyntaxError: invalid syntax
```
**Fix**: Check for missing colons, parentheses, indentation

### Import Errors
```
ModuleNotFoundError: No module named 'module'
```
**Fix**: Install missing package or fix import path

### Type Errors (mypy)
```
Argument "x" has incompatible type "str"
```
**Fix**: Add type hints or fix variable types

### Lint Errors (ruff)
```
F401 'module' imported but unused
```
**Fix**: Remove unused import

### Indentation Errors
```
IndentationError: unexpected indent
```
**Fix**: Fix indentation (use 4 spaces)

## Fix Order

1. **Syntax errors** - Fix first
2. **Import errors** - Ensure all imports work
3. **Type errors** - Add correct type hints
4. **Lint warnings** - Clean up code style

## Build Commands

```bash
# Syntax check
python -m py_compile file.py

# Type checking
python -m mypy .

# Linting
python -m ruff check .

# Formatting check
python -m black --check .

# Import check
python -c "import module"

# Run all
python -m py_compile && python -m ruff check . && python -m mypy .
```

## Verification

After fixes:
1. `python -m py_compile` - should pass
2. `python -m ruff check .` - should show 0 errors
3. `python -m mypy .` - should show 0 errors
