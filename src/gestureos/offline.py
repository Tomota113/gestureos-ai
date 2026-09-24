"""Guided, entirely local gesture collection using the existing serial logger."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import uuid

from .capture import CaptureStore, collect, write_json
from .dataset import fingerprint, load_capture, read_object, require
from .protocol import LABEL, PATH_COMPONENT, PROTOCOL, Request

DESCRIPTIONS = {
    "swipe_left": "Gauche", "swipe_right": "Droite", "swipe_up": "Haut",
    "swipe_down": "Bas", "circle_clockwise": "Cercle horaire", "shake": "Secousse",
    "unknown": "Autre mouvement / repos (aucun des six gestes)",
}
RAW_FILES = ("request.json", "serial.raw", "samples.csv", "result.json")


def configuration(path):
    config = read_object(path.read_bytes())
    require(config["protocol"] == PROTOCOL and config["baudrate"] == 230400, "Configuration série incompatible")
    labels = config["labels"]
    require(isinstance(labels, list) and labels and all(isinstance(x, str) and LABEL.fullmatch(x) for x in labels)
            and len(set(labels)) == len(labels), "Liste de gestes invalide")
    Request("0" * 32, labels[0], config["samples_per_capture"], config["sample_rate_hz"])
    require(type(config["countdown_seconds"]) is int and 0 <= config["countdown_seconds"] <= 10,
            "Compte à rebours invalide")
    return config


def usb_ports():
    from serial.tools import list_ports
    return [port for port in list_ports.comports()
            if port.vid is not None or port.device.startswith(("/dev/ttyUSB", "/dev/ttyACM"))]


def session_counts(root, subject, session, labels):
    counts = dict.fromkeys(labels, 0)
    invalid = 0
    for directory in sorted((root / subject / session).glob("*")):
        if not directory.is_dir():
            continue
        try:
            entry = load_capture(directory, root, labels)
            counts[entry["label"]] += 1
        except (OSError, ValueError, KeyError, TypeError):
            invalid += 1
    return counts, invalid


def publish_capture(directory, pending_root, raw_root, labels):
    """Copy a reviewed capture exclusively, retaining the original pending evidence."""
    entry = load_capture(directory, pending_root, labels)
    # Read and check snapshots before creating the destination. The source stays intact.
    files = {name: (directory / name).read_bytes() for name in RAW_FILES}
    require(all(fingerprint(data) == entry["file_sha256"][name] for name, data in files.items()),
            "La capture a changé pendant sa validation")
    destination = raw_root / entry["path"]
    destination.mkdir(parents=True, exist_ok=False)
    for name in RAW_FILES:  # result.json is published last
        with (destination / name).open("xb") as stream:
            stream.write(files[name])
            stream.flush()
            import os
            os.fsync(stream.fileno())
    write_json(destination / "human_review.json", {"schema_version": 1, "decision": "accepted",
               "capture_id": entry["capture_id"], "label": entry["label"],
               "reviewed_utc": datetime.now(timezone.utc).isoformat()})
    return destination


def run_session(port, subject, session, data_root, config, *, ask=input):
    require(all(PATH_COMPONENT.fullmatch(x) for x in (subject, session)),
            "Sujet/session : lettres, chiffres, tirets ou underscores seulement (1..64 caractères)")
    labels = config["labels"]
    data_root = data_root.resolve()
    raw_root, pending_root = data_root / "raw", data_root / "pending"
    print(f"\nSujet : {subject} | Séance : {session}\nDonnées : {data_root}")
    print("Aucun Wi-Fi requis. Un geste par prise, au signal GO. q pour quitter.")
    notes = ask("Position du capteur / main / repère / remarques de cette séance : ").strip()
    note_folder = data_root / "session_notes" / subject / session
    note_folder.mkdir(parents=True, exist_ok=True)
    write_json(note_folder / f"{uuid.uuid4().hex}.json", {
        "schema_version": 1, "subject": subject, "session": session, "notes": notes,
        "created_utc": datetime.now(timezone.utc).isoformat(), "collection_config": config})
    while True:
        counts, invalid = session_counts(raw_root, subject, session, labels)
        print("\nChoisis le geste à enregistrer :")
        for i, label in enumerate(labels, 1):
            print(f"  {i}. {DESCRIPTIONS.get(label, label)} — {counts[label]} prise(s) validée(s)")
        if invalid:
            print(f"Attention : {invalid} dossier(s) RAW invalide(s), conservé(s) pour diagnostic.")
        choice = ask("Numéro du geste, ou q : ").strip().lower()
        if choice == "q":
            print(f"Séance conservée dans {data_root}. Tu peux fermer le terminal.")
            return 0
        if not choice.isdigit() or not 1 <= int(choice) <= len(labels):
            print("Choix invalide ; aucune capture lancée.")
            continue
        label = labels[int(choice) - 1]
        request = Request(uuid.uuid4().hex, label, config["samples_per_capture"], config["sample_rate_hz"])
        print(f"Prépare {DESCRIPTIONS.get(label, label)}. Durée : environ {request.samples/request.rate_hz:g} s.")
        store = CaptureStore(pending_root, subject, session, request)
        result = collect(port, store, countdown=config["countdown_seconds"])
        if result["status"] != "complete":
            print(f"ÉCHEC : {result['error']}\nLog conservé : {store.path}\nPas ajouté aux données d’entraînement.")
            continue
        review = ask("As-tu fait le bon geste pendant GO, sans incident ? [o=oui / n=non / q=quitter] : ").strip().lower()
        if review == "o":
            destination = publish_capture(store.path, pending_root, raw_root, labels)
            write_json(store.path / "review.json", {"decision": "accepted", "published_to": str(destination)})
            print(f"ENREGISTRÉ : {destination}")
        else:
            write_json(store.path / "review.json", {"decision": "not_accepted", "response": review})
            print("Prise conservée dans pending, exclue du dossier RAW d’entraînement. Tu peux la refaire.")
            if review == "q":
                return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="USB serial port; otherwise choose from detected USB ports")
    parser.add_argument("--subject", help="Pseudonym, e.g. user01")
    parser.add_argument("--session", help="Existing session to resume; a new ID is generated by default")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--config", type=Path, default=Path("configs/collection.json"))
    parser.add_argument("--check", action="store_true", help="Check local software/USB without opening a port")
    args = parser.parse_args()
    try:
        config = configuration(args.config)
        import serial
        ports = usb_ports()
        if args.check:
            print(f"Logiciel de collecte prêt localement ; pyserial {serial.__version__} ; {len(config['labels'])} labels.")
            print("Ports USB : " + (", ".join(p.device for p in ports) or "aucun détecté (matériel non testé)"))
            print("Aucun accès réseau, aucune ouverture du port, aucun flashage.")
            return 0
        port = args.port
        if not port:
            if not ports:
                print("Aucun port USB détecté. Branche l’ESP32 avec un câble de données, puis relance.")
                return 1
            for i, item in enumerate(ports, 1):
                print(f"{i}. {item.device} — {item.description}")
            selection = input("Port USB [1] : ").strip() or "1"
            require(selection.isdigit() and 1 <= int(selection) <= len(ports), "Port invalide")
            port = ports[int(selection) - 1].device
        subject = args.subject or input("Ton identifiant (sans nom complet) [user01] : ").strip() or "user01"
        session = args.session or datetime.now().strftime("session_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:4]
        return run_session(port, subject, session, args.data_root, config)
    except (EOFError, KeyboardInterrupt):
        print("\nArrêt demandé. Les captures restent sur disque ; une prise non confirmée reste dans pending.")
        return 130
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        parser.exit(2, f"Collecte arrêtée : {exc}\nLes fichiers existants sont conservés.\n")


if __name__ == "__main__":
    raise SystemExit(main())
