import gradio as gr
from pathlib import Path
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


demo = gr.Interface(
    title=f"<center><h1>Denoise API</h1>(v{VERSION})</center> ",
    description='<p style="font-size: 20px; font-weight: 400;">Upload your voice record. You can test the app with the default example as well.<p>',
    article="",
    fn=process_audio,
    inputs=[
        gr.Audio(value=DEFAULT_EXAMPLE, label="Input Audio(*.m4a)", type="filepath")
    ],
    outputs=[gr.Audio(label="Output Audio(*.wav)")],
)

demo.launch(server_name="0.0.0.0", show_error=True)
