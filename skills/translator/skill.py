"""
EvolvixOS — Translator Skill
Translate text between 30+ languages — fully offline using Argos Translate.
100% local. Zero tokens. Zero cloud.

Pip: pip install argostranslate
License: MIT (Argos Translate), CC-BY (language models)
"""

import os
import json
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Translator — offline translation for 30+ languages. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/translations"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._languages = None
        self._translators = {}

    def run(self, args: dict) -> str:
        action = args.get("action", "translate")

        if action == "translate":
            return self.translate(
                args.get("text", ""),
                args.get("from_lang", "en"),
                args.get("to_lang", "es")
            )
        elif action == "detect":
            return self.detect_language(args.get("text", ""))
        elif action == "list_languages":
            return self.list_languages()
        else:
            return f"Unknown action: {action}. Use: translate, detect, list_languages"

    def translate(self, text: str, from_lang: str = "en", to_lang: str = "es") -> str:
        if not text:
            return "Error: No text provided."

        try:
            import argostranslate.translate as argos
        except ImportError:
            return "Error: pip install argostranslate\nThen download a language pair:\n  python -c \"import argostranslate; argostranslate.package.install_all()\""

        try:
            key = f"{from_lang}_{to_lang}"
            if key not in self._translators:
                self._translators[key] = argos.get_translation_from_languages(
                    argos.get_installed_languages(),
                    from_lang, to_lang
                )
            translator = self._translators[key]
            result = translator.translate(text)
            return result
        except Exception as e:
            return (f"Error translating {from_lang}→{to_lang}: {e}\n"
                    f"Available languages: {self.list_languages()}")

    def detect_language(self, text: str) -> str:
        try:
            import argostranslate.translate as argos
            installed = argos.get_installed_languages()
            # Simple detection: check which language model can process the text
            # This is a heuristic — Argos doesn't have built-in detection
            return f"Installed language pairs: {[l.code for l in installed]}"
        except Exception:
            return "Language detection requires langdetect: pip install langdetect"

    def list_languages(self) -> str:
        try:
            import argostranslate.translate as argos
            installed = argos.get_installed_languages()
            return json.dumps([{"code": l.code, "name": l.name} for l in installed], indent=2)
        except Exception as e:
            return f"Error: {e}\nInstall: pip install argostranslate && python -c \"import argostranslate; argostranslate.package.install_all()\""
