#!/usr/bin/env python3
"""
Script per convertire i file di diario in formato Memvid (.mv2)
"""

import os
import re
from pathlib import Path
from datetime import datetime
import memvid_sdk

# Configurazione
JOURNAL_DIR = Path(__file__).parent / "journal"
OUTPUT_FILE = Path(__file__).parent / "reminor_memory.mv2"

def parse_date_from_filename(filename: str) -> datetime:
    """Estrae la data dal nome del file (es. 2025-05-21.txt)"""
    match = re.match(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return datetime.now()

def main():
    print("=" * 60)
    print("  CONVERSIONE DIARIO REMINOR -> MEMVID V2")
    print("=" * 60)

    # Trova tutti i file .txt del diario (escludi _emotions.json)
    journal_files = sorted([
        f for f in JOURNAL_DIR.glob("*.txt")
        if f.is_file() and not f.name.startswith(".")
    ])

    print(f"\nTrovati {len(journal_files)} file di diario")

    # Rimuovi file .mv2 esistente se presente
    if OUTPUT_FILE.exists():
        os.remove(OUTPUT_FILE)
        print(f"Rimosso file esistente: {OUTPUT_FILE}")

    # Crea nuovo file Memvid con indici lexical e vector
    print(f"\nCreazione file Memvid: {OUTPUT_FILE}")
    mem = memvid_sdk.create(
        str(OUTPUT_FILE),
        enable_lex=True,   # Indice full-text BM25
        enable_vec=False   # Vector index (richiede embedding provider esterno)
    )

    # Prepara i documenti per batch insert
    documents = []
    skipped = 0

    for file_path in journal_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            # Salta file vuoti
            if not content:
                skipped += 1
                continue

            # Estrai data dal nome file
            entry_date = parse_date_from_filename(file_path.name)
            date_str = entry_date.strftime("%Y-%m-%d")
            timestamp = int(entry_date.timestamp())

            # Prepara documento per Memvid
            doc = {
                "title": f"Diario {date_str}",
                "label": "diary",
                "text": content,
                "metadata": {
                    "date": date_str,
                    "source": "reminor",
                    "filename": file_path.name
                },
                "tags": ["diario", "personale"],
                "timestamp": timestamp
            }
            documents.append(doc)

        except Exception as e:
            print(f"  Errore nel file {file_path.name}: {e}")
            skipped += 1

    print(f"\nDocumenti da inserire: {len(documents)}")
    print(f"File saltati (vuoti o errori): {skipped}")

    # Batch insert (100x più veloce di insert singoli)
    if documents:
        print("\nInserimento batch in corso...")
        frame_ids = mem.put_many(documents)
        print(f"Inseriti {len(frame_ids)} frame")

    # Finalizza e chiudi
    print("\nFinalizzazione...")
    mem.seal()
    mem.close()

    # Verifica statistiche
    print("\n" + "=" * 60)
    print("  CONVERSIONE COMPLETATA")
    print("=" * 60)

    # Riapri per statistiche
    mem = memvid_sdk.use("basic", str(OUTPUT_FILE))
    stats = mem.stats()

    print(f"\nStatistiche file {OUTPUT_FILE.name}:")
    if hasattr(stats, 'frame_count'):
        print(f"  - Frame totali: {stats.frame_count}")
        print(f"  - Indice lexical: {'attivo' if stats.lex_enabled else 'disattivo'}")
        print(f"  - Indice vector: {'attivo' if stats.vec_enabled else 'disattivo'}")
    else:
        # stats è un dizionario
        print(f"  - Statistiche: {stats}")
    print(f"  - Dimensione file: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    mem.close()

    print("\n✓ File pronto per l'uso con Reminor!")
    return str(OUTPUT_FILE)

if __name__ == "__main__":
    main()
