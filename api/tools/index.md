# Built-in Tools

Built-in tools are ready-to-use `@tool` callables that run in-process with the agent. They are the fastest path to a practical assistant because they require no MCP server setup for local use.

Use these when one script owns the full workflow. Move to MCP servers when tools must be shared across processes.

## Filesystem

Filesystem tools provide safe read/write/list/info operations constrained by the tool's sandbox rules. Use them for local project analysis, file inspection, and controlled write workflows.

### llm_framework.tools.filesystem

#### read_file

```python
read_file(path: str, encoding: str = 'utf-8') -> str
```

Read a text file and return its contents.

Parameters:

| Name       | Type  | Description                    | Default    |
| ---------- | ----- | ------------------------------ | ---------- |
| `path`     | `str` | Path to the file to read.      | *required* |
| `encoding` | `str` | Text encoding (default utf-8). | `'utf-8'`  |

#### write_file

```python
write_file(path: str, content: str, encoding: str = 'utf-8') -> str
```

Write text to a file, creating parent directories if needed.

Parameters:

| Name       | Type  | Description                    | Default    |
| ---------- | ----- | ------------------------------ | ---------- |
| `path`     | `str` | Destination file path.         | *required* |
| `content`  | `str` | Text to write.                 | *required* |
| `encoding` | `str` | Text encoding (default utf-8). | `'utf-8'`  |

#### list_directory

```python
list_directory(path: str) -> list
```

List the contents of a directory.

Parameters:

| Name   | Type  | Description                    | Default    |
| ------ | ----- | ------------------------------ | ---------- |
| `path` | `str` | Path to the directory to list. | *required* |

#### file_info

```python
file_info(path: str) -> dict
```

Return metadata about a file or directory.

Parameters:

| Name   | Type  | Description                    | Default    |
| ------ | ----- | ------------------------------ | ---------- |
| `path` | `str` | Path to the file or directory. | *required* |

______________________________________________________________________

## Shell

Shell tools provide controlled command execution with an allowlist-oriented safety model. Use this when the agent needs CLI capabilities while keeping execution boundaries explicit.

### llm_framework.tools.shell

#### run_command

```python
run_command(command: str, args: list[str] | None = None, cwd: str | None = None, timeout: float = 30.0) -> str
```

Run an allowlisted shell command and return its combined stdout and stderr.

Parameters:

| Name      | Type        | Description                                                                                       | Default                                                               |
| --------- | ----------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `command` | `str`       | The command to run. Must be in the allowed list (cat, echo, find, grep, head, ls, pwd, tail, wc). | *required*                                                            |
| `args`    | \`list[str] | None\`                                                                                            | Optional list of arguments to pass to the command.                    |
| `cwd`     | \`str       | None\`                                                                                            | Working directory for the command; must be within the home directory. |
| `timeout` | `float`     | Maximum seconds to wait before killing the process (default 30).                                  | `30.0`                                                                |

______________________________________________________________________

## Web Fetch

Web fetch tools retrieve page content and convert it into model-friendly plain text. Use them for lightweight retrieval without a full browser automation stack.

### llm_framework.tools.web_fetch

#### fetch_url

```python
fetch_url(url: str, as_text: bool = True) -> str
```

Fetch a URL and return its content as text.

Parameters:

| Name      | Type   | Description                                   | Default    |
| --------- | ------ | --------------------------------------------- | ---------- |
| `url`     | `str`  | The URL to fetch (http/https only).           | *required* |
| `as_text` | `bool` | If True, strip HTML tags from HTML responses. | `True`     |

______________________________________________________________________

## Calculator

Calculator tools provide deterministic arithmetic and avoid model math drift. Use them whenever numeric correctness matters more than freeform reasoning.

### llm_framework.tools.calculator

#### add_numbers

```python
add_numbers(a: float, b: float) -> float
```

Adds two numbers.

Parameters:

| Name | Type    | Description     | Default    |
| ---- | ------- | --------------- | ---------- |
| `a`  | `float` | First operand.  | *required* |
| `b`  | `float` | Second operand. | *required* |

#### multiply_numbers

```python
multiply_numbers(a: float, b: float) -> float
```

Multiplies two numbers.

Parameters:

| Name | Type    | Description     | Default    |
| ---- | ------- | --------------- | ---------- |
| `a`  | `float` | First operand.  | *required* |
| `b`  | `float` | Second operand. | *required* |

#### subtract_numbers

```python
subtract_numbers(a: float, b: float) -> float
```

Subtracts the second number from the first.

Parameters:

| Name | Type    | Description     | Default    |
| ---- | ------- | --------------- | ---------- |
| `a`  | `float` | The minuend.    | *required* |
| `b`  | `float` | The subtrahend. | *required* |

#### divide_numbers

```python
divide_numbers(a: float, b: float) -> float
```

Divides the first number by the second. Raises an error if divisor is zero.

Parameters:

| Name | Type    | Description                    | Default    |
| ---- | ------- | ------------------------------ | ---------- |
| `a`  | `float` | The dividend.                  | *required* |
| `b`  | `float` | The divisor; must not be zero. | *required* |

______________________________________________________________________

## Clock

Clock tools provide current UTC date/time information for time-aware responses. Use them for timestamping, scheduling prompts, and time-window calculations.

### llm_framework.tools.clock

#### get_current_datetime

```python
get_current_datetime() -> str
```

Return the current UTC date and time in ISO 8601 format.

______________________________________________________________________

## Memory

Memory tool helpers expose a `MemoryStore` instance as agent-callable save/recall/list/delete operations. Use this when you want memory capabilities without running a separate memory MCP server.

### llm_framework.tools.memory

#### make_memory_tools

```python
make_memory_tools(store: MemoryStore) -> list
```

Create @tool functions bound to a MemoryStore instance; no global state.
