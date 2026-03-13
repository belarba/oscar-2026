# Oscar 2025 — Os dados por trás da 97ª cerimônia

Site interativo com duas visualizações sobre o Oscar 2025:

**Crítica vs Público** — Scatter plot cruzando notas do Rotten Tomatoes (crítica) com IMDb (público) dos indicados a Melhor Filme, Diretor, Ator e Atriz. Identifica o filme mais consensual, mais divisivo, superestimado e subestimado pela crítica.

**O Brasil no Oscar** — Timeline de todas as 55 submissões brasileiras ao prêmio de Melhor Filme Internacional desde 1960, incluindo a vitória histórica de *Ainda Estou Aqui* (2025).

## Stack

- Python 3.9+
- pandas, plotly, jinja2, requests, beautifulsoup4
- GitHub Pages (hospedagem)

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/scrape_brasil_oscar.py   # Scraping Wikipedia
python scripts/process_ratings.py       # Processar dados
python scripts/build_site.py            # Gerar site em docs/
```

O site final fica em `docs/index.html`.

## Estrutura

```
data/manual/ratings.csv       — Notas RT/IMDb (compiladas manualmente)
data/raw/brasil_oscar.csv     — Scraping Wikipedia
data/processed/               — Dados processados
scripts/                      — Pipeline (scrape → process → build)
templates/index.html          — Template Jinja2 com toggle claro/escuro
docs/index.html               — Site gerado (GitHub Pages)
```

## Fontes de dados

- [Wikipedia — Brazilian submissions for Best International Feature Film](https://en.wikipedia.org/wiki/List_of_Brazilian_submissions_for_the_Academy_Award_for_Best_International_Feature_Film)
- [Rotten Tomatoes](https://www.rottentomatoes.com/)
- [IMDb](https://www.imdb.com/)
