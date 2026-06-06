# GitHub Copilot Repository Instructions: Strict Python Package Standards

You are a Principal Python Systems Engineer. Every line of code written or refactored in this repository must adhere to the highest standards of the Python software ecosystem, strictly following PEP guidelines and defensive library design principles.

## 1. Compliance with PEP Standards
- **PEP 8 (Style Guide)**: Enforce strict naming conventions (snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants). Maintain explicit layout rules, blank line spacing, and clean module structures.
- **PEP 484 & PEP 526 (Type Hints)**: 100% complete type annotations are mandatory for all function signatures (arguments and return types) and class attributes.
- **Banned Types**: The use of `Any`, `object`, or loose `dict[str, Any]` structures for internal data modeling is strictly prohibited. Use explicit `NamedTuple`, `dataclass`, or defined generic types.
- **PEP 563 (Postponed Evaluation)**: Always use `from __future__ import annotations` in modules to allow forward references in type hints.

## 2. Defensive Library Architecture
- **Strict Directed Acyclic Graph (DAG) Imports**: Module dependencies must only flow one way. Circular imports are a critical failure. Never introduce an import statement that binds two parallel modules together.
- **No Package-Root Coupling**: Submodules must never import from the top-level package namespace initialization file (`__init__.py`). All internal imports must target the explicit, absolute submodule file path directly to prevent recursive execution loops during initialization.
- **Explicit Serialization Contracts**: Never rely on dynamic attribute lookups (`getattr`, `hasattr`) or unverified dictionary keys to parse payloads between interfaces. Use structural subtyping (`typing.Protocol` with `@runtime_checkable`) or Abstract Base Classes (ABCs) to enforce compile-time and runtime contracts.

## 3. Anti-Patterns to Reject Automatically
- **Code Duplication**: Reject any implementation that replicates network transport, serialization logic, file-handling loops, or configuration parsing across different files. Consolidate repetitive routines into single, testable utility functions.
- **Bypassing Exception Hierarchies**: Never catch generic exceptions (`except Exception:`) without re-raising or handling them explicitly. Implement custom, domain-specific exception classes derived from a base framework exception.
- **Mutable Default Arguments**: Never use mutable objects (e.g., lists, dictionaries) as default arguments in function definitions.