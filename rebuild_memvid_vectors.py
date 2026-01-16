#!/usr/bin/env python3
"""
Ricostruisce il file Memvid con ricerca vettoriale abilitata.
Usa embeddings locali (nessuna API key richiesta).
"""

import os
import re
from pathlib import Path
from datetime import datetime
import memvid_sdk

# Configurazione
JOURNAL_DIR = Path(__file__).parent / "journal"
OUTPUT_FILE = Path(__file__).parent / "reminor_memory_vec.mv2"
OLD_FILE = Path(__file__).parent / "reminor_memory.mv2"

def rebuild_with_vectors():
    print("=" * 60)
    print("  RICOSTRUZIONE MEMVID CON RICERCA VETTORIALE")
    print("=" * 60)

    # Rimuovi file esistente se presente
    if OUTPUT_FILE.exists():
        print(f"\nRimuovo file esistente: {OUTPUT_FILE}")
        OUTPUT_FILE.unlink()

    # Crea nuovo file con ENTRAMBI gli indici abilitati
    print("\n1. Creazione file Memvid con vettori...")
    print("   enable_lex=True (BM25)")
    print("   enable_vec=True (Embeddings)")

    try:
        mem = memvid_sdk.create(
            str(OUTPUT_FILE),
            enable_lex=True,   # BM25 per ricerca testuale
            enable_vec=True    # Vettori per ricerca semantica
        )
        print("   File creato con successo!")
    except Exception as e:
        print(f"   ERRORE creazione: {e}")
        return False

    # Carica tutti i file .txt
    print("\n2. Caricamento file diario...")
    documents = []

    for file_path in sorted(JOURNAL_DIR.glob("*.txt")):
        if file_path.name.startswith("."):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                continue

            # Estrai data dal nome file
            date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', file_path.name)
            if date_match:
                entry_date = datetime(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3))
                )
            else:
                entry_date = datetime.now()

            date_str = entry_date.strftime("%Y-%m-%d")

            doc = {
                "title": f"Diario {date_str}",
                "label": "diary",
                "text": content,
                "metadata": {"date": date_str, "filename": file_path.name},
                "tags": ["diario"],
                "timestamp": int(entry_date.timestamp())
            }
            documents.append(doc)

        except Exception as e:
            print(f"   Errore file {file_path.name}: {e}")

    print(f"   Trovati {len(documents)} documenti")

    # Inserisci documenti (gli embeddings vengono calcolati automaticamente)
    print("\n3. Inserimento documenti con calcolo embeddings...")
    print("   (questo potrebbe richiedere qualche secondo)")

    try:
        frame_ids = mem.put_many(documents)
        print(f"   Inseriti {len(frame_ids)} documenti")
    except Exception as e:
        print(f"   ERRORE inserimento: {e}")
        mem.close()
        return False

    # Finalizza
    print("\n4. Finalizzazione file...")
    try:
        mem.seal()
        print("   File sigillato")
    except Exception as e:
        print(f"   ERRORE seal: {e}")

    # Statistiche
    print("\n5. Statistiche finali:")
    stats = mem.stats()
    print(f"   Frame: {stats.get('frame_count', 'N/A')}")
    print(f"   Size: {stats.get('size_bytes', 0)/1024:.1f} KB")
    print(f"   Lex index: {stats.get('lex_index', 'N/A')}")
    print(f"   Vec index: {stats.get('vec_index', 'N/A')}")

    mem.close()

    # Test rapido
    print("\n6. Test ricerca semantica...")
    mem = memvid_sdk.use("basic", str(OUTPUT_FILE))

    test_queries = ["il mio cane", "vacanza mare", "lavoro ufficio"]
    for query in test_queries:
        results = mem.find(query, k=2)
        hits = results.get('hits', [])
        print(f"\n   Query: '{query}'")
        for hit in hits[:2]:
            title = hit.get('title', 'N/A')
            score = hit.get('score', 0)
            print(f"   → {title} (score: {score:.2f})")

    mem.close()

    print("\n" + "=" * 60)
    print("  RICOSTRUZIONE COMPLETATA!")
    print("=" * 60)
    print(f"\nNuovo file: {OUTPUT_FILE}")
    print(f"Dimensione: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    return True

if __name__ == "__main__":
    success = rebuild_with_vectors()
    if not success:
        print("\nRicostruzione fallita. Controlla gli errori sopra.")
