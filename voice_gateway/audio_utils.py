"""
Audio utilities for EvolvixOS Voice Gateway.

Provides audio format validation, audio metadata extraction, and audio conversion
to 16kHz mono 16-bit PCM WAV standard for Whisper speech-to-text processing.
"""

import audioop
import os
import wave
from pathlib import Path
from typing import Any, Dict, Optional


def is_valid_wav(file_path: str) -> bool:
    """
    Validate whether a file exists and is a readable WAV audio file.

    :param file_path: Path to the audio file.
    :return: True if valid WAV file, False otherwise.
    """
    if not os.path.exists(file_path):
        return False

    if os.path.getsize(file_path) < 44:
        return False

    try:
        with open(file_path, "rb") as f:
            header = f.read(12)
            if len(header) < 12:
                return False
            # Check RIFF signature and WAVE format identifier
            if not (header.startswith(b"RIFF") and header[8:12] == b"WAVE"):
                return False

        with wave.open(file_path, "rb") as wav_file:
            _ = wav_file.getparams()
            return True
    except Exception:
        return False


def get_audio_info(file_path: str) -> Dict[str, Any]:
    """
    Extract audio metadata: duration (sec), sample_rate, channels, sample_width, size_bytes.

    :param file_path: Path to the audio file.
    :return: Dictionary containing audio file properties.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    file_size = os.path.getsize(file_path)

    if not is_valid_wav(file_path):
        # Optional fallback to pydub if installed
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return {
                "duration_sec": round(len(audio) / 1000.0, 3),
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "sample_width": audio.sample_width,
                "size_bytes": file_size,
            }
        except Exception:
            raise ValueError(f"File '{file_path}' is not a valid WAV or supported audio format")

    with wave.open(file_path, "rb") as wav:
        channels = wav.getnchannels()
        sampwidth = wav.getsampwidth()
        framerate = wav.getframerate()
        nframes = wav.getnframes()
        duration = nframes / float(framerate) if framerate > 0 else 0.0

        return {
            "duration_sec": round(duration, 3),
            "sample_rate": framerate,
            "channels": channels,
            "sample_width": sampwidth,
            "size_bytes": file_size,
        }


def convert_to_wav(
    input_path: str,
    target_sample_rate: int = 16000,
    target_channels: int = 1,
    target_sample_width: int = 2,
    output_path: Optional[str] = None,
) -> str:
    """
    Convert an audio file to WAV format (16kHz, mono, 16-bit PCM standard for Whisper STT).

    Uses Python's standard library wave and audioop modules, with fallback to pydub.

    :param input_path: Path to source audio file.
    :param target_sample_rate: Desired sample rate in Hz (default: 16000).
    :param target_channels: Desired channel count (default: 1 for mono).
    :param target_sample_width: Desired bytes per sample (default: 2 for 16-bit PCM).
    :param output_path: Optional output file path. If None, auto-generated alongside input file.
    :return: Path to the converted WAV file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    if output_path is None:
        out_dir = Path(input_path).parent
        out_name = f"conv_{Path(input_path).stem}.wav"
        output_path = str(out_dir / out_name)

    # Check if input is already a valid WAV matching target parameters
    if is_valid_wav(input_path):
        info = get_audio_info(input_path)
        if (
            info["sample_rate"] == target_sample_rate
            and info["channels"] == target_channels
            and info["sample_width"] == target_sample_width
        ):
            if os.path.abspath(input_path) != os.path.abspath(output_path):
                import shutil
                shutil.copy2(input_path, output_path)
            return output_path

    # Standard conversion using built-in wave & audioop
    try:
        with wave.open(input_path, "rb") as wav_in:
            nchannels = wav_in.getnchannels()
            sampwidth = wav_in.getsampwidth()
            framerate = wav_in.getframerate()
            nframes = wav_in.getnframes()
            frames = wav_in.readframes(nframes)

        curr_frames = frames
        curr_channels = nchannels
        curr_sampwidth = sampwidth
        curr_rate = framerate

        # 1. Channel conversion (stereo -> mono)
        if curr_channels != target_channels:
            if curr_channels == 2 and target_channels == 1:
                curr_frames = audioop.tomono(curr_frames, curr_sampwidth, 0.5, 0.5)
                curr_channels = 1
            else:
                raise ValueError(f"Cannot convert channel count from {curr_channels} to {target_channels}")

        # 2. Sample width conversion (e.g. 8-bit/24-bit -> 16-bit)
        if curr_sampwidth != target_sample_width:
            curr_frames = audioop.lin2lin(curr_frames, curr_sampwidth, target_sample_width)
            curr_sampwidth = target_sample_width

        # 3. Sample rate conversion (e.g. 44100Hz -> 16000Hz)
        if curr_rate != target_sample_rate:
            converted, _ = audioop.ratecv(
                curr_frames,
                curr_sampwidth,
                curr_channels,
                curr_rate,
                target_sample_rate,
                None,
            )
            curr_frames = converted
            curr_rate = target_sample_rate

        # Write output file
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with wave.open(output_path, "wb") as wav_out:
            wav_out.setnchannels(target_channels)
            wav_out.setsampwidth(target_sample_width)
            wav_out.setframerate(target_sample_rate)
            wav_out.writeframes(curr_frames)

        return output_path

    except Exception as primary_err:
        # Fallback to pydub if installed
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(input_path)
            audio = audio.set_frame_rate(target_sample_rate)
            audio = audio.set_channels(target_channels)
            audio = audio.set_sample_width(target_sample_width)
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            audio.export(output_path, format="wav")
            return output_path
        except Exception:
            raise RuntimeError(f"Audio conversion failed for '{input_path}': {primary_err}")
