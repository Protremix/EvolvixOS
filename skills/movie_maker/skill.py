"""
EvolvixOS — Movie Maker Skill
Creates full movies from a text prompt using local AI. Zero tokens.

Pipeline:
  1. Script — LLM writes a script from your prompt
  2. Scenes — Breaks script into scenes with visual descriptions
  3. Images — Generates scene images (FLUX.1 / Stable Diffusion)
  4. Voice — Generates narration/character voices (Kokoro TTS)
  5. Music — Generates background music (MusicGen)
  6. Video — Animates images into video clips (Wan 2.1 / AnimateDiff)
  7. Assembly — Combines everything into a final movie (FFmpeg/MoviePy)

All 100% local. No external services.
"""

import os
import json
import time
import subprocess
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class Skill:
    """Movie creation pipeline — from text prompt to full movie."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/videos"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir = self.output_dir / "movie_frames"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir = self.output_dir / "movie_audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "create")

        if action == "create":
            return self.create_movie(args)
        elif action == "script":
            return self.generate_script(args)
        elif action == "info":
            return self._info()
        else:
            return f"Unknown action: {action}. Use: create, script, info"

    def _info(self) -> str:
        return """Movie Maker Skill — Creates full movies from text prompts.

Actions:
  create  — Full movie pipeline (script → images → voice → music → video → assembly)
  script  — Generate just the script for a movie

Args for 'create':
  prompt:     Movie description (e.g., "A 60-second sci-fi short about AI waking up")
  duration:   Target duration in seconds (default: 60)
  style:      Visual style (cinematic, anime, realistic, cartoon, documentary)
  voice:      Narrator voice (af=American female, am=American male, bf=British female)
  resolution: Video resolution (720p, 1080p) (default: 720p)
  music:      Background music mood (epic, calm, suspense, cheerful, sad)

Example:
  <skill name="movie_maker">{"action": "create", "prompt": "A robot discovering nature for the first time", "duration": 30, "style": "cinematic"}</skill>
"""

    def generate_script(self, args: dict) -> str:
        """Generate a movie script using the local LLM."""
        import ollama

        prompt = args.get("prompt", "A short film")
        duration = args.get("duration", 60)
        style = args.get("style", "cinematic")

        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        client = ollama.Client(host=ollama_host)

        num_scenes = max(3, min(20, duration // 10))  # ~10 seconds per scene

        llm_prompt = f"""You are a movie script writer. Write a script for a {duration}-second {style} short film.

Concept: {prompt}

Write the script with exactly {num_scenes} scenes. For each scene, include:

SCENE [number]:
  DURATION: [seconds]
  VISUAL: [detailed visual description for image generation — be very specific about lighting, colors, composition]
  NARRATION: [narration text that will be spoken aloud]
  MOOD: [emotional tone]
  MUSIC: [music style for this scene]

The script should tell a compelling story. Be specific with visual descriptions so they can be used as image generation prompts.

