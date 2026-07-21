import os
import socket
import struct
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog


UDP_HOST = "127.0.0.1"
UDP_PORT = 6000
CHUNK_SIZE = 512

MAGIC = b"MQAM"
VERSION = 1


def send_file(file_path: str) -> None:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    file_name = path.name.encode("utf-8")
    file_size = path.stat().st_size

    if len(file_name) > 255:
        raise ValueError("El nombre del archivo es demasiado largo")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Cabecera:
    # MAGIC       4 bytes
    # VERSION     1 byte
    # NAME_LEN    1 byte
    # FILE_SIZE   8 bytes
    # FILE_NAME   variable
    header = (
        MAGIC
        + struct.pack("!B", VERSION)
        + struct.pack("!B", len(file_name))
        + struct.pack("!Q", file_size)
        + file_name
    )

    print(f"Enviando: {path}")
    print(f"Tamaño: {file_size} bytes")
    print(f"Destino UDP: {UDP_HOST}:{UDP_PORT}")

    # Preámbulo de entrenamiento.
    training = bytes(range(256)) * 16

    # Relleno final para vaciar los filtros.
    padding = bytes(range(256)) * 16

    payload = training + header + path.read_bytes() + padding

    sent = 0

    while sent < len(payload):
        chunk = payload[sent : sent + CHUNK_SIZE]

        # Se envía únicamente el contenido del flujo.
        # GNU Radio no conserva los límites originales de los datagramas.
        sock.sendto(chunk, (UDP_HOST, UDP_PORT))

        sent += len(chunk)

        # Pausa pequeña para evitar desbordar los buffers UDP.
        time.sleep(0.01)

    print("Transmisión finalizada.")


def main() -> None:
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Seleccione una imagen o archivo de texto",
        filetypes=[
            ("Imagenes y textos", "*.png *.jpg *.jpeg *.bmp *.txt"),
            ("Imagenes", "*.png *.jpg *.jpeg *.bmp"),
            ("Textos", "*.txt"),
            ("Todos los archivos", "*.*"),
        ],
    )

    root.destroy()

    if not file_path:
        print("No se selecciono ningun archivo.")
        return

    try:
        send_file(file_path)
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()