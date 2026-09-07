from pydub import AudioSegment, silence
import os
import math


def transform_m4a_to_wav(m4a_file_path, output_dir=None):
    """
    Transform an m4a file to wav format with 48kHz sample rate.

    Args:
        m4a_file_path (str): Path to the input .m4a file
        output_dir (str, optional): Directory where output file will be saved
    Returns:
        str: Path to the converted WAV file
    """
    try:
        # Set output directory to same as input if none specified
        if output_dir is None:
            output_dir = os.path.dirname(m4a_file_path)

        # Create output directory if it doesn't exist
        # os.makedirs(output_dir, exist_ok=True)

        # Load and convert audio
        audio = AudioSegment.from_file(m4a_file_path)

        # Generate output filename
        base_filename = os.path.splitext(os.path.basename(m4a_file_path))[0]
        wav_path = os.path.join(output_dir, f"{base_filename}.wav")

        # Export with 48kHz sample rate
        audio.export(wav_path, format="wav", parameters=["-ar", "48000"])
        print(f"Successfully converted to WAV: {wav_path}")

        return wav_path
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return None


def split_audio(audio_path, segment_length_ms=60000):
    """
    Split an audio file into segments of specified length.

    Args:
        audio_path (str): Path to the audio file to split
        segment_length_ms (int): Length of each segment in milliseconds
    """
    try:
        # Load audio
        audio = AudioSegment.from_file(audio_path)

        # Get total duration and calculate number of segments
        total_duration = len(audio)
        num_segments = math.ceil(total_duration / segment_length_ms)

        fname = f"{os.path.splitext(os.path.basename(audio_path))[0]}"

        # Create output directory
        output_dir = os.path.join(os.path.dirname(audio_path), f"{fname}_chopped")
        os.makedirs(output_dir, exist_ok=True)

        # Split and save segments
        for i in range(num_segments):
            start_time = i * segment_length_ms
            end_time = min((i + 1) * segment_length_ms, total_duration)

            segment = audio[start_time:end_time]
            segment_filename = (
                f"{os.path.splitext(os.path.basename(audio_path))[0]}_part{i+1}.wav"
            )
            segment_path = os.path.join(output_dir, segment_filename)

            segment.export(
                segment_path, format="wav", parameters=["-ar", "48000"]
            )  # -ar sets the sample rate
            print(f"Created segment: {segment_path}")

        return output_dir
    except Exception as e:
        print(f"Error splitting file: {str(e)}")


from pathlib import Path


def remove_noise_from_folder(folder_path):
    from df.enhance import enhance, init_df, load_audio, save_audio

    # Load default model
    model, df_state, _ = init_df()
    # Download and open some audio file. You use your audio files here

    folder_path = Path(folder_path)
    denoised_suffix = "_noiseRemovedDF"

    for file_path in folder_path.iterdir():
        if file_path.is_file():
            try:
                audio_path = file_path

                audio, _ = load_audio(audio_path, sr=df_state.sr())
                # Denoise the audio
                enhanced = enhance(model, df_state, audio)

                filename = file_path.parent / (
                    file_path.stem + denoised_suffix + ".wav"
                )
                save_audio(filename, enhanced, df_state.sr())
                print(f"Noise removed : {file_path.stem}")
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")


def remove_silence(
    input_file, output_file, min_silence_len=500, silence_thresh=-40, keep_silence=100
):
    """
    Removes silence gaps from an audio file.

    Args:
        input_file: Path to input WAV file
        output_file: Path to save processed WAV file
        min_silence_len: Minimum duration of silence to remove (milliseconds)
        silence_thresh: Silence threshold in dBFS (-infinity to 0)
        keep_silence: Amount of silence to keep at the beginning/end of each non-silent chunk
    """
    # Check if input file exists
    assert os.path.isfile(input_file), f"Input file {input_file} not found"

    # Load audio file
    audio = AudioSegment.from_wav(input_file)

    audio_chunks = silence.split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence,
    )

    processed_audio = AudioSegment.empty()
    for chunk in audio_chunks:
        processed_audio += chunk

    processed_audio.export(
        output_file, format="wav", parameters=["-ar", "48000"]
    )  # -ar sets the sample rate


from pathlib import Path


def add_suffix_before_extension(file_path_str: str, suffix: str) -> str:
    """
    Adds a suffix before the file extension of a given path.

    Args:
        file_path_str: The original file path as a string.
        suffix: The suffix to be added (e.g., "_new", "-copy").

    Returns:
        The new file path as a string with the suffix added before the extension.
    """
    path_obj = Path(file_path_str)
    # Reconstruct the path with the suffix inserted before the extension
    new_stem = path_obj.stem + suffix
    new_path_obj = path_obj.parent / (new_stem + path_obj.suffix)
    return str(new_path_obj)


def combine_wav_files_with_suffix(
    input_folder: str,
    output_folder: str,
    suffix: str,
    output_filename: str = "combined.wav",
) -> str:
    """
    Combine all WAV files with a specific suffix from input_folder into a single WAV file.

    Args:
        input_folder: Path to folder containing WAV files
        output_folder: Path where combined WAV will be saved
        suffix: Suffix to filter WAV files (e.g., "_part1")
        output_filename: Name of the output file (default: "combined.wav")

    Returns:
        Path to the combined WAV file
    """
    # Create output folder if it doesn't exist
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all WAV files with the specified suffix
    wav_files = [str(p) for p in Path(input_folder).glob(f"**/*{suffix}.wav")]
    from natsort import natsorted

    wav_files = natsorted(wav_files)

    if not wav_files:
        raise ValueError(f"No WAV files found with suffix '{suffix}' in {input_folder}")

    # Load and combine audio files
    combined = AudioSegment.empty()
    for file_path in wav_files:
        audio = AudioSegment.from_wav(file_path)
        combined += audio

    # Export combined audio
    output_file = output_path / output_filename
    combined.export(
        str(output_file), format="wav", parameters=["-ar", "48000"]
    )  # -ar sets the sample rate

    return str(output_file)


def increase_wav_gain(input_file, output_file, gain_db):
    """
    Increase the gain of a WAV file by a specified number of decibels.

    Args:
        input_file: Path to input WAV file
        output_file: Path to output WAV file
        gain_db: Gain increase in decibels (e.g., 10 for 10dB increase)
    """
    # Load the audio file
    audio = AudioSegment.from_wav(input_file)

    # Increase the volume
    louder = audio + gain_db

    # Export the modified audio
    louder.export(
        output_file, format="wav", parameters=["-ar", "48000"]
    )  # -ar sets the sample rate


from datetime import datetime
import pytz


def generate_timestamp():
    """Generate a timestamp string in YYYYMMDD_HHMMSS format."""
    return datetime.now(pytz.UTC).strftime("%Y%m%d_%H%M%S")


def postprocess_denoised_audio(denoised_filepath, min_silence, silence_thresh):
    if denoised_filepath:
        # Remove Silences
        input_filepath = denoised_filepath
        output_path = add_suffix_before_extension(input_filepath, "_NS")
        remove_silence(
            input_filepath,
            output_file=output_path,
            min_silence_len=min_silence,
            silence_thresh=silence_thresh,
        )
        denoised_and_nosilence_path = output_path
    else:
        denoised_and_nosilence_path = None
    return denoised_and_nosilence_path
