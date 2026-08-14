#!/usr/bin/env python3
"""Offline Translator - Argos Translate (MIT) - 100% Free"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        if not text:
            return {"error": "text required"}
        try:
            from argostranslate import translate
            installed = translate.get_installed_languages()
            src = [l for l in installed if l.code == args.get("from", "en")]
            dst = [l for l in installed if l.code == args.get("to", "es")]
            if src and dst:
                return {"translated": src[0].get_translation(dst[0]).translate(text)}
            return {"error": "Language pair not installed"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "argostranslate"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
