"""
EvolvixOS — Package Wrapper Skill
Introspects any Python/pip package public API using inspect module.
Lists available functions/classes, fetches help/docstrings, and executes specific functions.
"""

import sys
import json
import inspect
import importlib
import subprocess
from typing import Optional, Any, Dict, List


def safe_serialize(val: Any) -> Any:
    """Recursively convert object to JSON serializable structures."""
    if val is None or isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, (list, tuple, set)):
        return [safe_serialize(x) for x in val]
    if isinstance(val, dict):
        return {str(k): safe_serialize(v) for k, v in val.items()}
    if hasattr(val, "to_dict"):
        try:
            return val.to_dict()
        except Exception:
            pass
    if hasattr(val, "tolist"):
        try:
            return val.tolist()
        except Exception:
            pass
    return str(val)


class Skill:
    """Package Wrapper — Introspect and interact with any pip package."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    def auto_install(self, package_name: str) -> bool:
        """Attempt to pip install package if missing."""
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", package_name],
                capture_output=True, text=True, timeout=120
            )
            return res.returncode == 0
        except Exception:
            return False

    def import_package(self, package_name: str, auto_install: bool = True):
        try:
            return importlib.import_module(package_name)
        except ImportError:
            if auto_install:
                if self.auto_install(package_name):
                    importlib.invalidate_caches()
                    return importlib.import_module(package_name)
            raise

    def introspect(self, mod) -> dict:
        """List public functions, classes, variables, and docstring of a module."""
        doc = inspect.getdoc(mod) or ""
        functions = []
        classes = []
        variables = []

        for name, member in inspect.getmembers(mod):
            if name.startswith("_"):
                continue
            if inspect.isfunction(member) or inspect.isbuiltin(member):
                try:
                    sig = str(inspect.signature(member))
                except Exception:
                    sig = "(...)"
                fn_doc = (inspect.getdoc(member) or "").split("\n")[0]
                functions.append({"name": name, "signature": f"{name}{sig}", "doc": fn_doc})
            elif inspect.isclass(member):
                cls_doc = (inspect.getdoc(member) or "").split("\n")[0]
                classes.append({"name": name, "doc": cls_doc})
            else:
                variables.append(name)

        return {
            "module": mod.__name__,
            "doc": doc,
            "version": getattr(mod, "__version__", "unknown"),
            "functions_count": len(functions),
            "classes_count": len(classes),
            "functions": functions[:50],
            "classes": classes[:30],
            "variables": variables[:30]
        }

    def get_help(self, mod, func_name: str) -> dict:
        """Fetch full docstring, signature, and parameter details for a function/class."""
        target = mod
        for part in func_name.split("."):
            if hasattr(target, part):
                target = getattr(target, part)
            else:
                return {"success": False, "error": f"Member '{part}' not found in '{func_name}'."}

        doc = inspect.getdoc(target) or "No documentation available."
        try:
            sig = str(inspect.signature(target))
        except Exception:
            sig = "N/A"

        return {
            "success": True,
            "target": func_name,
            "signature": f"{func_name}{sig}",
            "docstring": doc,
            "type": str(type(target))
        }

    def call_func(self, mod, func_name: str, args: list, kwargs: dict) -> dict:
        """Execute a function inside the package."""
        target = mod
        for part in func_name.split("."):
            if hasattr(target, part):
                target = getattr(target, part)
            else:
                return {"success": False, "error": f"Member '{part}' not found in '{func_name}'."}

        if not callable(target):
            return {"success": True, "result": safe_serialize(target), "is_callable": False}

        result = target(*args, **kwargs)
        return {"success": True, "result": safe_serialize(result)}

    def run(self, args: dict) -> dict:
        """
        Run package wrapper actions.

        Args:
            package (str) / package_name: Pip package name
            action (str): 'introspect' (default), 'help', 'call'
            function (str, optional): Function/class name
            args (list, optional): Arguments for function call
            kwargs (dict, optional): Keyword arguments for function call
            auto_install (bool): Default True
        """
        package = args.get("package") or args.get("package_name")
        if not package:
            return {"success": False, "error": "Missing required argument 'package'."}

        action = args.get("action", "introspect").lower()
        auto_install_flag = args.get("auto_install", True)

        try:
            mod = self.import_package(package, auto_install=auto_install_flag)
        except Exception as e:
            return {"success": False, "error": f"Could not import package '{package}': {str(e)}"}

        func_name = args.get("function") or args.get("func")

        if action in ("introspect", "list", "info"):
            if func_name:
                return self.get_help(mod, func_name)
            return {"success": True, "package": package, "introspection": self.introspect(mod)}

        elif action in ("help", "doc", "signature"):
            if not func_name:
                return {"success": False, "error": "Action 'help' requires 'function' parameter."}
            return self.get_help(mod, func_name)

        elif action in ("call", "execute", "run"):
            if not func_name:
                return {"success": False, "error": "Action 'call' requires 'function' parameter."}
            call_args = args.get("func_args") if "func_args" in args else args.get("args", [])
            if not isinstance(call_args, list):
                call_args = [call_args]
            call_kwargs = args.get("func_kwargs") if "func_kwargs" in args else args.get("kwargs", {})
            if not isinstance(call_kwargs, dict):
                call_kwargs = {}
            return self.call_func(mod, func_name, call_args, call_kwargs)

        else:
            return {"success": False, "error": f"Unknown action '{action}'. Options: introspect, help, call"}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_args = json.loads(sys.argv[1])
    else:
        raw_args = {"package": "json", "action": "introspect"}
    skill = Skill()
    print(json.dumps(skill.run(raw_args), indent=2))
