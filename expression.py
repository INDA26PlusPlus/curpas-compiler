from typing import Self
import json
import math

class Expression():
    """
    Node class for the AST
    """
    _id: int = 0
    def __init__(self, dtype: str, data: str | list[Self] = None, id=None):
        self.dtype = dtype
        self.expressions = []
        self.symbol = None
        if data is not None:
            if isinstance(data, list):
                self.expressions = [e.copy() for e in data]
            else:
                self.symbol = data
        if id is None:
            self.id = Expression._id
            Expression._id += 1
        else:
            self.id = id

        if self.dtype not in ["constant", "symbol", "series", "fraction", "multfraction", "exponent", "parentheses", "empty"]:
            raise ValueError(f'"{self.dtype}" is not a recognized dtype')

    def __getitem__(self, address: list[int]) -> Self:
        exp = self
        for idx in address:
            if exp.dtype == "empty":
                raise ValueError(f"Address {address} not valid for expression {self.as_json()}, index {idx} was applied to empty")
            if idx >= len(exp.expressions) or idx < 0:
                raise ValueError(f"Address {address} not valid for expression {self.as_json()}, index {idx} was applied to expression of length {len(exp.expressions)}")
            exp = exp.expressions[idx]
        return exp

    def __setitem__(self, address: list[int] | None, new_exp: Self):
        if not isinstance(new_exp, Expression):
            raise ValueError(f"Expressions can only contain other expressions, not {type(exp)}")
        if address is None or address == []:
            self.dtype = new_exp.dtype
            self.expressions = new_exp.expressions
            self.symbol = new_exp.symbol
            self.id = new_exp.id
        else:
            exp = self
            for i, idx in enumerate(address):
                if exp.dtype in ["constant", "symbol", "empty"]:
                    raise ValueError(f"Address {address} not valid for expression {self.as_json()}, index {idx} was applied to single term")
                if idx >= len(exp.expressions) or idx < 0:
                    raise ValueError(f"Address {address} not valid for expression {self.as_json()}, index {idx} was applied to expression of length {len(exp.expressions)}")
                if exp.dtype == "parentheses" and idx != 0:
                    raise ValueError(f"Address {address} not valid for expression {self.as_json()}, index {idx} was applied to parentheses")
                if i != len(address) - 1:
                    exp = exp.expressions[idx]
            exp.expressions[address[-1]] = new_exp

    def __str__(self):
        s = self.str_obj()[0]
        single_str = ""
        for l in s:
            single_str += l + "\n"
        return single_str

    def str_obj(self) -> tuple[list[str], int]:
        """
        Turns any expression into a 2d string representation
        Returns the 2d string followed by the top y coordinate (for centering)
        """
        filler = ". "
        match self.dtype:
            case "symbol" | "constant":
                return [self.symbol + " " + ("" if len(self.symbol) % 2 == 1 else " ")], 0

            case "series":
                # Get all component expressions
                strings = []
                ub = 0
                lb = 0
                for e in self.expressions:
                    s, t = e.str_obj()
                    ub = max(ub, t)
                    lb = min(lb, t-len(s))
                    strings.append((s, t))
                string = [""]*(ub-lb)

                # Compile them together
                for j, (s, t) in enumerate(strings):
                    w = int(len(s[0])/2)
                    for i, idx in zip(range(ub-lb), range(ub, lb, -1)):
                        if idx > t or idx <= t-len(s):
                            string[i] += filler * w
                        else:
                            string[i] += s[i-(ub-t)]
                return string, ub

            case "fraction" | "multfraction":
                # Get numerator and denominator
                n_str, nub = self.expressions[0].str_obj()
                d_str, dub = self.expressions[1].str_obj()
                n_width = int(round(len(n_str[0])/2.0))
                d_width = int(round(len(d_str[0])/2.0))
                width = max(n_width, d_width)

                # Compile them together
                string = []
                l_pad = int(math.floor((width - n_width)/2.0))
                r_pad = (width - n_width) - l_pad
                for r in n_str:
                    string.append(filler * l_pad + r + filler * r_pad)
                if self.dtype == "fraction":
                    row = ""
                    for i in range(width):
                        if i == width-1:
                            row += "─ "
                        else:
                            row += "──"
                    string.append(row)
                else:
                    row = ""
                    for i in range(width):
                        if i == width-1:
                            row += "× "
                        else:
                            row += "×─"
                    string.append(row)
                l_pad = int(math.floor((width - d_width)/2.0))
                r_pad = (width - d_width) - l_pad
                for r in d_str:
                    string.append(filler * l_pad + r + filler * r_pad)
                
                return string, len(n_str)
            
            case "exponent":
                # Get base and exponent
                b_str, bub = self.expressions[0].str_obj()
                e_str, eub = self.expressions[1].str_obj()
                b_width = int(round(len(b_str[0])/2.0))
                e_width = int(round(len(e_str[0])/2.0))
                width = max(e_width, (b_width + int(math.floor((e_width - 1)/2.0))))

                # Compile them together
                string = []
                l_pad = max(0, b_width - (int(math.floor((e_width)/2.0)) + 1))
                r_pad = width - (l_pad + e_width)
                for r in e_str:
                    string.append(filler * l_pad + r + filler * r_pad)

                l_pad = max(0, (int(math.floor((e_width)/2.0)) + 1) - b_width)
                r_pad = width - (l_pad + b_width)

                row = ""
                for i in range(width):
                    if i == (l_pad + b_width) - 1:
                        row += "^ "
                    else:
                        row += filler
                string.append(row)

                for r in b_str:
                    string.append(filler * l_pad + r + filler * r_pad)
                
                return string, len(e_str) + bub + 1

            case "parentheses":
                # Get expression
                exp_str, ub = self.expressions[0].str_obj()
                width = int(round(len(exp_str[0])/2.0))

                # Compile them together
                string = []
                for i in range(len(exp_str)):
                    string.append("( ")
                
                for i, r in enumerate(exp_str):
                    string[i] += (r)
                
                for i in range(len(exp_str)):
                    string[i] += ") "
                
                return string, ub
            
            case "empty":
                return ["# "], 0

            case _:
                raise ValueError(f'No str object handling found for expression of dtype "{self.dtype}"')

    def __repr__(self):
        return json.dumps(self.as_json(), indent=2)

    def __copy__(self) -> Self:
        return self.copy()

    def copy(self) -> Self:
        copy = Expression(self.dtype)

        copy.id = self.id
        copy.symbol = self.symbol
        copy.expressions = [e.copy() for e in self.expressions]

        return copy

    def resolve(self) -> None:
        """
        Cleans up remnants of expression building
        """
        if self.dtype not in ["constant", "symbol", "empty"]:
            if self.dtype == "parentheses":
                self[[0]].resolve()
            else:
                for e in self.expressions:
                    e.resolve()
        
        match self.dtype:
            case "series":
                if len(self.expressions) == 1:
                    self[[]] = self[[0]]
                    return self.resolve()
                elif len(self.expressions) == 0:
                    self[[]] = Expression("empty")
                    return
                for i, e in enumerate(self.expressions):
                    if e.dtype == "series":
                        self.expressions = self.expressions[:i] + e.expressions + self.expressions[i+1:]
                        return self.resolve()
                    if e.dtype == "empty":
                        self.expressions.pop(i)
                        return self.resolve()

            case "exponent":
                if self.expressions[0].dtype == "exponent":
                    new_top = Expression("exponent", [self[[0, 1]], self[[1].copy()]])
                    self[[0]] = self[[0, 0]]
                    self[[1]] = new_top
                    return self.resolve()
                if self.expressions[0].dtype == "series":
                    new_exp = self.expressions[0].copy()
                    for i in range(len(new_exp.expressions)-1,-1,-1):
                        if new_exp.expressions[i].dtype != "symbol":
                            old_exp = self.copy()
                            old_exp[[0]] = new_exp.expressions[i]
                            new_exp.expressions[i] = old_exp
                            self[[]] = new_exp
                            break
                    else:
                        raise ValueError(f"Exponent of series with only symbols is not allowed. {self}")
                    return self.resolve()

    def find_highest_order(self) -> int:
        ORDER_OF_OPERATIONS = [["+", "±", "-"], ["*", "c"], ["^"], ["!"], ["√"]]

        def get_order(op: str) -> int:
            for i in range(len(ORDER_OF_OPERATIONS)):
                if op in ORDER_OF_OPERATIONS[i]:
                    return i
            raise ValueError(f"Operator {op} not defined in order of operations")

        highest_order = len(ORDER_OF_OPERATIONS)
        last_exp = "None"
        for e in self.expressions:
            # Coefficient Check
            if last_exp in ["!", "e"] and (e.dtype != "symbol" or e.symbol in ["√"]):
                highest_order = min(highest_order, get_order("c"))

            if e.dtype == "symbol":
                if e.symbol in ["(", ")"]:
                    raise ValueError("Cannot evaluate un-resolved parentheses")
                # Special case for a*-b, which should be product not sum
                if e.symbol in ["±", "-"] and last_exp == "*":
                    highest_order = min(highest_order, get_order("*"))
                else:
                    highest_order = min(highest_order, get_order(e.symbol))
                last_exp = e.symbol
            else:
                if e.dtype == "exponent":
                    highest_order = min(highest_order, get_order("^"))
                last_exp = "e"
        
        return highest_order

    def evaluate(self, n = None) -> set[float]:
        """
        Calculate the possible values of the entire expression
        """

        def validate_series(exp: Expression) -> None:
            valid_series_start = ["±", "-", "√", "e"]
            valid_series_end = ["!", "e"]
            def valid_series_pair(l, r):
                """
                Rules for valid pairing of symbols in a series
                """
                if l[0] in ["(", ")"] or r[0] in ["(", ")"]: # Unresolved parentheses are not allowed at all
                    return False
                if l[0] in ["+", "±", "-", "*"] and r[0] in ["e", "√"]:
                    return True
                if l[0] in ["e", "!"] and r[0] in ["+", "±", "-", "*"]:
                    return True
                if l[0] == "*" and r[0] in ["±", "-"]:
                    return True
                if l[0] == "√" and r[0] == "e":
                    return True
                if l[0] == "e" and r[0] == "!":
                    return True
                if l in ["e-parentheses", "e-fraction", "e-multfraction"] and r[0] in ["e", "√"]:
                    return True
                if l[0] in ["e", "!"] and r in ["e-parentheses", "e-fraction", "e-multfraction", "√"]:
                    return True
                return False

            # Check first expression
            last_exp = self.expressions[0]
            l = "e"
            if last_exp.dtype == "symbol":
                l = last_exp.symbol
            if l not in valid_series_start:
                raise ValueError(f'Symbol "{last_exp.symbol}" may not start series: {self}')

            # Check all expression pairs
            for e in self.expressions[1:]:
                r = "e-" + e.dtype
                if e.dtype == "symbol":
                    r = e.symbol
                l = "e-" + last_exp.dtype
                if last_exp.dtype == "symbol":
                    l = last_exp.symbol
                if not valid_series_pair(l, r):
                    raise ValueError(f'Parts:\n{last_exp}\nand\n{e}\nMay not form a pair in series')
                last_exp = e
            
            # Check last expression
            e = self.expressions[-1]
            r = "e"
            if e.dtype == "symbol":
                r = e.symbol
            if r not in valid_series_end:
                raise ValueError(f'Symbol "{last_exp.symbol}" may not end series: {self}')

        match self.dtype:
            case "constant":
                if self.symbol == "n":
                    if n is None:
                        raise ValueError("Cannot parse expression with n without passing n")
                    answers = {float(n)}
                else:
                    match self.symbol:
                        case "φ":
                            answers = {(1 + 5 ** 0.5) / 2}
                        case "π":
                            answers = {math.pi}
                        case "e":
                            answers = {math.e}
                        case _:
                            try:
                                answers = {float(self.symbol)}
                            except Exception:
                                raise ValueError(f"No recognized constant for symbol '{self.symbol}'")
                self.expressions = []

            case "series":
                validate_series(self)

                highest_order = self.find_highest_order()
                # Now evaluate the series depending on what the highest order is
                blank = Expression("series", [])
                match highest_order:

                    # Sum series
                    case 0:
                        groups: list[set[float]] = []
                        operators: list = []
                        sub_series = blank.copy()
                        for i, e in enumerate(self.expressions):
                            if e.dtype == "symbol" and e.symbol in ["+", "±", "-"]:
                                # Special case for a*-b, which should be product not sum
                                if i != 0 and e.symbol in ["±", "-"] and self.expressions[i-1].dtype == "symbol" and self.expressions[i-1].symbol == "*":
                                    sub_series.expressions.append(e)
                                    continue

                                operators.append(e.symbol)
                                if len(sub_series.expressions) == 0:
                                    groups.append({0})
                                else:
                                    sub_series.resolve()
                                    groups.append(sub_series.evaluate(n))
                                sub_series = blank.copy()
                            else:
                                sub_series.expressions.append(e)
                        sub_series.resolve()
                        groups.append(sub_series.evaluate(n))
                        self.resolve()
                        
                        # Sum components
                        answers = groups[0]
                        for i in range(1, len(groups)):
                            new_answers = set([])
                            for a in answers:
                                for b in groups[i]:
                                    match operators[i-1]:
                                        case "+":
                                            new_answers.add(a+b)
                                        case "-":
                                            new_answers.add(a-b)
                                        case "±":
                                            new_answers.add(a+b)
                                            new_answers.add(a-b)
                            answers = new_answers

                    # Product series
                    case 1:
                        groups: list[set[float]] = []
                        sub_series = blank.copy()
                        last_exp = "None"
                        for i, e in enumerate(self.expressions):
                            if (e.dtype == "symbol" and e.symbol == "*") or (last_exp in ["!", "e"] and (e.dtype != "symbol" or e.symbol in ["√"])):
                                sub_series.resolve()
                                groups.append(sub_series.evaluate(n))
                                sub_series = blank.copy()
                                if (last_exp in ["!", "e"] and (e.dtype != "symbol" or e.symbol in ["√"])):
                                    sub_series.expressions.append(e)
                            else:
                                sub_series.expressions.append(e)
                            if e.dtype == "symbol":
                                last_exp = e.symbol
                            else:
                                last_exp = "e"
                        sub_series.resolve()
                        groups.append(sub_series.evaluate(n))
                        self.resolve()
                        
                        # Sum components
                        answers = groups[0]
                        for i in range(1, len(groups)):
                            new_answers = set([])
                            for a in answers:
                                for b in groups[i]:
                                    new_answers.add(a*b)
                            answers = new_answers

                    # Exponent
                    case 2:
                        power = None
                        sub_series = blank.copy()
                        for e in self.expressions:
                            if e.dtype == "exponent":
                                power = e.expressions[1]
                                sub_series.expressions.append(e.expressions[0])
                            else:
                                sub_series.expressions.append(e)
                        # This funky section temprarily groups all the relavent objects together to evaluate/destroy them, then unpacks them again with resolve
                        self[[]] = Expression("exponent", [sub_series, power])
                        answers = self.evaluate(n)
                        self.resolve()

                    # Factorial
                    case 3:
                        sub_series = blank.copy()
                        answers = set([])
                        sub_series.expressions = self.expressions[:-1]
                        sub_series.resolve()
                        group = sub_series.evaluate(n)
                        for a in group:
                            if a.real < 0 and a.real == round(a.real):
                                raise ValueError("Expression includes undefined gamma value", True)
                            elif a.imag != 0:
                                raise ValueError("Factorial is defined for complex numbers, but I'm not sure if we want it to be", True)
                            else:
                                answers.add(math.gamma(a + 1))

                    # Sqrt
                    case 4:
                        sub_series = blank.copy()
                        answers = set([])
                        sub_series.expressions = self.expressions[1:]
                        sub_series.resolve()
                        group = sub_series.evaluate(n)
                        for a in group:
                            answers.add(a ** 0.5)

                    # Single expression
                    case _:
                        answers = self.expressions[0].evaluate(n)

            case "fraction" | "multfraction":
                numers = self.expressions[0].evaluate(n)
                denoms = self.expressions[1].evaluate(n)
                answers = set([])
                for n in numers:
                    for d in denoms:
                        if d == 0:
                            raise ValueError(f"Expression includes undefined fraction {n}/{d}", True)
                        answers.add(float(n)/d)
                        if self.dtype == "multfraction":
                            answers.add(n*d)
            
            case "exponent":
                bases = self.expressions[0].evaluate(n)
                exponents = self.expressions[1].evaluate(n)

                answers = set([])
                for b in bases:
                    for e in exponents:
                        if (b == 0 and e < 0):
                            raise ValueError(f"Expression includes undefined exponent {b}^{e}", True)
                        answers.add(b ** e)

            case "parentheses":
                answers = self.expressions[0].evaluate(n)

            case "empty":
                raise ValueError("Cannot evaluate an expression containing empty expressions")

            case _:
                raise ValueError(f'No evaluation handling found for expression of dtype "{self.dtype}"')

        return answers

    def as_json(self) -> dict:
        def validate_series(exp: Expression) -> None:
            valid_series_start = ["±", "-", "√", "e"]
            valid_series_end = ["!", "e"]
            def valid_series_pair(l, r):
                """
                Rules for valid pairing of symbols in a series
                """
                if l[0] in ["(", ")"] or r[0] in ["(", ")"]: # Unresolved parentheses are not allowed at all
                    return False
                if l[0] in ["+", "±", "-", "*"] and r[0] in ["e", "√"]:
                    return True
                if l[0] in ["e", "!"] and r[0] in ["+", "±", "-", "*"]:
                    return True
                if l[0] == "*" and r[0] in ["±", "-"]:
                    return True
                if l[0] == "√" and r[0] == "e":
                    return True
                if l[0] == "e" and r[0] == "!":
                    return True
                if l in ["e-parentheses", "e-fraction", "e-multfraction"] and r[0] in ["e", "√"]:
                    return True
                if l[0] in ["e", "!"] and r in ["e-parentheses", "e-fraction", "e-multfraction", "√"]:
                    return True
                return False

            # Check first expression
            last_exp = self.expressions[0]
            l = "e"
            if last_exp.dtype == "symbol":
                l = last_exp.symbol
            if l not in valid_series_start:
                raise ValueError(f'Symbol "{last_exp.symbol}" may not start series: {self}')

            # Check all expression pairs
            for e in self.expressions[1:]:
                r = "e-" + e.dtype
                if e.dtype == "symbol":
                    r = e.symbol
                l = "e-" + last_exp.dtype
                if last_exp.dtype == "symbol":
                    l = last_exp.symbol
                if not valid_series_pair(l, r):
                    raise ValueError(f'Parts:\n{last_exp}\nand\n{e}\nMay not form a pair in series')
                last_exp = e
            
            # Check last expression
            e = self.expressions[-1]
            r = "e"
            if e.dtype == "symbol":
                r = e.symbol
            if r not in valid_series_end:
                raise ValueError(f'Symbol "{last_exp.symbol}" may not end series: {self}')

        match self.dtype:
            case "constant":
                if self.symbol == "n":
                    json = {"type": "n"}
                else:
                    match self.symbol:
                        case "φ":
                            json = {"type": "constant", "value": (1 + 5 ** 0.5) / 2}
                        case "π":
                            json = {"type": "constant", "value": math.pi}
                        case "e":
                            json = {"type": "constant", "value": math.e}
                        case _:
                            try:
                                json = {"type": "constant", "value": float(self.symbol)}
                            except Exception:
                                raise ValueError(f"No recognized constant for symbol '{self.symbol}'")
                self.expressions = []

            case "series":
                validate_series(self)

                highest_order = self.find_highest_order()
                # Now evaluate the series depending on what the highest order is
                blank = Expression("series", [])
                match highest_order:

                    # Sum series
                    case 0:
                        groups: list[set[float]] = []
                        operators: list = []
                        sub_series = blank.copy()
                        for i, e in enumerate(self.expressions):
                            if e.dtype == "symbol" and e.symbol in ["+", "±", "-"]:
                                # Special case for a*-b, which should be product not sum
                                if i != 0 and e.symbol in ["±", "-"] and self.expressions[i-1].dtype == "symbol" and self.expressions[i-1].symbol == "*":
                                    sub_series.expressions.append(e)
                                    continue

                                operators.append(e.symbol)
                                if len(sub_series.expressions) == 0:
                                    groups.append({0})
                                else:
                                    sub_series.resolve()
                                    groups.append(sub_series.as_json())
                                sub_series = blank.copy()
                            else:
                                sub_series.expressions.append(e)
                        sub_series.resolve()
                        groups.append(sub_series.as_json())
                        self.resolve()
                        
                        # Sum components
                        json = groups[0]
                        for i in range(1, len(groups)):
                            match operators[i-1]:
                                case "+":
                                    json = {"type": "add", "a": json, "b": groups[i]}
                                case "-":
                                    json = {"type": "sub", "a": json, "b": groups[i]}
                                case "±":
                                    json = {"type": "addsub", "a": json, "b": groups[i]}

                    # Product series
                    case 1:
                        groups: list[set[float]] = []
                        sub_series = blank.copy()
                        last_exp = "None"
                        for i, e in enumerate(self.expressions):
                            if (e.dtype == "symbol" and e.symbol == "*") or (last_exp in ["!", "e"] and (e.dtype != "symbol" or e.symbol in ["√"])):
                                sub_series.resolve()
                                groups.append(sub_series.as_json())
                                sub_series = blank.copy()
                                if (last_exp in ["!", "e"] and (e.dtype != "symbol" or e.symbol in ["√"])):
                                    sub_series.expressions.append(e)
                            else:
                                sub_series.expressions.append(e)
                            if e.dtype == "symbol":
                                last_exp = e.symbol
                            else:
                                last_exp = "e"
                        sub_series.resolve()
                        groups.append(sub_series.as_json())
                        self.resolve()
                        
                        # Sum components
                        json = groups[0]
                        for i in range(1, len(groups)):
                            json = {"type": "mult", "a": json, "b": groups[i]}

                    # Exponent
                    case 2:
                        power = None
                        sub_series = blank.copy()
                        for e in self.expressions:
                            if e.dtype == "exponent":
                                power = e.expressions[1]
                                sub_series.expressions.append(e.expressions[0])
                            else:
                                sub_series.expressions.append(e)
                        # This funky section temprarily groups all the relavent objects together to evaluate/destroy them, then unpacks them again with resolve
                        self[[]] = Expression("exponent", [sub_series, power])
                        json = self.as_json()
                        self.resolve()

                    # Factorial
                    case 3:
                        raise ValueError("Factorials aren't real what are you talking about")

                    # Sqrt
                    case 4:
                        sub_series = blank.copy()
                        sub_series.expressions = self.expressions[1:]
                        sub_series.resolve()
                        json = sub_series.as_json()
                        json = {"type": "pow", "a": json, "b": 0.5}

                    # Single expression
                    case _:
                        json = self.expressions[0].as_json()

            case "fraction" | "multfraction":
                numer = self.expressions[0].as_json()
                denom = self.expressions[1].as_json()
                if self.dtype == "fraction":
                    json = {"type": "div", "a": numer, "b": denom}
                else:
                    json = {"type": "multdiv", "a": numer, "b": denom}
            
            case "exponent":
                base = self.expressions[0].as_json()
                exponent = self.expressions[1].as_json()

                json = {"type": "pow", "a": base, "b": exponent}

            case "parentheses":
                json = self.expressions[0].as_json()

            case "empty":
                raise ValueError("Cannot evaluate an expression containing empty expressions")

            case _:
                raise ValueError(f'No evaluation handling found for expression of dtype "{self.dtype}"')

        return json



