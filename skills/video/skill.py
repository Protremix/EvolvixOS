"""
EvolvixOS — Video Generation Skill
Text-to-video using open-source models (Wan 2.1 / AnimateDiff). Zero tokens.
Runs locally on GPU via diffusers.
"""

import os
import time
import torch
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()

# Lazy imports — only load when skill is used (saves memory)
_diffusers = None
_imageio = None


def _ensure_imports():
    global _diffusers, _imageio
    if _diffusers is None:
        from diffusers import DiffusionPipeline, AutoencoderKL, FluxPipeline
        _diffusers = {"DiffusionPipeline": DiffusionPipeline, "AutoencoderKL": AutoencoderKL, "FluxPipeline": FluxPipeline}
    if _imageio is None:
        import imageio
        import imageio_ffmpeg
        _imageio = {"imageio": imageio, "imageio_ffmpeg": imageio_ffmpeg}
    return _diffusers, _imageio


class Skill:
    """Video generation skill — 100% local, zero tokens."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.model_name = self.config.get("model", "wan2.1")
        self.output_dir = Path(self.config.get("output_dir", "./output/videos"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = self.config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        self.resolution = self.config.get("default_resolution", "720p")
        self.fps = self.config.get("default_fps", 24)
        self.duration = self.config.get("default_duration_seconds", 5)
        self.vram_optimization = self.config.get("vram_optimization", "sequential_cpu_offload")
        self._pipeline = None

    def _load_model(self):
        """Load the video model locally. One-time download, then cached."""
        if self._pipeline is not None:
            return self._pipeline

        console.print(f"[cyan]📦 Loading video model: {self.model_name}[/cyan]")
        console.print("[dim]First run downloads the model (~5-10GB). Subsequent runs use cache.[/dim]")

        diffusers, imageio = _ensure_imports()

        # Wan 2.1 — best open-source text-to-video (Apache 2.0 license)
        if self.model_name == "wan2.1":
            from diffusers import WanPipeline
            self._pipeline = WanPipeline.from_pretrained(
                "Wan-AI/Wan2.1-T2V-1.3B",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )
        # AnimateDiff — faster, lower VRAM
        elif self.model_name == "animatediff":
            from diffusers import AnimateDiffPipeline, MotionAdapter
            adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-2")
            self._pipeline = AnimateDiffPipeline.from_pretrained(
                "emilianJR/epiCRealism",
                motion_adapter=adapter,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )
        else:
            raise ValueError(f"Unknown video model: {self.model_name}")

        # VRAM optimization
        if self.device == "cuda" and self.vram_optimization:
            if self.vram_optimization == "sequential_cpu_offload":
                self._pipeline.enable_sequential_cpu_offload()
            elif self.vram_optimization == "model_cpu_offload":
                self._pipeline.enable_model_cpu_offload()
        elif self.device == "cpu":
            console.print("[yellow]⚠ Running on CPU. Video generation will be slow.[/yellow]")

        return self._pipeline

    def generate_video(self, prompt: str, negative_prompt: str = "") -> str:
        """Generate video from text prompt. 100% local."""
        console.print(f"[cyan]🎬 Generating video: {prompt[:80]}...[/cyan]")

        pipeline = self._load_model()

        # Generate frames
        console.print("[blue]🎞️  Generating frames...[/blue]")
        with torch.inference_mode():
            output = pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt or "blurry, low quality, distorted, watermark",
                num_frames=self.fps * self.duration,
                num_inference_steps=30,
                guidance_scale=7.5,
            )

        frames = output.frames[0]  # List of PIL images or numpy arrays
        console.print(f"[green]✅ Generated {len(frames)} frames[/green]")

        # Save as MP4
        _, imageio = _ensure_imports()
        writer = imageio["imageio"]
        ffmpeg_mod = imageio["imageio_ffmpeg"]

        filename = self.output_dir / f"video_{int(time.time())}.mp4"
        writer.mimwrite(
            str(filename),
            frames,
            fps=self.fps,
            codec="libx264",
            quality=8,
            output_params=["-pix_fmt", "yuv420p"],
        )

        console.print(f"[green]💾 Video saved: {filename}[/green]")
        return str(filename)

    def run(self, args: dict) -> str:
        """Execute the video skill."""
        action = args.get("action", "generate")
        prompt = args.get("prompt", args.get("query", ""))

        if action == "generate":
            if not prompt:
                return "Error: no prompt provided for video generation."
            result = self.generate_video(
                prompt=prompt,
                negative_prompt=args.get("negative_prompt", ""),
            )
            return f"Video generated successfully: {result}"

        elif action == "status":
            has_gpu = torch.cuda.is_available()
            gpu_name = torch.cuda.get_device_name(0) if has_gpu else "N/A"
            gpu_vram = f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB" if has_gpu else "N/A"
            return (
                f"Video Generation Status:\n"
                f"  Model: {self.model_name}\n"
                f"  Device: {self.device}\n"
                f"  GPU: {gpu_name} ({gpu_vram} VRAM)\n"
                f"  Resolution: {self.resolution}\n"
                f"  FPS: {self.fps}\n"
                f"  Duration: {self.duration}s\n"
                f"  VRAM optimization: {self.vram_optimization}\n"
            )

        else:
            return f"Unknown action: {action}. Use 'generate' or 'status'."
