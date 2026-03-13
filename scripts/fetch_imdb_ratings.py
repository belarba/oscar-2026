"""
Busca ratings do IMDb para os filmes listados no CSV de ratings.
Atualiza a coluna imdb_score no CSV manual.

Uso:
    python scripts/fetch_imdb_ratings.py

Nota: O scraping do IMDb pode quebrar se a estrutura HTML mudar.
      Nesse caso, atualize manualmente o data/manual/ratings.csv.
"""

import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MANUAL_DIR = BASE_DIR / "data" / "manual"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def search_imdb(title: str) -> dict | None:
    """Busca um filme no IMDb e retorna título, rating e URL."""
    query = title.replace(" ", "+")
    url = f"https://www.imdb.com/find/?q={query}&s=tt&ttype=ft"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Erro ao buscar '{title}': {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Procura o primeiro resultado de filme
    results = soup.select('a[href*="/title/tt"]')
    if not results:
        print(f"  Nenhum resultado para '{title}'")
        return None

    # Pega o link do primeiro resultado
    first = results[0]
    href = first.get("href", "")
    match = re.search(r"/title/(tt\d+)", href)
    if not match:
        return None

    imdb_id = match.group(1)
    return fetch_rating(imdb_id, title)


def fetch_rating(imdb_id: str, title: str) -> dict | None:
    """Busca o rating de um filme pelo ID do IMDb."""
    url = f"https://www.imdb.com/title/{imdb_id}/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Erro ao buscar rating de '{title}': {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Tenta extrair o rating do JSON-LD
    script = soup.find("script", type="application/ld+json")
    if script:
        import json
        try:
            data = json.loads(script.string)
            rating = data.get("aggregateRating", {}).get("ratingValue")
            if rating:
                return {
                    "imdb_id": imdb_id,
                    "imdb_score": float(rating),
                    "title": data.get("name", title),
                }
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: procura no HTML
    rating_el = soup.select_one('[data-testid="hero-rating-bar__aggregate-rating__score"] span')
    if rating_el:
        try:
            return {
                "imdb_id": imdb_id,
                "imdb_score": float(rating_el.text),
                "title": title,
            }
        except ValueError:
            pass

    print(f"  Rating não encontrado para '{title}'")
    return None


def main():
    csv_path = MANUAL_DIR / "ratings.csv"
    df = pd.read_csv(csv_path)

    # Pega filmes únicos (pelo nome em inglês)
    filmes = df["filme_en"].unique()

    print(f"Buscando ratings do IMDb para {len(filmes)} filmes...\n")

    ratings = {}
    for filme in filmes:
        print(f"  Buscando: {filme}...")
        result = search_imdb(filme)
        if result:
            ratings[filme] = result["imdb_score"]
            print(f"    → IMDb: {result['imdb_score']}")
        else:
            print(f"    → Não encontrado, mantendo valor atual")
        time.sleep(1.5)  # Respeita rate limit

    # Atualiza o CSV
    updated = 0
    for filme_en, score in ratings.items():
        mask = df["filme_en"] == filme_en
        old_score = df.loc[mask, "imdb_score"].values[0]
        if old_score != score:
            df.loc[mask, "imdb_score"] = score
            updated += 1
            print(f"\n  Atualizado: {filme_en} ({old_score} → {score})")

    if updated > 0:
        df.to_csv(csv_path, index=False)
        print(f"\n{updated} filmes atualizados em {csv_path}")
    else:
        print("\nNenhuma atualização necessária.")

    print("\nNota: RT scores devem ser atualizados manualmente no CSV.")
    print("Consulte: https://www.rottentomatoes.com/")


if __name__ == "__main__":
    main()
