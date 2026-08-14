"""
EvolvixOS — Pipeline Engine Skill
Chains multiple skills together in sequential steps.
Passes output from one step into the next, enabling complex composable workflows.
"""

import sys
import os
import json
import re
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, List


class Skill:
    """Pipeline Engine — Executes multi-step skill pipelines with data piping."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.skills_dir = Path(self.config.get("skills_dir", Path(__file__).parent.parent))

    def _load_skill_class(self, skill_name: str):
        """Dynamically load the Skill class from skills/<skill_name>/skill.py."""
        target_path = self.skills_dir / skill_name / "skill.py"
        if not target_path.exists():
            raise FileNotFoundError(f"Skill '{skill_name}' not found at {target_path}")

        module_name = f"evolvix_skills_{skill_name}"
        spec = importlib.util.spec_from_file_location(module_name, target_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for skill '{skill_name}'")

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, "Skill"):
            raise AttributeError(f"Skill '{skill_name}' at {target_path} does not export class 'Skill'")

        return mod.Skill

    def _resolve_template(self, arg_val: Any, prev_output: Any, all_outputs: List[Any]) -> Any:
        """Recursively resolve variables like $prev, $prev.key, {{prev}}, {{prev.key}}, $step0.key in args."""
        if isinstance(arg_val, str):
            if arg_val in ("$prev", "{{prev}}"):
                return prev_output

            m = re.match(r"^(?:\$prev|\{\{prev\}\})\.([a-zA-Z0-9_]+)$", arg_val)
            if m and isinstance(prev_output, dict):
                return prev_output.get(m.group(1), arg_val)

            res_str = arg_val
            if "$prev" in res_str or "{{prev}}" in res_str:
                if isinstance(prev_output, dict):
                    for k, v in prev_output.items():
                        res_str = res_str.replace(f"$prev.{k}", str(v))
                        res_str = res_str.replace(f"{{prev.{k}}}", str(v))
                    res_str = res_str.replace("$prev", json.dumps(prev_output))
                    res_str = res_str.replace("{{prev}}", json.dumps(prev_output))
                else:
                    res_str = res_str.replace("$prev", str(prev_output))
                    res_str = res_str.replace("{{prev}}", str(prev_output))

            for idx, step_out in enumerate(all_outputs):
                prefix = f"step{idx}"
                if isinstance(step_out, dict):
                    for k, v in step_out.items():
                        res_str = res_str.replace(f"${prefix}.{k}", str(v))
                        res_str = res_str.replace(f"{{{prefix}.{k}}}", str(v))

            return res_str

        elif isinstance(arg_val, dict):
            return {k: self._resolve_template(v, prev_output, all_outputs) for k, v in arg_val.items()}

        elif isinstance(arg_val, list):
            return [self._resolve_template(item, prev_output, all_outputs) for item in arg_val]

        return arg_val

    def run(self, args: dict) -> dict:
        """
        Execute a pipeline of skills.

        Args:
            steps (list): List of dicts, each with format:
                          {"skill": "skill_name", "args": {...}}
            ignore_errors (bool, optional): Continue running pipeline if a step fails (default: False).
        """
        steps = args.get("steps")
        if not steps or not isinstance(steps, list):
            return {"success": False, "error": "Missing required list argument 'steps'."}

        ignore_errors = args.get("ignore_errors", False)
        step_results = []
        prev_output = None

        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                return {"success": False, "error": f"Step at index {idx} must be a dictionary."}

            skill_name = step.get("skill") or step.get("skill_name") or step.get("name")
            if not skill_name:
                return {"success": False, "error": f"Step at index {idx} missing 'skill' or 'skill_name'."}

            step_args = step.get("args") or {}
            if not isinstance(step_args, dict):
                step_args = {"input": step_args}

            if "action" in step and "action" not in step_args:
                step_args["action"] = step["action"]

            resolved_args = self._resolve_template(step_args, prev_output, step_results)

            if prev_output is not None and "input" not in resolved_args and "prev_output" not in resolved_args:
                resolved_args["prev_output"] = prev_output

            try:
                skill_cls = self._load_skill_class(skill_name)
                skill_instance = skill_cls()
                result = skill_instance.run(resolved_args)
            except Exception as e:
                result = {"success": False, "error": f"Error running step {idx} ({skill_name}): {str(e)}"}

            step_record = {
                "step_index": idx,
                "skill": skill_name,
                "input_args": resolved_args,
                "output": result
            }
            step_results.append(step_record)
            prev_output = result

            step_success = result.get("success", True) if isinstance(result, dict) else True
            if not step_success and not ignore_errors:
                return {
                    "success": False,
                    "error": f"Pipeline stopped at step {idx} ({skill_name}) due to failure.",
                    "steps_executed": len(step_results),
                    "failed_step": idx,
                    "step_results": step_results
                }

        return {
            "success": True,
            "steps_executed": len(step_results),
            "final_output": prev_output,
            "step_results": step_results
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_args = json.loads(sys.argv[1])
    else:
        raw_args = {
            "steps": [
                {
                    "skill": "code_runner",
                    "args": {"code": "print(21 * 2)"}
                },
                {
                    "skill": "code_runner",
                    "args": {"code": "import sys; print('Prev output received:', '$prev.stdout'.strip())"}
                }
            ]
        }
    skill = Skill()
    print(json.dumps(skill.run(raw_args), indent=2))
