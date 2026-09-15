#!/usr/bin/env python3
"""Eth - a tiny Amharic-first programming language interpreter."""

from __future__ import annotations

import ast
import operator
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class EthError(Exception):
    """User-facing Eth language error."""


@dataclass
class Env:
    values: dict[str, Any]


class ExpressionEvaluator(ast.NodeVisitor):
    BIN_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    CMP_OPS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    def __init__(self, env: Env, ask):
        self.env = env
        self.ask = ask

    def eval(self, source: str) -> Any:
        try:
            tree = ast.parse(source.strip(), mode="eval")
        except SyntaxError as exc:
            raise EthError(f"የሂሳብ አገላለጽ ስህተት: {source}") from exc
        return self.visit(tree.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (str, int, float, bool)) or node.value is None:
            return node.value
        raise EthError("ያልተፈቀደ የውሂብ አይነት")

    def visit_Name(self, node: ast.Name):
        if node.id in self.env.values:
            return self.env.values[node.id]
        if node.id == "እውነት":
            return True
        if node.id == "ሐሰት":
            return False
        raise EthError(f"ያልታወቀ ተለዋዋጭ: {node.id}")

    def visit_BinOp(self, node: ast.BinOp):
        fn = self.BIN_OPS.get(type(node.op))
        if fn is None:
            raise EthError("ይህ የሂሳብ ምልክት አይደገፍም")
        try:
            return fn(self.visit(node.left), self.visit(node.right))
        except ZeroDivisionError as exc:
            raise EthError("በዜሮ መካፈል አይቻልም") from exc

    def visit_UnaryOp(self, node: ast.UnaryOp):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.Not):
            return not value
        raise EthError("ያልተፈቀደ unary operator")

    def visit_Compare(self, node: ast.Compare):
        left = self.visit(node.left)
        for op_node, comparator in zip(node.ops, node.comparators):
            fn = self.CMP_OPS.get(type(op_node))
            if fn is None:
                raise EthError("ይህ የንጽጽር ምልክት አይደገፍም")
            right = self.visit(comparator)
            if not fn(left, right):
                return False
            left = right
        return True

    def visit_BoolOp(self, node: ast.BoolOp):
        if isinstance(node.op, ast.And):
            result = True
            for value in node.values:
                result = self.visit(value)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            for value in node.values:
                result = self.visit(value)
                if result:
                    return result
            return result
        raise EthError("ያልተፈቀደ boolean operator")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EthError("የተፈቀደ ተግባር ብቻ መጠቀም ይቻላል")
        if node.func.id == "ጠይቅ":
            if len(node.args) > 1 or node.keywords:
                raise EthError("ጠይቅ አንድ መልዕክት ብቻ ይቀበላል")
            prompt = self.visit(node.args[0]) if node.args else ""
            return self.ask(str(prompt))
        raise EthError(f"ያልታወቀ ተግባር: {node.func.id}")

    def generic_visit(self, node):
        raise EthError(f"ያልተደገፈ አገላለጽ: {type(node).__name__}")


class EthInterpreter:
    def __init__(self, input_fn=input, output_fn=print):
        self.env = Env({})
        self.input = input_fn
        self.output = output_fn

    def evaluate(self, expr: str):
        return ExpressionEvaluator(self.env, self.input).eval(expr)

    def run(self, source: str):
        lines = source.splitlines()
        self._run_block(lines, 0, len(lines), 0)

    def _run_block(self, lines, start, end, indent):
        i = start
        while i < end:
            raw = lines[i]
            if not raw.strip() or raw.lstrip().startswith("#"):
                i += 1
                continue
            current_indent = len(raw) - len(raw.lstrip(" "))
            if current_indent < indent:
                return i
            if current_indent != indent:
                raise EthError(f"መስመር {i + 1}: የindentation ስህተት")

            line = raw.strip()
            if line.startswith("አሳይ "):
                self.output(self.evaluate(line[4:].strip()))
                i += 1
                continue

            if line.startswith("ጠይቅ "):
                raise EthError(f"መስመር {i + 1}: ጠይቅ በ assignment ውስጥ ይጠቀሙት። ለምሳሌ: ስም = ጠይቅ(\"ስም?\")")

            if line.startswith("ከሆነ ") and line.endswith(":"):
                condition = line[5:-1].strip()
                block_start = i + 1
                block_end = self._find_block_end(lines, block_start, end, indent)
                next_i = block_end
                else_start = None
                else_end = None
                if block_end < end and lines[block_end].strip() == "ካልሆነ:":
                    else_start = block_end + 1
                    else_end = self._find_block_end(lines, else_start, end, indent)
                    next_i = else_end
                if self.evaluate(condition):
                    self._run_block(lines, block_start, block_end, indent + 4)
                elif else_start is not None:
                    self._run_block(lines, else_start, else_end, indent + 4)
                i = next_i
                continue

            if line.startswith("ድገም ") and line.endswith(":"):
                count = self.evaluate(line[5:-1].strip())
                if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                    raise EthError(f"መስመር {i + 1}: ድገም አዎንታዊ integer ይፈልጋል")
                block_start = i + 1
                block_end = self._find_block_end(lines, block_start, end, indent)
                for _ in range(count):
                    self._run_block(lines, block_start, block_end, indent + 4)
                i = block_end
                continue

            if "=" in line and not any(op in line for op in ("==", ">=", "<=", "!=")):
                name, expr = line.split("=", 1)
                name = name.strip()
                if not name.isidentifier():
                    raise EthError(f"መስመር {i + 1}: የተለዋዋጭ ስም ልክ አይደለም: {name}")
                self.env.values[name] = self.evaluate(expr)
                i += 1
                continue

            raise EthError(f"መስመር {i + 1}: ያልታወቀ ትእዛዝ: {line}")
        return i

    @staticmethod
    def _find_block_end(lines, start, end, parent_indent):
        i = start
        while i < end:
            raw = lines[i]
            if not raw.strip() or raw.lstrip().startswith("#"):
                i += 1
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if indent <= parent_indent:
                return i
            i += 1
        return end


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("Eth v0.1 — የአማርኛ Programming Language")
        print("አጠቃቀም: python eth.py <ፋይል.eth>")
        return 0
    path = Path(argv[0])
    try:
        source = path.read_text(encoding="utf-8")
        EthInterpreter().run(source)
    except (OSError, EthError) as exc:
        print(f"Eth ስህተት: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
