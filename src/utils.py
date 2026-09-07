import asyncio
import subprocess
import json
import sys
from typing import List
from pathlib import Path


async def run_async_subprocess(
    command: List[str],
    show_live_output: bool = True,
    cwd: Path | str | None = None,
) -> str:
    print(f"Starting command call (via Async Subprocess): ")
    print(command)

    # Redirigimos stderr a stdout igual que en tu versión síncrona
    process = await asyncio.create_subprocess_exec(
        command[0],
        *command[1:],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,  # Fusiona canales cronológicamente
        cwd=cwd,
    )

    captured_output = []

    # Leemos línea por línea en tiempo real de forma asíncrona
    if process.stdout:
        async for line_bytes in process.stdout:
            # Decodificamos ignorando errores tal como tu versión síncrona
            line = line_bytes.decode(errors="ignore")
            captured_output.append(line)

            if show_live_output:
                sys.stdout.write(line)
                sys.stdout.flush()

    await process.wait()
    full_output = "".join(captured_output)

    if process.returncode != 0:
        # print("\n" + "=" * 50)
        # print("DETAILED ERROR OUTPUT:")
        # print("=" * 50)
        # print(full_output.strip())
        # print("=" * 50 + "\n")

        raise subprocess.CalledProcessError(
            returncode=process.returncode,
            cmd=command,
            output=full_output,
            stderr="",
        )

    print("\nSuccess command call via Async Subprocess")
    return full_output
