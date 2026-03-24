---
description: Python TDD workflow with pytest and comprehensive tests
agent: tdd-guide
subtask: true
model: openai/gpt-5.3-codex
---

# Python Test Command

Implement using Python TDD methodology: $ARGUMENTS

## Your Task

Apply test-driven development with Python best practices:

1. **Define types** - Type hints and dataclasses
2. **Write comprehensive tests** - pytest with fixtures
3. **Implement minimal code** - Pass the tests
4. **Check coverage** - Target 80%+

## TDD Cycle for Python

### Step 1: Define Types
```python
from dataclasses import dataclass
from typing import Protocol

@dataclass
class Input:
    field: str

@dataclass
class Output:
    result: str

class Calculator(Protocol):
    def calculate(self, input_data: Input) -> Output: ...
```

### Step 2: Write Tests with pytest
```python
import pytest
from module import calculate

class TestCalculate:
    @pytest.mark.parametrize("input_data,expected", [
        (Input(field="test"), Output(result="TEST")),
        (Input(field=""), Output(result="")),
    ])
    def test_calculate(self, input_data, expected):
        result = calculate(input_data)
        assert result == expected

    def test_calculate_raises_on_invalid(self):
        with pytest.raises(ValueError):
            calculate(Input(field=None))
```

### Step 3: Run Tests (RED)
```bash
python -m pytest -v
```

### Step 4: Implement (GREEN)
```python
def calculate(input_data: Input) -> Output:
    if input_data.field is None:
        raise ValueError("field cannot be None")
    return Output(result=input_data.field.upper())
```

### Step 5: Check Coverage
```bash
python -m pytest --cov=module --cov-report=term-missing
```

## Python Testing Commands

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=app --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_module.py

# Run with markers
python -m pytest -m "not slow"

# Run with fixtures
python -m pytest --fixtures
```

## Coverage Requirements

| Code Type | Target |
|-----------|--------|
| Standard code | 80% |
| Business logic | 100% |
| Security functions | 100% |
| Utilities | 90% |
