# Eth 🇪🇹

**Eth** is an Amharic-first programming language built to be easy for beginners. Eth source is UTF-8 `.eth` text and the interpreter is written in Python.

## Eth v0.2

The interpreter now has a real language pipeline:

`source → Lexer → Parser → AST → Interpreter`

### Language features

- `አሳይ` — print values
- variables with `=`
- strings, integers, floats and booleans (`እውነት` / `ሐሰት`)
- arithmetic: `+ - * / // %`
- comparisons: `== != < <= > >=`
- boolean operators: `እና` / `ወይም`
- `ከሆነ` / `ካልሆነ` — if / else
- `ድገም` — repeat loops
- `ጠይቅ(...)` — user input
- `ተግባር` / `መልስ` — functions and return values
- lists and indexing: `[10, 20, 30]`, `ቁጥሮች[1]`
- Amharic identifiers and Amharic error messages

## Run Eth

Python 3.10+ is recommended.

```bash
python eth.py examples/hello.eth
```

## Example: functions and lists

```text
ተግባር ደምር(a, b):
    መልስ a + b

ቁጥሮች = [10, 20, 30]
አሳይ ደምር(ቁጥሮች[0], 5)
```

Output:

```text
15
```

## Input

```text
ስም = ጠይቅ("ስምህ ማን ነው? ")
አሳይ "ሰላም " + ስም
```

## Development

Run the tests with:

```bash
pytest -q
```

GitHub Actions also runs the test suite and the example program on pushes and pull requests.

## Roadmap

1. dictionaries and richer list operations
2. modules and a standard library
3. better diagnostics with source locations
4. `eth` executable and interactive REPL
5. editor syntax highlighting and diagnostics
6. AI assistant for explaining and repairing Eth code
7. compiler/self-hosting track after the language semantics stabilize

Eth is intentionally small right now: the goal is to make the language semantics clear before adding a large standard library or compiler.
