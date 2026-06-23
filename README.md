# 🛠️ disk-recovery-cli

> A command-line tool for salvaging data from partially corrupted hard drives — reading block by block, surviving I/O errors, and producing a full SHA-256 integrity report.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-brightgreen)]()

---

## 📋 Table of Contents
- [Motivation](#-motivation)
- [Features](#-features)
- [How it works](#-how-it-works)
- [Installation](#-installation)
- [Usage](#-usage)
- [Output example](#-output-example)
- [Testing](#-testing)
- [Project structure](#-project-structure)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🎯 Motivation
Standard copy tools (`cp`, Finder, Windows Explorer) share a fatal flaw: they **abort on the first I/O error**, leaving you with nothing. After personally losing data during a file transfer from a failing drive, I built `disk-recovery-cli` to solve exactly this. When a bad sector is hit, the tool pads the block with null bytes, records the event, and **keeps going** — because a partial file is almost always better than no file.

---

## ✨ Features
- **Block-by-block recovery** via raw POSIX syscalls (`os.read` / `os.write` / `os.lseek`)
- **Hardware fault isolation** — catches `errno.EIO` per block without aborting the entire file
- **Three recovery states** per file: `SAIN` (intact), `PARTIEL` (bad sectors patched), `ERREUR` (unreadable)
- **SHA-256 integrity hashing** of every recovered file, including null-padded sectors
- **`rapport_hashes.txt`** — a verifiable checksum manifest in the destination, compatible with `sha256sum -c`
- **Live progress bar** via `tqdm`
- **Final statistics report** with per-status counts and global recovery rate
- **Configurable block size** via `--block-size` CLI flag

---

## 🔬 How it works
The recovery pipeline runs in two phases:

```text
Phase 1 — Pre-Scan
└── os.walk() traverses the full source tree
    and collects all file paths before touching anything.

Phase 2 — Block-by-block copy (per file)
├── Opens source and destination with raw file descriptors
├── Reads in chunks of block_size bytes
│   ├── Success → write block, update SHA-256 hasher
│   └── EIO → write null bytes, lseek past bad block,
│       mark file as PARTIEL, continue
└── Fatal OSError → mark ERREUR, move to next file
```

Using os.lseek(..., os.SEEK_CUR) to skip past a bad sector mirrors the behaviour of professional tools like ddrescue, keeping the output file structurally coherent with the original.

## 📦 Installation

```Bash
git clone [https://github.com/nbkrcode/disk-recovery-cli.git](https://github.com/nbkrcode/disk-recovery-cli.git)
cd disk-recovery-cli
pip install -r requirements.txt
```

tqdm is the only external dependency. Python 3.8+ required.

## 🚀 Usage

```Bash
python recovery.py <source> <destination> [--block-size <bytes>]
```

Argument	Description
source	Path to the corrupted drive or directory
destination	Path to the healthy destination directory
-b, --block-size	Read block size in bytes (default: 4096)
Examples:

```Bash
# Standard recovery from an external drive (macOS)
python recovery.py /Volumes/CorruptedDrive /Volumes/Backup

# Finer granularity for heavily fragmented sectors
python recovery.py /Volumes/CorruptedDrive /Volumes/Backup --block-size 512

# Larger blocks for faster reads on lightly damaged media
python recovery.py /dev/sdb1 /mnt/rescue --block-size 65536
```

⚠️ Always run as a read-only operation on the source — never write to the failing drive. Use a healthy destination on a separate device.

## 📊 Output example

```Plaintext
[1/2] Analyse du dossier source en cours : /Volumes/CorruptedDrive
-> 312 fichiers trouvés.
[2/2] Démarrage de la récupération vers : /Volumes/Backup
Récupération: 100%|████████████████████| 312/312 [02:14<00:00, 2.32fichier/s]

==================================================
📊 RAPPORT DE RÉCUPÉRATION
Total des fichiers traités : 312
✅ Fichiers copiés 100% intacts : 289
⚠️ Fichiers sauvés partiellement : 17 (Secteurs défectueux ignorés)
❌ Fichiers totalement perdus : 6
Taux de récupération global : 98.08%
```

The rapport_hashes.txt file written to the destination lists the SHA-256 checksum of every recovered file, including null-padded ones, for post-recovery verification:
```Plaintext
a3f1c8... documents/thesis.pdf
00e2b4... photos/2023/IMG_0042.jpg
...
```

## 🧪 Testing

test_corruption.py validates bad-sector handling without any physical hardware by using unittest.mock.patch to inject an OSError(EIO) on the second os.read call.

```Bash
python test_corruption.py
```

Expected output:

```Plaintext
--- CRÉATION DU FICHIER TEST ---
--- DÉMARRAGE DE LA RÉCUPÉRATION ---
Simulation du crash secteur...
--- RÉSULTAT DU TEST ---
Statut final : PARTIEL
Empreinte SHA-256 : <deterministic hash>
Contenu récupéré : b'AAAAAAAAAA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00CCCCCCCCCC'
```

The null-padded middle block confirms that bad-sector isolation works correctly: the first and third blocks are intact, and the corrupted second block is replaced with zeros rather than crashing the process.

## 📁 Project structure

```Plaintext
disk-recovery-cli/
├── recovery.py           # Core recovery engine + CLI entry point
├── test_corruption.py    # Hardware fault simulation via mock injection
├── requirements.txt      # External dependencies (tqdm)
└── README.md
```

## 🗺️ Roadmap
- [ ] Rust rewrite — in progress, targeting memory safety and zero-copy I/O performance
- [ ] --dry-run mode — estimate recoverability without writing to disk
- [ ] JSON/CSV output for machine-readable recovery reports
- [ ] Retry logic with configurable attempts per bad sector
- [ ] Parallel file recovery using concurrent.futures

## 📄 License

MIT © nbkrcode