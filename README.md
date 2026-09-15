# Eth 🇪🇹

**Eth** is an Amharic-first programming language prototype. The first version is an interpreter written in Python and uses `.eth` source files.

## What works in v0.1

- `አሳይ` — print values
- variables with `=`
- strings, integers, floats, booleans
- `+ - * / // % **`
- comparisons: `== != < <= > >=`
- `ከሆነ` / `ካልሆነ` — if / else
- `ድገም` — repeat loops
- `ጠይቅ(...)` — user input
- UTF-8 Amharic identifiers and source files
- Amharic error messages for common language errors

## Run Eth

Python 3.10+ is recommended.

```bash
python eth.py examples/hello.eth
```

Expected output:

```text
ሰላም ሱራፌል
30
x ከ y ያነሰ ነው
Eth!
Eth!
Eth!
```

## Write your first Eth program

Create `hello.eth`:

```text
ስም = "ሱራፌል"
ዕድሜ = 20

አሳይ "ሰላም " + ስም

ከሆነ ዕድሜ >= 18:
    አሳይ "አዋቂ ነህ"
ካልሆነ:
    አሳይ "ገና ልጅ ነህ"
```

Then run:

```bash
python eth.py hello.eth
```

## Input

```text
ስም = ጠይቅ("ስምህ ማን ነው? ")
አሳይ "ሰላም " + ስም
```

## Project direction

The interpreter is intentionally small and dependency-free. The next milestones are:

1. functions (`ተግባር` / `መልስ`)
2. lists and dictionaries
3. modules and a standard library
4. a proper lexer/parser and AST instead of the current expression bridge
5. `eth` command-line executable
6. editor syntax highlighting and diagnostics
7. an AI assistant that explains and repairs Eth code
8. a self-hosting/compiler track after the language semantics stabilize

## Development

Tests use `pytest`:

```bash
pytest -q
```

Eth source files are UTF-8 encoded.
