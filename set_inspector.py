from pathlib import Path


def inspect_set(set_path: str | Path) -> None:
    """
    Osnovni binarni inspektor za Korg PA300 .SET datoteku.

    Ne pokušava još interpretirati podatke.
    Samo prikazuje osnovne informacije i početne bajtove.
    """

    path = Path(set_path)

    if not path.exists():
        raise FileNotFoundError(f"SET file does not exist: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() != ".set":
        raise ValueError("Expected a Korg .SET file")

    data = path.read_bytes()

    print("=" * 60)
    print("KORG PA300 SET INSPECTOR")
    print("=" * 60)

    print(f"File: {path.name}")
    print(f"Size: {len(data)} bytes")
    print()

    print("First 256 bytes:")
    print("-" * 60)

    preview = data[:256]

    for offset in range(0, len(preview), 16):
        chunk = preview[offset:offset + 16]

        hex_data = " ".join(f"{byte:02X}" for byte in chunk)

        ascii_data = "".join(
            chr(byte) if 32 <= byte <= 126 else "."
            for byte in chunk
        )

        print(
            f"{offset:08X}  "
            f"{hex_data:<47}  "
            f"|{ascii_data}|"
        )

    print()
    print("=" * 60)


def main() -> None:
    print("Korg PA300 SET Inspector")
    print()

    value = input("Unesi putanju do .SET datoteke: ").strip()

    try:
        inspect_set(value)
    except (FileNotFoundError, ValueError) as error:
        print(f"Greška: {error}")


if __name__ == "__main__":
    main()