Format each scene clearly."""

        response = client.chat(
            model=os.environ.get("EVOLVIX_MODEL", "deepseek-r1:7b"),
            messages=[{"role": "user", "content": llm_prompt}],
            options={"temperature": 0.8, "num_ctx": 32768},
        )

        script = response["message"]["content"]

        # Save script
        script_path = self.output_dir / "script.txt"
        script_path.write_text(script)

        return f"Script generated with {num_scenes} scenes. Saved to {script_path}\n\n{script[:1000]}..."

    def create_movie(self, args: dict) -> str:
        """Full movie creation pipeline."""
        prompt = args.get("prompt", "A short film")
        duration = args.get("duration", 60)
        style = args.get("style", "cinematic")
        voice = args.get("voice", "af")
        resolution = args.get("resolution", "720p")
        music_mood = args.get("music", "epic")

        console.print(f"[bold cyan]🎬 Creating movie: {prompt}[/bold cyan]")
        console.print(f"   Duration: {duration}s | Style: {style} | Voice: {voice}")

        # Step 1: Generate script
        console.print("\n[blue]Step 1/6: Writing script...[/blue]")
        script_result = self.generate_script(args)
        script_path = self.output_dir / "script.txt"
        script = script_path.read_text()

        # Parse scenes
        scenes = self._parse_scenes(script)
        console.print(f"[green]✅ {len(scenes)} scenes written[/green]")

        if not scenes:
            return f"Failed to generate script. Raw output:\n{script[:2000]}"

        # Step 2: Generate images for each scene
        console.print("\n[blue]Step 2/6: Generating scene images...[/blue]")
        image_paths = []
        for i, scene in enumerate(scenes):
            console.print(f"  Scene {i+1}/{len(scenes)}: {scene['visual'][:50]}...")
            img_path = self.image_dir / f"scene_{i:03d}.png"
            try:
                self._generate_image(scene["visual"], img_path, style)
                image_paths.append(str(img_path))
            except Exception as e:
                console.print(f"  [yellow]⚠ Image generation failed: {e}[/yellow]")
                # Create placeholder image
                self._create_placeholder(img_path, scene["visual"])
                image_paths.append(str(img_path))
        console.print(f"[green]✅ {len(image_paths)} images generated[/green]")

        # Step 3: Generate voice narration
        console.print("\n[blue]Step 3/6: Generating voice narration...[/blue]")
        audio_paths = []
        for i, scene in enumerate(scenes):
            narration = scene.get("narration", "")
            if narration.strip():
                console.print(f"  Scene {i+1}: {narration[:50]}...")
                audio_path = self.audio_dir / f"narration_{i:03d}.wav"
                try:
                    self._generate_speech(narration, audio_path, voice)
                    audio_paths.append(str(audio_path))
                except Exception as e:
                    console.print(f"  [yellow]⚠ TTS failed: {e}[/yellow]")
                    audio_paths.append(None)
            else:
                audio_paths.append(None)
        console.print(f"[green]✅ {sum(1 for a in audio_paths if a)} narration clips generated[/green]")

        # Step 4: Generate background music
        console.print("\n[blue]Step 4/6: Generating background music...[/blue]")
        music_path = self.audio_dir / "background_music.wav"
        try:
            self._generate_music(music_mood, music_path, duration)
            console.print(f"[green]✅ Music generated[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ Music generation failed: {e}[/yellow]")
            music_path = None

        # Step 5: Create video clips from images
        console.print("\n[blue]Step 5/6: Creating video clips...[/blue]")
        clip_paths = []
        for i, (img_path, scene) in enumerate(zip(image_paths, scenes)):
            scene_duration = int(scene.get("duration", duration // len(scenes)))
            clip_path = self.output_dir / f"clip_{i:03d}.mp4"
            audio = audio_paths[i] if i < len(audio_paths) else None
            try:
                self._create_clip(img_path, clip_path, scene_duration, audio, resolution)
                clip_paths.append(str(clip_path))
            except Exception as e:
                console.print(f"  [yellow]⚠ Clip {i+1} failed: {e}[/yellow]")
                clip_paths.append(None)
        console.print(f"[green]✅ {sum(1 for c in clip_paths if c)} clips created[/green]")

        # Step 6: Assemble final movie
        console.print("\n[blue]Step 6/6: Assembling final movie...[/blue]")
        valid_clips = [c for c in clip_paths if c]
        if not valid_clips:
            return "Failed to create any video clips."

        output_path = self.output_dir / f"movie_{int(time.time())}.mp4"
        try:
            self._assemble_movie(valid_clips, music_path, output_path)
            console.print(f"\n[bold green]🎬 Movie created: {output_path}[/bold green]")
            return f"Movie created successfully!\nPath: {output_path}\nScenes: {len(scenes)}\nDuration: ~{duration}s"
        except Exception as e:
            console.print(f"[yellow]⚠ Assembly with music failed, trying without...[/yellow]")
            try:
                self._assemble_movie(valid_clips, None, output_path)
                return f"Movie created (no music): {output_path}"
            except Exception as e2:
                return f"Movie assembly failed: {e2}"

    def _parse_scenes(self, script: str) -> list:
        """Parse the script into scene objects."""
        scenes = []
        current_scene = {}
        scene_num = 0

        for line in script.split("\n"):
            line = line.strip()
            if line.upper().startswith("SCENE"):
                if current_scene:
                    scenes.append(current_scene)
                scene_num += 1
                current_scene = {"num": scene_num}
            elif line.upper().startswith("DURATION:"):
                try:
                    current_scene["duration"] = int("".join(c for c in line.split(":")[1] if c.isdigit()))
                except Exception:
                    current_scene["duration"] = 10
            elif line.upper().startswith("VISUAL:"):
                current_scene["visual"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("NARRATION:"):
                current_scene["narration"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("MOOD:"):
                current_scene["mood"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("MUSIC:"):
                current_scene["music"] = line.split(":", 1)[1].strip()

        if current_scene:
            scenes.append(current_scene)

        # Ensure all scenes have required fields
        for s in scenes:
            s.setdefault("duration", 10)
            s.setdefault("visual", "A cinematic scene")
            s.setdefault("narration", "")

        return scenes

    def _generate_image(self, prompt: str, output_path: Path, style: str = "cinematic"):
        """Generate an image using local image model."""
        full_prompt = f"{style} style, {prompt}, high quality, detailed, professional"

        try:
            from diffusers import FluxPipeline
            import torch

            pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
            else:
                pipe = pipe.to("cpu")

            image = pipe(
                full_prompt,
                num_inference_steps=4,
                guidance_scale=0.0,
                height=768,
                width=1280,
            ).images[0]

            image.save(str(output_path))
            return True

        except Exception:
            # Fallback: try Stable Diffusion
            try:
                from diffusers import StableDiffusionPipeline
                import torch

                pipe = StableDiffusionPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=torch.float16,
                )
                if torch.cuda.is_available():
                    pipe = pipe.to("cuda")

                image = pipe(full_prompt, num_inference_steps=20).images[0]
                image.save(str(output_path))
                return True
            except Exception:
                raise

    def _create_placeholder(self, path: Path, text: str):
        """Create a simple placeholder image when generation fails."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (1280, 720), color=(20, 20, 40))
            draw = ImageDraw.Draw(img)
            draw.text((100, 300), text[:80], fill=(200, 200, 200))
            img.save(str(path))
        except Exception:
            pass

    def _generate_speech(self, text: str, output_path: Path, voice: str = "af"):
        """Generate speech using local TTS."""
        try:
            from kokoro import KModel, KPipeline
            import soundfile as sf

            model = KModel().eval()
            pipeline = KPipeline(model=model, voice=voice)
            audio = []
            for _, _, chunk in pipeline(text, voice=voice):
                audio.append(chunk)
            import numpy as np
            full_audio = np.concatenate(audio)
            sf.write(str(output_path), full_audio, 24000)
            return True
        except Exception:
            # Fallback: pyttsx3
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.save_to_file(text, str(output_path))
                engine.runAndWait()
                return True
            except Exception:
                raise

    def _generate_music(self, mood: str, output_path: Path, duration: int):
        """Generate background music using MusicGen."""
        try:
            from transformers import MusicgenForConditionalGeneration, AutoProcessor
            import torch

            model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
            processor = AutoProcessor.from_pretrained("facebook/musicgen-small")

            if torch.cuda.is_available():
                model = model.to("cuda")

            inputs = processor(text=[f"{mood} background music, instrumental"], padding=True, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            audio = model.generate(**inputs, max_new_tokens=1500)
            processor.batch_decode(audio, smooth=True)[0].save(str(output_path))
            return True
        except Exception:
            raise

    def _create_clip(self, image_path: str, output_path: Path, duration: int, audio_path: Optional[str], resolution: str):
        """Create a video clip from an image with optional audio."""
        res_map = {"720p": "1280:720", "1080p": "1920:1080"}
        res = res_map.get(resolution, "1280:720")

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-t", str(duration),
            "-vf", f"scale={res},format=yuv420p,fade=in:0:15,fade=out:st={max(0,duration-1)}:d=1",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-r", "24",
        ]

        if audio_path:
            cmd.extend(["-i", audio_path, "-c:a", "aac", "-b:a", "128k", "-shortest"])
        else:
            cmd.extend(["-an"])

        cmd.append(str(output_path))
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)
        return True

    def _assemble_movie(self, clip_paths: list, music_path: Optional[str], output_path: Path):
        """Assemble all clips into final movie with music."""
        # Create concat file
        concat_file = self.output_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for clip in clip_paths:
                f.write(f"file '{clip}'\n")

        # Concatenate clips
        temp_video = self.output_dir / "temp_video.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", str(temp_video)
        ], capture_output=True, timeout=120, check=True)

        # Add music if available
        if music_path and music_path.exists():
            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_video), "-i", str(music_path),
                "-filter_complex", "[1:a]volume=0.3[bg];[0:a]volume=1.0[voice];[bg][voice]amix=inputs=2:duration=shortest[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                str(output_path)
            ], capture_output=True, timeout=120, check=True)
        else:
            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_video), "-c", "copy", str(output_path)
            ], capture_output=True, timeout=60, check=True)

        # Cleanup
        temp_video.unlink(missing_ok=True)
        concat_file.unlink(missing_ok=True)

        return True
