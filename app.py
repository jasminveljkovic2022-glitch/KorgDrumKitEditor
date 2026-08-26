from korg.midi import midi_to_note, note_to_midi


def main():
    print("Korg PA300 Drum Kit Editor")
    print("=" * 30)

    while True:
        print()
        print("1 - MIDI broj -> nota")
        print("2 - Nota -> MIDI broj")
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

        else:
            print("Nepoznata opcija.")


if __name__ == "__main__":
    main()
