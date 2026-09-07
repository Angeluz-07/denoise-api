import gradio as gr
from pathlib import Path
import os
import tempfile
from utils import run_async_subprocess

from process_record import (
    transform_m4a_to_wav,
    split_audio,
    remove_noise_from_folder,
    combine_wav_files_with_suffix,
    generate_timestamp,
    remove_silence,
    add_suffix_before_extension,
)
from version import VERSION

BASE_DIR = Path(__file__).parent.parent
INPUT_AUDIOS_FOLDER = BASE_DIR / ".data" / "audios"
INPUT_AUDIOS_FOLDER.mkdir(exist_ok=True)

VIDEOS_DIR = BASE_DIR / ".data" / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)

DEFAULT_EXAMPLE = BASE_DIR / ".data" / "example" / "Voz 070.m4a"


def process_audio(audio_filepath):
    # generate workdir folder
    TS = generate_timestamp()
    WORKDIR_FOLDER = INPUT_AUDIOS_FOLDER / f"{TS}_{Path(audio_filepath).stem}"
    WORKDIR_FOLDER.mkdir(exist_ok=True)

    # convert to wav
    wav_filepath = transform_m4a_to_wav(audio_filepath, output_dir=WORKDIR_FOLDER)

    # Denoise
    input_filepath = wav_filepath
    output_dir = split_audio(input_filepath)
    remove_noise_from_folder(output_dir)
    denoised_filepath = combine_wav_files_with_suffix(
        input_folder=output_dir,
        output_folder=WORKDIR_FOLDER,
        suffix="_noiseRemovedDF",
        output_filename=Path(input_filepath).stem + "_D.wav",
    )
    return denoised_filepath


async def process_video(video_path: str | Path) -> Path:
    video_path = Path(video_path)

    # Create persistent temp files so Gradio can read them after the function finishes
    audio_in_fd, audio_in_path = tempfile.mkstemp(suffix=".wav")
    os.close(audio_in_fd)
    output_vid_path = VIDEOS_DIR / f"{video_path.stem}_D.mp4"

    try:
        # 1. Extract audio from video efficiently using your async subprocess
        extract_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            audio_in_path,
        ]
        await run_async_subprocess(extract_cmd, show_live_output=True)

        denoised_audio_path = process_audio(audio_in_path)

        # 3. Mux original video stream (lossless copy) with the new denoised audio
        # fmt:off
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(denoised_audio_path),
            "-c:v", "copy",  # Blazing fast: skips video re-encoding entirely
            "-c:a", "aac",  # Re-encodes audio to standard AAC for wide compatibility
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_vid_path,
        ]
        # fmt:on
        await run_async_subprocess(mux_cmd, show_live_output=True)

        print("Video denoised!")
        return output_vid_path

    finally:
        # Clean up the intermediate raw audio file to save space
        if os.path.exists(audio_in_path):
            os.remove(audio_in_path)


theme = gr.themes.Default(
    text_size=gr.themes.sizes.text_lg,  # Options: text_sm, text_md, text_lg
)

audio_demo = gr.Interface(
    description="Upload your voice record. You can test the app with the default example as well.",
    fn=process_audio,
    inputs=gr.Audio(value=DEFAULT_EXAMPLE, label="Input Audio(*.m4a)", type="filepath"),
    outputs=gr.Audio(label="Output Audio(*.wav)"),
    title="Denoise API",
)

video_demo = gr.Interface(
    description="Upload a video with audio noise. The output will be the same video with denoised audio.",
    fn=process_video,
    inputs=gr.Video(label="Input Video"),
    outputs=gr.Video(label="Output Video"),
    title="Denoise API",
)

demo = gr.TabbedInterface([audio_demo, video_demo], ["Audio", "Video"])

demo.launch(server_name="0.0.0.0", show_error=True, theme=theme)
