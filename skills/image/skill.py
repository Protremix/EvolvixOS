"""
EvolvixOS — Image Generation Skill
Text-to-image using FLUX.1 schnell (Apache 2.0). 100% local, zero tokens.
"""

import os
import time
import torch
from pathlib import Path
from rich.console import Console

console = Console()


class Skill:
    """Image generation skill — FLUX.1 / Stable Diffusion, fully local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.model_name = self.config.get("model", "flux-schnell")
        self.output_dir = Path(self.config.get("output_dir", "./output/images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._pipeline = None

    def _load_model(self):
        """Load the image model locally."""
        if self._pipeline is not None:
            return self._pipeline

        console.print(f"[cyan]📦 Loading image model: {self.model_name}[/cyan]")
        console.print("[dim]First run downloads the model (~11GB for FLUX, ~6GB for SDXL).[/dim]")

        from diffusers import FluxPipeline, StableDiffusionXLPipeline

        if self.model_name == "flux-schnell":
            self._pipeline = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-schnell",
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
            )
            if self.device == "cuda":
                self._pipeline.enable_model_cpu_offload()
        elif self.model_name == "sd-xl":
            self._pipeline = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )
            if self.device == "cuda":
                self._pipeline.enable_model_cpu_offload()
        else:
            raise ValueError(f"Unknown image model: {self.model_name}")

        return self._pipeline

    def generate_image(self, prompt: str, negative_prompt: str = "", width: int = 1024, height: int = 1024) -> str:
        """Generate image from text. 100% local."""
        console.print(f"[cyan]🎨 Generating image: {prompt[:80]}...[/cyan]")

        pipeline = self._load_model()

        with torch.inference_mode():
            if self.model_name == "flux-schnell":
                # FLUX schnell — fast, 4 steps
                output = pipeline(
                    prompt=prompt,
                    num_inference_steps=4,
                    guidance_scale=0.0,
                    width=width,
                    height=height,
                )
            else:
                # SDXL — more control
                output = pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt or "blurry, low quality, distorted, watermark, ugly",
                    num_inference_steps=25,
                    guidance_scale=7.5,
                    width=width,
                    height=height,
                )

        image = output.images[0]
        filename = self.output_dir / f"image_{int(time.time())}.png"
        image.save(str(filename))

        console.print(f"[green]💾 Image saved: {filename}[/green]")
        return str(filename)

    def run(self, args: dict) -> str:
        """Execute the image skill."""
        action = args.get("action", "generate")
        prompt = args.get("prompt", args.get("query", ""))

        if action == "generate":
            if not prompt:
                return "Error: no prompt provided for image generation."

            # Parse size
            size = args.get("size", "1024x1024")
            try:
                w, h = map(int, size.split("x"))
            except ValueError:
                w, h = 1024, 1024

            result = self.generate_image(
                prompt=prompt,
                negative_prompt=args.get("negative_prompt", ""),
                width=w, height=h,
            )
            return f"Image generated: {result}"

        else:
            return f"Unknown action: {action}. Use 'generate'."
