# stacktrace-lens

> A CLI tool that parses and pretty-prints Python stack traces with context-aware suggestions and color-coded output.

---

## Installation

```bash
pip install stacktrace-lens
```

Or install from source:

```bash
git clone https://github.com/yourusername/stacktrace-lens.git
cd stacktrace-lens
pip install .
```

---

## Usage

Pipe a traceback directly into `stacktrace-lens`:

```bash
python my_script.py 2>&1 | stlens
```

Or pass a log file containing a traceback:

```bash
stlens --file error.log
```

**Example output:**

```
📍 Traceback (most recent call last):
  ┌─ my_script.py, line 42, in process_data
  │   result = data["key"] / total
  └─ KeyError: 'key'

💡 Suggestion: The key 'key' was not found in the dictionary.
   Consider using dict.get('key') to provide a default value.
```

### Options

| Flag            | Description                          |
|-----------------|--------------------------------------|
| `--file`        | Read traceback from a file           |
| `--no-color`    | Disable color-coded output           |
| `--suggestions` | Show/hide context-aware suggestions  |
| `--json`        | Output parsed traceback as JSON      |

---

## Requirements

- Python 3.8+
- `rich` >= 13.0
- `click` >= 8.0

---

## License

This project is licensed under the [MIT License](LICENSE).