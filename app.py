from korg.midi import midi_to_note, note_to_midi
from korg.set_parser import KorgSetParser


def inspect_set_file():
    path = input("Unesi putanju do Korg .SET datoteke: ").strip()

    try:
        parser = KorgSetParser(path)

        info = parser.inspect()

        print()
        print("Korg SET Inspector")
        print("-" * 30)
        print(f"Datoteka: {info['path']}")
        print(f"Veličina: {info['size']} bytes")
        print(f"Preview:  {info['preview_size']} bytes")

        print()
        print("HEX preview:")
        print(info["hex"])

        strings = parser.find_ascii_strings()

        print()
        print(f"ASCII stringovi pronađeni: {len(strings)}")

        for index, value in enumerate(strings[:50], start=1):
            print(f"{index:3}: {value}")

        if len(strings) > 50:
            print(f"... i još {len(strings) - 50}")

    except (FileNotFoundError, ValueError) as error:
        print(f"Greška: {error}")


def main():
    print("Korg PA300 Drum Kit Editor")
    print("=" * 30)

    while True:
        print()
        print("1 - MIDI broj -> nota")
        print("2 - Nota -> MIDI broj")
        print("3 - Inspect Korg SET")
        print("0 - Izlaz")

        choice = input("Odaberi: ").strip()

        if choice == "0":
            break

        if choice == "1":
            value = input("Unesi MIDI broj (0-127): ").strip()

            try:
                midi_note = int(value)
                print(f"MIDI {midi_note} = {midi_to_note(midi_note)}")
            except ValueError as error:
                print(f"Greška: {error}")

        elif choice == "2":
            value = input("Unesi notu (npr. C1, D#1, F#2): ").strip()

            try:
                midi_note = note_to_midi(value)
                print(f"{value.upper()} = MIDI {midi_note}")
            except ValueError as error:
                print(f"Greška: {error}")

        elif choice == "3":
            inspect_set_file()

        else:
            print("Nepoznata opcija.")


if __name__ == "__main__":
    main()
