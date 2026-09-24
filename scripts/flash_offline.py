"""Install cached ESP32 images without download/build, retaining a full flash backup."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

PROJECT = Path(__file__).resolve().parents[1]
PLATFORM = Path.home() / ".platformio"
PYTHON = PLATFORM / "penv/bin/python"
ESPTOOL = PLATFORM / "packages/tool-esptoolpy/esptool.py"


def image_path(profile):
    folder = PROJECT / "outputs/firmware-offline"
    manifest = json.loads((folder / "manifest.json").read_text())
    entry = manifest["images"][profile]
    if manifest["chip"] != "esp32" or manifest["flash_size_bytes"] != 4194304 or entry["offset"] != 0:
        raise ValueError("Profil attendu : ESP32 classique, Flash 4 Mo, image à offset0")
    if entry["file"] != f"{profile}.bin":
        raise ValueError("Nom d’image inattendu")
    path = folder / entry["file"]
    data = path.read_bytes()
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise ValueError("Empreinte du firmware incorrecte")
    if not PYTHON.is_file() or not ESPTOOL.is_file():
        raise ValueError("Outil esptool local manquant ; ne pas partir avant de le restaurer")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=("bench", "dataset"))
    parser.add_argument("--port")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        firmware = image_path(args.profile)
        if args.check:
            subprocess.run([str(PYTHON), str(ESPTOOL), "version"], check=True)
            print(f"Image {args.profile} et outil local disponibles. Aucun accès au matériel.")
            return 0
        if not args.port:
            parser.error("--port est requis pour installer le firmware")
        print("ESP32 classique 4 Mo uniquement. Lire le guide de câblage avant mise sous tension.")
        print(f"Programme à installer : {args.profile}. Port : {args.port}.")
        print("Une sauvegarde complète de la Flash précédera l’écriture. Aucun téléchargement.")
        if input("Tape INSTALLER pour remplacer le programme de cette carte : ").strip() != "INSTALLER":
            print("Annulé.")
            return 0
        folder = PROJECT / "backups" / (datetime.now().strftime("flash_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8])
        folder.mkdir(parents=True, exist_ok=False)
        backup = folder / "before.bin"
        base = [str(PYTHON), str(ESPTOOL), "--chip", "esp32", "--port", args.port, "--baud", "115200"]
        subprocess.run(base + ["read_flash", "0", "0x400000", str(backup)], check=True)
        if backup.stat().st_size != 4194304:
            raise ValueError("Sauvegarde Flash incomplète ; écriture annulée")
        with (folder / "backup.json").open("x") as stream:
            json.dump({"sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
                       "bytes": backup.stat().st_size, "port": args.port, "next_profile": args.profile}, stream, indent=2)
        subprocess.run(base + ["write_flash", "--flash_mode", "dio", "--flash_freq", "40m",
                              "--flash_size", "4MB", "0x0", str(firmware)], check=True)
        print(f"Firmware installé. Ancienne Flash conservée : {backup}")
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Installation arrêtée : {exc}\nLes sauvegardes et logs existants sont conservés.\n")
    except (KeyboardInterrupt, EOFError):
        parser.exit(130, "\nInterrompu. Conserver le dossier backups.\n")


if __name__ == "__main__":
    raise SystemExit(main())
