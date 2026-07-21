import socket
import struct
from pathlib import Path


UDP_HOST = "127.0.0.1"
UDP_PORT = 6001
OUTPUT_DIR = Path("received_files")

MAGIC = b"MQAM"


def receive_file() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Aumenta el buffer para archivos más grandes.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)

    sock.bind((UDP_HOST, UDP_PORT))

    print(f"Esperando datos en UDP {UDP_HOST}:{UDP_PORT}...")

    received = bytearray()
    header_reported = False

    while True:
        packet, _ = sock.recvfrom(65535)

        if not packet:
            continue

        received.extend(packet)

        # Busca la cabecera dentro del flujo. Los bytes de entrenamiento
        # o los transitorios iniciales pueden aparecer antes de MAGIC.
        start = received.find(MAGIC)

        if start < 0:
            # Evita crecimiento ilimitado si todavía no aparece MAGIC.
            # Conservamos los últimos bytes por si la firma queda dividida.
            if len(received) > 4 * 1024 * 1024:
                del received[:-32]
            continue

        # MAGIC(4) + VERSION(1) + NAME_LEN(1) + FILE_SIZE(8)
        minimum_header = 14

        if len(received) < start + minimum_header:
            continue

        version = received[start + 4]
        name_len = received[start + 5]

        file_size = struct.unpack(
            "!Q",
            received[start + 6 : start + 14]
        )[0]

        header_end = start + 14 + name_len

        if len(received) < header_end:
            continue

        try:
            file_name = received[start + 14 : header_end].decode("utf-8")
        except UnicodeDecodeError:
            print("Se detectó una cabecera inválida; buscando otra firma MQAM.")
            del received[: start + 1]
            header_reported = False
            continue

        # Validaciones para evitar aceptar una firma MQAM accidental.
        if version != 1:
            del received[: start + 1]
            header_reported = False
            continue

        if name_len == 0 or file_size > 2 * 1024 * 1024 * 1024:
            del received[: start + 1]
            header_reported = False
            continue

        if not header_reported:
            print(f"Cabecera detectada:")
            print(f"  Archivo: {file_name}")
            print(f"  Tamaño esperado: {file_size} bytes")
            header_reported = True

        file_end = header_end + file_size

        if len(received) < file_end:
            current = max(0, len(received) - header_end)
            percent = min(100.0, 100.0 * current / file_size) if file_size else 100
            print(
                f"\rRecibiendo: {current}/{file_size} bytes "
                f"({percent:.1f}%)",
                end="",
                flush=True,
            )
            continue

        file_data = bytes(received[header_end:file_end])

        # Path.name evita que el nombre recibido escriba fuera del directorio.
        safe_name = Path(file_name).name
        output_path = OUTPUT_DIR / safe_name
        output_path.write_bytes(file_data)

        print()
        print(f"Archivo recibido: {output_path.resolve()}")
        print(f"Tamaño recibido: {len(file_data)} bytes")
        return


if __name__ == "__main__":
    try:
        receive_file()
    except KeyboardInterrupt:
        print("\nRecepción cancelada.")