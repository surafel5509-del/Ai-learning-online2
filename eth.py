#!/usr/bin/env python3
"""Eth v0.2 - an Amharic-first programming language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import sys


class EthError(Exception):
    """User-facing Eth language error."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: Any
    line: int
    column: int


KEYWORDS = {
    "አሳይ": "PRINT", "ከሆነ": "IF", "ካልሆነ": "ELSE", "ድገም": "REPEAT",
    "ተግባር": "FUNC", "መልስ": "RETURN", "እና": "AND", "ወይም": "OR",
    "እውነት": "TRUE", "ሐሰት": "FALSE",
}


class Lexer:
    """Turn UTF-8 Eth source into tokens, including indentation."""

    def tokenize(self, source: str) -> list[Token]:
        tokens: list[Token] = []
        indent_stack = [0]
        lines = source.splitlines()
        for line_no, raw in enumerate(lines, 1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            spaces = len(raw) - len(raw.lstrip(" "))
            if "\t" in raw[:spaces]:
                raise EthError(f"መስመር {line_no}: tab አይፈቀድም፣ spaces ብቻ ይጠቀሙ")
            if spaces > indent_stack[-1]:
                indent_stack.append(spaces); tokens.append(Token("INDENT", None, line_no, 1))
            elif spaces < indent_stack[-1]:
                while spaces < indent_stack[-1]:
                    indent_stack.pop(); tokens.append(Token("DEDENT", None, line_no, spaces + 1))
                if spaces != indent_stack[-1]:
                    raise EthError(f"መስመር {line_no}: የindentation ስህተት")
            i = spaces
            while i < len(raw):
                c = raw[i]
                if c == " ": i += 1; continue
                if c == "#": break
                col = i + 1
                if c in "\"'":
                    quote = c; i += 1; buf = []
                    while i < len(raw) and raw[i] != quote:
                        if raw[i] == "\\" and i + 1 < len(raw):
                            i += 1; buf.append({"n":"\n","t":"\t","r":"\r","\\":"\\","\"":"\"","'":"'"}.get(raw[i], raw[i]))
                        else: buf.append(raw[i])
                        i += 1
                    if i >= len(raw): raise EthError(f"መስመር {line_no}: የstring መዝጊያ ጥቅስ ጎድሏል")
                    i += 1; tokens.append(Token("STRING", "".join(buf), line_no, col)); continue
                if c.isdigit():
                    j = i
                    while j < len(raw) and (raw[j].isdigit() or raw[j] == "."): j += 1
                    text = raw[i:j]
                    if text.count(".") > 1: raise EthError(f"መስመር {line_no}: የቁጥር አገላለጽ ስህተት")
                    tokens.append(Token("NUMBER", float(text) if "." in text else int(text), line_no, col)); i = j; continue
                if c.isalpha() or c == "_" or "\u1200" <= c <= "\u137f":
                    j = i + 1
                    while j < len(raw) and (raw[j].isalnum() or raw[j] == "_" or "\u1200" <= raw[j] <= "\u137f"): j += 1
                    text = raw[i:j]; tokens.append(Token(KEYWORDS.get(text, "IDENT"), text, line_no, col)); i = j; continue
                two = raw[i:i+2]
                if two in ("==", "!=", "<=", ">=", "//"):
                    tokens.append(Token(two, two, line_no, col)); i += 2; continue
                if c in "+-*/%<>=()[],:": tokens.append(Token(c, c, line_no, col)); i += 1; continue
                raise EthError(f"መስመር {line_no}, አምድ {col}: ያልታወቀ ምልክት '{c}'")
            tokens.append(Token("NEWLINE", None, line_no, len(raw) + 1))
        while len(indent_stack) > 1:
            indent_stack.pop(); tokens.append(Token("DEDENT", None, len(lines) + 1, 1))
        tokens.append(Token("EOF", None, len(lines) + 1, 1)); return tokens


@dataclass
class Program: statements: list[Any]
@dataclass
class PrintStmt: expr: Any
@dataclass
class AssignStmt: name: str; expr: Any
@dataclass
class IfStmt: condition: Any; then_body: list[Any]; else_body: list[Any]
@dataclass
class RepeatStmt: count: Any; body: list[Any]
@dataclass
class FunctionDef: name: str; params: list[str]; body: list[Any]
@dataclass
class ReturnStmt: expr: Any
@dataclass
class ExprStmt: expr: Any
@dataclass
class Literal: value: Any
@dataclass
class Name: value: str
@dataclass
class ListExpr: items: list[Any]
@dataclass
class Binary: left: Any; op: str; right: Any
@dataclass
class Unary: op: str; expr: Any
@dataclass
class Call: callee: Any; args: list[Any]
@dataclass
class Index: target: Any; index: Any


class Parser:
    """Recursive-descent parser producing a small Eth AST."""
    def __init__(self, tokens: list[Token]): self.tokens, self.i = tokens, 0
    def cur(self): return self.tokens[self.i]
    def at(self, kind): return self.cur().kind == kind
    def take(self, kind):
        if not self.at(kind):
            t = self.cur(); raise EthError(f"መስመር {t.line}: '{kind}' ይጠበቃል")
        t = self.cur(); self.i += 1; return t
    def skip_newlines(self):
        while self.at("NEWLINE"): self.i += 1
    def parse(self):
        out=[]; self.skip_newlines()
        while not self.at("EOF"): out.append(self.statement()); self.skip_newlines()
        return Program(out)
    def statement(self):
        if self.at("PRINT"): self.i += 1; return PrintStmt(self.expr())
        if self.at("IF"):
            self.i += 1; c=self.expr(); self.take(":"); self.take("NEWLINE"); a=self.block(); b=[]
            if self.at("ELSE"): self.i += 1; self.take(":"); self.take("NEWLINE"); b=self.block()
            return IfStmt(c,a,b)
        if self.at("REPEAT"):
            self.i += 1; c=self.expr(); self.take(":"); self.take("NEWLINE"); return RepeatStmt(c,self.block())
        if self.at("FUNC"):
            self.i += 1; n=self.take("IDENT").value; self.take("("); p=[]
            if not self.at(")"):
                p.append(self.take("IDENT").value)
                while self.at(","): self.i += 1; p.append(self.take("IDENT").value)
            self.take(")"); self.take(":"); self.take("NEWLINE"); return FunctionDef(n,p,self.block())
        if self.at("RETURN"): self.i += 1; return ReturnStmt(self.expr())
        if self.at("IDENT") and self.tokens[self.i+1].kind == "=":
            n=self.take("IDENT").value; self.take("="); return AssignStmt(n,self.expr())
        return ExprStmt(self.expr())
    def block(self):
        self.take("INDENT"); out=[]; self.skip_newlines()
        while not self.at("DEDENT") and not self.at("EOF"): out.append(self.statement()); self.skip_newlines()
        self.take("DEDENT"); return out
    def expr(self): return self.parse_or()
    def parse_or(self):
        x=self.parse_and()
        while self.at("OR"): self.i += 1; x=Binary(x,"ወይም",self.parse_and())
        return x
    def parse_and(self):
        x=self.parse_compare()
        while self.at("AND"): self.i += 1; x=Binary(x,"እና",self.parse_compare())
        return x
    def parse_compare(self):
        x=self.parse_term()
        while self.cur().kind in {"==","!=","<","<=",">",">="}: op=self.cur().kind; self.i += 1; x=Binary(x,op,self.parse_term())
        return x
    def parse_term(self):
        x=self.parse_factor()
        while self.at("+") or self.at("-"): op=self.cur().kind; self.i += 1; x=Binary(x,op,self.parse_factor())
        return x
    def parse_factor(self):
        x=self.parse_unary()
        while self.cur().kind in {"*","/","//","%"}: op=self.cur().kind; self.i += 1; x=Binary(x,op,self.parse_unary())
        return x
    def parse_unary(self):
        if self.at("-") or self.at("+"): op=self.cur().kind; self.i += 1; return Unary(op,self.parse_unary())
        return self.parse_postfix()
    def parse_postfix(self):
        x=self.primary()
        while True:
            if self.at("("):
                self.i += 1; a=[]
                if not self.at(")"):
                    a.append(self.expr())
                    while self.at(","): self.i += 1; a.append(self.expr())
                self.take(")"); x=Call(x,a)
            elif self.at("["): self.i += 1; j=self.expr(); self.take("]"); x=Index(x,j)
            else: return x
    def primary(self):
        t=self.cur()
        if self.at("NUMBER") or self.at("STRING"): self.i += 1; return Literal(t.value)
        if self.at("TRUE"): self.i += 1; return Literal(True)
        if self.at("FALSE"): self.i += 1; return Literal(False)
        if self.at("IDENT"): self.i += 1; return Name(t.value)
        if self.at("["):
            self.i += 1; a=[]
            if not self.at("]"):
                a.append(self.expr())
                while self.at(","): self.i += 1; a.append(self.expr())
            self.take("]"); return ListExpr(a)
        if self.at("("): self.i += 1; x=self.expr(); self.take(")"); return x
        raise EthError(f"መስመር {t.line}: ያልተጠበቀ ምልክት '{t.value or t.kind}'")


@dataclass
class UserFunction:
    params: list[str]
    body: list[Any]
    closure: dict[str, Any]

class _Return(Exception):
    def __init__(self, value): self.value = value


class Interpreter:
    def __init__(self, input_fn=input, output_fn=print): self.input=input_fn; self.output=output_fn; self.env={}; self.functions={}
    def run(self, source: str): self.exec_block(Parser(Lexer().tokenize(source)).parse().statements, self.env)
    def exec_block(self, statements, env):
        old=self.env; self.env=env
        try:
            for stmt in statements: self.exec_stmt(stmt)
        finally: self.env=old
    def exec_stmt(self, s):
        if isinstance(s,PrintStmt): self.output(self.eval(s.expr))
        elif isinstance(s,AssignStmt): self.env[s.name]=self.eval(s.expr)
        elif isinstance(s,ExprStmt): self.eval(s.expr)
        elif isinstance(s,IfStmt): self.exec_block(s.then_body if self.eval(s.condition) else s.else_body,self.env.copy())
        elif isinstance(s,RepeatStmt):
            n=self.eval(s.count)
            if not isinstance(n,int) or isinstance(n,bool) or n<0: raise EthError("ድገም የሚፈልገው አሉታዊ ያልሆነ integer ነው")
            for _ in range(n): self.exec_block(s.body,self.env.copy())
        elif isinstance(s,FunctionDef): self.functions[s.name]=UserFunction(s.params,s.body,self.env.copy())
        elif isinstance(s,ReturnStmt): raise _Return(self.eval(s.expr))
        else: raise EthError("ያልታወቀ statement")
    def eval(self,n):
        if isinstance(n,Literal): return n.value
        if isinstance(n,Name):
            if n.value in self.env: return self.env[n.value]
            if n.value in self.functions: return self.functions[n.value]
            raise EthError(f"ያልታወቀ ተለዋዋጭ: {n.value}")
        if isinstance(n,ListExpr): return [self.eval(x) for x in n.items]
        if isinstance(n,Index):
            try: return self.eval(n.target)[self.eval(n.index)]
            except (IndexError,KeyError,TypeError) as e: raise EthError("የlist መዳረሻ ስህተት") from e
        if isinstance(n,Unary):
            v=self.eval(n.expr); return -v if n.op=="-" else +v
        if isinstance(n,Binary):
            if n.op=="እና": return self.eval(n.left) and self.eval(n.right)
            if n.op=="ወይም": return self.eval(n.left) or self.eval(n.right)
            a,b=self.eval(n.left),self.eval(n.right); ops={"+":lambda:a+b,"-":lambda:a-b,"*":lambda:a*b,"/":lambda:a/b,"//":lambda:a//b,"%":lambda:a%b,"==":lambda:a==b,"!=":lambda:a!=b,"<":lambda:a<b,"<=":lambda:a<=b,">":lambda:a>b,">=":lambda:a>=b}
            try: return ops[n.op]()
            except KeyError as e: raise EthError(f"ያልታወቀ operator: {n.op}") from e
            except ZeroDivisionError as e: raise EthError("በዜሮ መካፈል አይቻልም") from e
        if isinstance(n,Call):
            args=[self.eval(x) for x in n.args]
            if isinstance(n.callee,Name) and n.callee.value=="ጠይቅ": return self.input(str(args[0]) if args else "")
            fn=self.eval(n.callee)
            if not isinstance(fn,UserFunction): raise EthError("ይህ ተግባር አይደለም")
            if len(args)!=len(fn.params): raise EthError(f"{n.callee.value}: የargument ብዛት አይጣጣምም")
            local=fn.closure.copy(); local.update(zip(fn.params,args))
            try: self.exec_block(fn.body,local)
            except _Return as r: return r.value
            return None
        raise EthError("ያልተደገፈ expression")


EthInterpreter = Interpreter


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    if not argv:
        print("Eth v0.2 — የአማርኛ Programming Language"); print("አጠቃቀም: python eth.py <ፋይል.eth>"); return 0
    try:
        with open(argv[0],encoding="utf-8") as f: Interpreter().run(f.read())
    except (OSError,EthError) as exc:
        print(f"Eth ስህተት: {exc}",file=sys.stderr); return 1
    return 0

if __name__ == "__main__": raise SystemExit(main())
