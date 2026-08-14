#!/usr/bin/env python3
"""Number Formatter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        number = args.get("number", 0)
        fmt = args.get("format", "comma")
        if fmt == "comma":
            result = f"{number:,.2f}"
        elif fmt == "currency":
            currency = args.get("currency", "$")
            result = f"{currency}{number:,.2f}"
        elif fmt == "percent":
            result = f"{number * 100:.1f}%"
        elif fmt == "scientific":
            result = f"{number:.6e}"
        elif fmt == "binary":
            result = bin(int(number))
        elif fmt == "hex":
            result = hex(int(number))
        elif fmt == "octal":
            result = oct(int(number))
        elif fmt == "ordinal":
            n = int(number)
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            result = f"{n}{suffix}"
        elif fmt == "roman":
            nums = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
            n = int(number)
            result = ""
            for val, sym in nums:
                while n >= val:
                    result += sym
                    n -= val
        elif fmt == "words":
            ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
            tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
            n = int(number)
            if n == 0: result = "zero"
            elif n < 20: result = ones[n]
            elif n < 100: result = tens[n//10] + ("-" + ones[n%10] if n%10 else "")
            elif n < 1000: result = ones[n//100] + " hundred" + (" " + tens[(n%100)//10] + ("-" + ones[n%10] if n%10 else "") if n%100 else "")
            elif n < 1000000: result = ones[n//1000] + " thousand " + ones[(n%1000)//100] + " hundred" if n%1000 else ones[n//1000] + " thousand"
            else: result = str(number)
        else:
            result = str(number)
        return {"result": result, "original": number, "format": fmt}
