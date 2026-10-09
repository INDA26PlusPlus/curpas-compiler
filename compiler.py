from expression import ExpressionBuilder, Expression
import typing
import ast
import sys
import math

"""
You'll find this langauge is really weird. It takes a set of instructions on how to build an expression like:
"start with 1, add a minus sign to the left, add a 3 to left of that minus sign, then add a division symbol above the 1 and a 4 above that"
But it does not compile these instructions, rather it compiles into a calculator for whatever expression is built at the end of the script,
which can be run with any value for any n's inserted into the expression during the build time.

The file extension is fnb, for function builder.
"""

variables = {
    "φ": (1 + 5 ** 0.5) / 2,
    "π": math.pi,
    "e": math.e,
    "n": None,
}

builder = ExpressionBuilder(0)

def parse_address(s: str):
    try:
        addr = ast.literal_eval(s)
        if not isinstance(addr, list):
            raise ValueError()
        for x in addr:
            if not isinstance(x, int):
                raise ValueError()
        return addr
    except Exception as e:
        print(e)
        raise ValueError(f'Could not parse address "{s}"')

def parse_term(term: str) -> float:
    try:
        value = float(term)
        return value
    except Exception:
        if term in variables:
            return variables[term]

    match term.split()[0]:
        case "has":
            if parse_term(term[len(term.split()[0])+1:]) in builder.evaluate(variables["n"]):
                return 1
            else:
                return 0

        case "missing":
            if parse_term(term[len(term.split()[0])+1:]) in builder.evaluate(variables["n"]):
                return 0
            else:
                return 1
        
        case _:
            raise ValueError(f'{term} does not have an associated numeric value')


def parse_line(script: list[str], depth: int, i: int) -> None:
    match script[i].split()[0]:
        case "init":
            if len(script[i].split()) != 2:
                raise ValueError(f'init takes 1 argument, got {len(script[i])-1}')
            builder.__init__(script[i].split()[1])
        case "add":
            if len(script[i].split()) != 4:
                raise ValueError(f'add takes 3 arguments, got {len(script[i])-1}')
            address = parse_address(script[i].split()[1])
            dir = script[i].split()[2]
            symbol = script[i].split()[3]

            builder.add(address=address, dir=dir, symbol=symbol)
        case "div":
            if len(script[i].split()) != 4:
                raise ValueError(f'add takes 3 arguments, got {len(script[i])-1}')
            address = parse_address(script[i].split()[1])
            dir = script[i].split()[2]
            symbol = script[i].split()[3]

            builder.divide(address=address, dir=dir, symbol=symbol)
        case "pow":
            if len(script[i].split()) != 3:
                raise ValueError(f'add takes 2 arguments, got {len(script[i])-1}')
            address = parse_address(script[i].split()[1])
            dir = script[i].split()[2]

            builder.exponentiate(address=address, dir=dir)
        case "cut":
            if len(script[i].split()) != 2 and len(script[i].split()) != 3:
                raise ValueError(f'add takes 1 or 2 arguments, got {len(script[i])-1}')
            address = parse_address(script[i].split()[1])
            if len(script[i].split()) == 3:
                dir = script[i].split()[2]
            else:
                dir = ""

            builder.delete(addr=address, dir=dir)
        case "show": # this is solely for debugging compiling
            if len(script[i].split()) != 2:
                raise ValueError(f'show takes 1 argument, got {len(script[i])-1}')
            match script[i].split()[1]:
                case "exp":
                    print(builder)
                case "eval":
                    builder.score(variables["n"])
                case "ast":
                    print(repr(builder))
                case _:
                    raise ValueError(f'unrecognized object for show "{script[i][1]}"')
        
        case "while":
            while parse_term(script[i].strip()[len(script[i].split()[0])+1:]) != 0.0:
                parse_section(script, depth+1, i+1)
        
        case "if":
            if parse_term(script[i].strip()[len(script[i].split()[0])+1:]) != 0.0:
                parse_section(script, depth+1, i+1)

        case _:
            raise ValueError(f'unrecognized keyword for "{script[i]}"')

def parse_section(script: list[str], depth: int, i: int):
    while i < len(script):
        line = script[i]
        if len(line.strip()) == 0:
            i += 1
            continue
        d = 0
        while line[:4] == "    ":
            line = line[4:]
            d += 1
        if d > depth:
            i += 1
            continue
        if d < depth:
            break

        try:
            parse_line(script, depth, i)
        except ValueError as e:
            print(f"Compile error at line {i+1}, {e}")
            exit()
        i += 1

try:
    variables["n"] = float(sys.argv[2])
    script = sys.argv[1]
except Exception as _:
    print("Args parse error, example: python compiler.py script.mms 1")
    exit()

with open(script, 'r') as f:
    parse_section(f.read().splitlines(), 0, 0)


print(repr(builder)) # <- the ast that needs to be turned into machine code