def unbind(exp: Expression):
    if exp.dtype not in ["constant", "symbol", "empty"]:
        for e in exp.expressions:
            unbind(e)

    if exp.dtype == "parentheses":
        new_exp = Expression("series", [])
        new_exp.expressions.append(Expression("symbol", data="(", id=exp.id))
        new_exp.expressions.append(exp[[0]])
        new_exp.expressions.append(Expression("symbol", data=")", id=exp[[1]].id))
        exp[[]] = new_exp
    exp.resolve()

class ExpressionBuilder():
    def __init__(self, symbol: str):
        self.parentheses_mode = False
        self.root_expression = Expression("constant", data=symbol)

    def __str__(self):
        return str(self.root_expression)

    def __repr__(self):
        return repr(self.root_expression)

    def evaluate(self, n = None):
        """
        Returns the possible evaluations of an expression.
        Passing True destructivly modifies the expression during overflows, and cannot be undone.
        """
        scores: list[float] = list(self.root_expression.evaluate(n))

        return scores

    def score(self, n = None):
        s = self.evaluate(n)
        if len(s) == 1:
            print(f"Eval: {s[0]}")
        elif len(s) == 0:
            print(f"Eval: None")
        else:
            print(f"Evals: {s}")

    def delete(self, addr: list[int], dir: str = "") -> None:
        exp: Expression = self.root_expression[addr].copy()
        address = addr.copy()
        if self.parentheses_mode and exp.dtype != "parentheses" and (exp.dtype != "symbol" or exp.symbol not in ["(", ")"]):
            raise ValueError("Finish placing parentheses first")
        else:
            action = None
            match exp.dtype:
                case "symbol" | "constant":
                    if exp.symbol in ["(", ")"]:
                        exp[[]] = Expression("empty")
                        self.root_expression[addr] = exp
                        self.parentheses_mode = not self.calc_parentheses()
                        exp = self.root_expression
                        address = []
                    else:
                        exp[[]] = Expression("empty")
                case "fraction" | "multfraction" | "exponent":
                    if exp[[0]].dtype == "empty":
                        exp[[]] = exp[[1]]
                    elif exp[[1]].dtype == "empty":
                        exp[[]] = exp[[0]]
                    else:
                        raise ValueError(f"Cannot remove operator from a complete {exp.dtype}")
                case "parentheses":
                    if dir not in ["l", "r"]:
                        raise ValueError(f"Must pass an l/r direction when removing paired parentheses")
                    parent_dtype = "none"
                    if len(address) > 0:
                        parent_dtype = self.root_expression[address[:-1]].dtype
                    if parent_dtype == "series":
                        if dir == "r":
                            address[-1] += (len(exp[[0]].expressions) + 1)         
                    else:
                        if dir == "r":
                            address.append(len(exp[[0]].expressions) + 1)
                        else:
                            address.append([0])

                    unbind(exp)
                    exp[address] = Expression("empty")
                    self.root_expression[[]] = exp
                    self.parentheses_mode = not self.calc_parentheses()
                    exp = self.root_expression
                    address = []
                case _:
                    raise ValueError(f'Cannot remove single token from expression of type "{exp.dtype}"')

        self.update_tree(address, exp)

    def update_tree(self, address, exp) -> None:
        new_root = self.root_expression.copy()
        new_root[address] = exp.copy()
        new_root.resolve()
        self.root_expression = new_root

    def add(self, address: list[int], dir: str, symbol: str) -> None:
        exp: Expression = self.root_expression[address].copy()
        address = address.copy()

        if self.parentheses_mode and symbol not in ["(", ")"]:
            raise ValueError("Finish placing parentheses first")

        is_constant = symbol in ["φ", "π", "e", "n"]
        try:
            float(symbol)
            is_constant = True
        except Exception:
            pass
            
        if is_constant:
            new_exp = Expression("constant", data=symbol)
        else:
            new_exp = Expression("symbol", data=symbol)

        # Find parent dtype
        parent = None
        if len(address) > 0:
            parent = self.root_expression[address[:-1]].copy()

        if parent is not None and parent.dtype == "exponent" and address[-1] == 0:
            address.pop()
            parent = None
            if len(address) > 0:
                parent = self.root_expression[address[:-1]].copy()

        if parent is not None and parent.dtype == "series":
            new_series = parent
            new_series.expressions.insert(address.pop() + (0 if dir == "l" else 1), new_exp)
        else:
            match dir:
                case "l":
                    new_series = Expression("series", [new_exp, exp])
                case "r":
                    new_series = Expression("series", [exp, new_exp])
                case _:
                    raise ValueError(f"Direction {dir} is not applicable for add")
        self.update_tree(address, new_series)
        if symbol in ["(", ")"]:
            unbind(self.root_expression)
            self.parentheses_mode = not self.calc_parentheses()

    def divide(self, address: list[int], dir: str, symbol: str) -> None:
        exp: Expression = self.root_expression[address].copy()
        address = address.copy()

        if self.parentheses_mode:
            raise ValueError("Finish placing parentheses first")

        if exp.dtype == "series":
            raise ValueError(f'Cannot apply fraction directly to an entire series')
        
        # Find parent dtype
        parent_dtype = "none"
        if len(address) > 0:
            parent_dtype = self.root_expression[address[:-1]].dtype

        # Build new expression
        if parent_dtype in ["fraction","multfraction"]:
            raise ValueError(f'Cannot apply fraction within fraction directly due to ambiguous order of operations')
        else:
            new_fraction = "fraction" if symbol == "/" else "multfraction"
            match dir:
                case "u":
                    exp = Expression(new_fraction, data=[Expression("empty"), exp])
                case "d":
                    exp = Expression(new_fraction, data=[exp, Expression("empty")])
                case _:
                    raise ValueError(f"Direction {dir} is not applicable for div")

        self.update_tree(address, exp)

    def exponentiate(self, address: list[int], dir: str) -> None:
        exp: Expression = self.root_expression[address].copy()
        address = address.copy()
        
        if self.parentheses_mode:
            raise ValueError("Finish placing parentheses first")

        # Find parent dtype
        parent_dtype = "none"
        if len(address) > 0:
            parent_dtype = self.root_expression[address[:-1]].dtype

        # Build new expression
        if exp.dtype not in ["constant", "parentheses", "exponent"]:
            raise ValueError(f'Cannot exponentiate expression of type "{exp.dtype}"')
        match dir:
            case "d":
                exp = Expression("exponent", data=[Expression("empty"), exp])
            case "u":
                exp = Expression("exponent", data=[exp, Expression("empty")])
            case _:
                raise ValueError(f"Direction {dir} is not applicable for pow")

        self.update_tree(address, exp)

    def calc_parentheses(self) -> bool:
        """
        Compute all the parentheses
        Returns whether or not the parentheses were all accounted for
        """
        exp: Expression = self.root_expression.copy()

        def mk(exp: Expression) -> None:
            if exp.dtype not in ["constant", "symbol", "empty", "parentheses"]:
                for e in exp.expressions:
                    mk(e)

            if exp.dtype == "series":
                start = -1
                for i, e in enumerate(exp.expressions):
                    if e.dtype == "symbol" and e.symbol == "(":
                        start = i
                    elif e.dtype == "symbol" and e.symbol == ")":
                        if start == -1:
                            raise ValueError("Invalid configuration of parentheses")
                        exp.expressions[start:i+1] = [Expression("parentheses", [Expression("series", exp.expressions[start+1:i]), Expression("symbol", data=")")])]
                        return mk(exp)
                if start != -1:
                    raise ValueError("Invalid configuration of parentheses")

        try:
            mk(exp)
            self.update_tree([], exp)
        except ValueError:
            return False
        return True