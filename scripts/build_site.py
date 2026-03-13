"""
Build script: lê dados processados, gera gráficos Plotly e monta o site final.
Output: docs/index.html (pronto para GitHub Pages)
"""

import pandas as pd
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TEMPLATES_DIR = BASE_DIR / "templates"
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Paleta Oscar
COLORS = {
    "accent": "#c9a84c",
    "accent_light": "#e8d48b",
    "accent_dark": "#a07d2e",
    "gold": "#d4af37",
    "red": "#cd5c5c",
    "green": "#6bbd6b",
    "bg_dark": "#1a1a1a",
    "bg_chart_dark": "#0f1a30",
    "text_dark": "#8a7a5a",
    "grid_dark": "rgba(201,168,76,0.08)",
}

CATEGORY_COLORS = {
    "Melhor Filme": "#c9a84c",
    "Melhor Diretor": "#e8d48b",
    "Melhor Ator": "#d4af37",
    "Melhor Atriz": "#a07d2e",
}

STATUS_COLORS = {
    "Submetido": "rgba(201,168,76,0.2)",
    "Shortlisted": "rgba(201,168,76,0.5)",
    "Indicado": "#c9a84c",
    "Vencedor": "#d4af37",
}


def build_scatter_chart(df: pd.DataFrame) -> str:
    """Gera o scatter plot Crítica vs Público."""
    # Filtra apenas Melhor Filme para o scatter principal (evita pontos duplicados)
    df_filme = df[df["categoria"] == "Melhor Filme"].copy()

    fig = go.Figure()

    # Adiciona cada categoria com cor diferente
    # Labels só para Melhor Filme (evita sobreposição)
    for cat, color in CATEGORY_COLORS.items():
        mask = df["categoria"] == cat
        subset = df[mask]
        if subset.empty:
            continue

        show_text = cat == "Melhor Filme"
        fig.add_trace(go.Scatter(
            x=subset["rt_score"],
            y=subset["imdb_score"],
            mode="markers+text" if show_text else "markers",
            name=cat,
            text=subset["filme"],
            textposition="top center" if show_text else None,
            textfont=dict(size=9, color=color) if show_text else None,
            marker=dict(
                size=12 if cat == "Melhor Filme" else 9,
                color=color,
                line=dict(width=1, color="rgba(255,255,255,0.2)"),
                opacity=0.9 if cat == "Melhor Filme" else 0.7,
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Rotten Tomatoes: %{x}%<br>"
                "IMDb: %{y}/10<br>"
                f"Categoria: {cat}<br>"
                "<extra></extra>"
            ),
        ))

    # Linha diagonal de "consenso" (onde RT% / 10 == IMDb)
    fig.add_trace(go.Scatter(
        x=[60, 100],
        y=[6.0, 10.0],
        mode="lines",
        line=dict(color="rgba(201,168,76,0.15)", width=1, dash="dash"),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Anotação na diagonal
    fig.add_annotation(
        x=80, y=8.5,
        text="Linha de consenso",
        showarrow=False,
        font=dict(size=9, color="rgba(201,168,76,0.3)"),
        textangle=-30,
    )

    fig.update_layout(
        paper_bgcolor=COLORS["bg_dark"],
        plot_bgcolor=COLORS["bg_chart_dark"],
        font=dict(family="Inter, sans-serif", color=COLORS["text_dark"]),
        xaxis=dict(
            title="Rotten Tomatoes (Crítica) %",
            gridcolor=COLORS["grid_dark"],
            range=[55, 102],
            dtick=10,
            color=COLORS["text_dark"],
        ),
        yaxis=dict(
            title="IMDb (Público)",
            gridcolor=COLORS["grid_dark"],
            range=[5.0, 9.0],
            dtick=0.5,
            color=COLORS["text_dark"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        margin=dict(l=60, r=20, t=50, b=60),
        height=500,
        hoverlabel=dict(
            bgcolor=COLORS["bg_dark"],
            font_size=12,
            font_color=COLORS["accent"],
        ),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="scatter-chart")


def build_brasil_chart(df: pd.DataFrame) -> str:
    """Gera o timeline chart do Brasil no Oscar."""
    if df is None or df.empty:
        return "<div id='brasil-chart'><p>Dados não disponíveis</p></div>"

    # Garante ordenação
    df = df.sort_values("ano").reset_index(drop=True)

    # Mapeia status para valores numéricos (altura da barra)
    status_height = {
        "Submetido": 1,
        "Shortlisted": 2,
        "Indicado": 3,
        "Vencedor": 4,
    }

    df["altura"] = df["status"].map(status_height).fillna(1)
    df["cor"] = df["status"].map(STATUS_COLORS).fillna("rgba(201,168,76,0.2)")

    filme_col = "filme" if "filme" in df.columns else df.columns[1]
    diretor_col = "diretor" if "diretor" in df.columns else None

    hover_text = []
    for _, row in df.iterrows():
        text = f"<b>{row[filme_col]}</b><br>Ano: {int(row['ano'])}"
        if diretor_col and pd.notna(row.get(diretor_col)):
            text += f"<br>Diretor: {row[diretor_col]}"
        text += f"<br>Status: {row['status']}"
        hover_text.append(text)

    fig = go.Figure()

    # Uma barra por status para ter legenda
    for status, color in STATUS_COLORS.items():
        mask = df["status"] == status
        subset = df[mask]
        if subset.empty:
            continue

        subset_hover = [hover_text[i] for i in subset.index]

        fig.add_trace(go.Bar(
            x=subset["ano"],
            y=subset["altura"],
            name=status,
            marker_color=color,
            marker_line=dict(width=0),
            hovertext=subset_hover,
            hoverinfo="text",
            hoverlabel=dict(
                bgcolor=COLORS["bg_dark"],
                font_size=12,
                font_color=COLORS["accent"],
            ),
        ))

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor=COLORS["bg_dark"],
        plot_bgcolor=COLORS["bg_chart_dark"],
        font=dict(family="Inter, sans-serif", color=COLORS["text_dark"]),
        xaxis=dict(
            title="Ano",
            gridcolor=COLORS["grid_dark"],
            color=COLORS["text_dark"],
            dtick=5,
        ),
        yaxis=dict(
            title="",
            showticklabels=False,
            gridcolor=COLORS["grid_dark"],
            range=[0, 5],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        margin=dict(l=20, r=20, t=50, b=60),
        height=400,
        bargap=0.3,
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="brasil-chart")


def build_highlights_html(df: pd.DataFrame) -> str:
    """Gera os cards de destaque do Entregável 1."""
    # Filtra só Melhor Filme para os destaques
    df_filme = df[df["categoria"] == "Melhor Filme"].copy()

    # Mais consensual: menor diferença absoluta
    consensual = df_filme.loc[df_filme["diff_abs"].idxmin()]
    # Mais divisivo: maior diferença absoluta
    divisivo = df_filme.loc[df_filme["diff_abs"].idxmax()]
    # Superestimado pela crítica: maior diff positiva (RT >> IMDb)
    superest = df_filme.loc[df_filme["diff_critica_publico"].idxmax()]
    # Subestimado pela crítica: maior diff negativa (IMDb >> RT)
    subest = df_filme.loc[df_filme["diff_critica_publico"].idxmin()]

    cards = [
        ("consensual", "Mais consensual", consensual,
         f"RT {consensual['rt_score']}% · IMDb {consensual['imdb_score']} · Diff: {consensual['diff_abs']:.0f}"),
        ("divisivo", "Mais divisivo", divisivo,
         f"RT {divisivo['rt_score']}% · IMDb {divisivo['imdb_score']} · Diff: {divisivo['diff_abs']:.0f}"),
        ("superestimado", "Crítica amou, público nem tanto", superest,
         f"RT {superest['rt_score']}% · IMDb {superest['imdb_score']}"),
        ("subestimado", "Público amou, crítica nem tanto", subest,
         f"RT {subest['rt_score']}% · IMDb {subest['imdb_score']}"),
    ]

    html = ""
    for css_class, label, row, detail in cards:
        html += f"""
        <div class="highlight-card {css_class}">
            <div class="highlight-label">{label}</div>
            <div class="highlight-filme">{row['filme']}</div>
            <div class="highlight-detail">{detail}</div>
        </div>
        """
    return html


def build_brasil_stats_html(df: pd.DataFrame) -> str:
    """Gera os cards de estatísticas do Brasil no Oscar."""
    if df is None or df.empty:
        return ""

    total = len(df)
    indicados = len(df[df["status"] == "Indicado"]) + len(df[df["status"] == "Vencedor"])
    primeiro_ano = int(df["ano"].min()) if "ano" in df.columns else "?"
    ultimo_ano = int(df["ano"].max()) if "ano" in df.columns else "?"

    stats = [
        (str(total), "Filmes submetidos"),
        (str(indicados), "Indicações oficiais"),
        (str(primeiro_ano), "Primeira submissão"),
        (str(ultimo_ano), "Submissão mais recente"),
    ]

    html = ""
    for number, label in stats:
        html += f"""
        <div class="brasil-stat">
            <div class="brasil-stat-number">{number}</div>
            <div class="brasil-stat-label">{label}</div>
        </div>
        """
    return html


def main():
    print("Construindo site...")

    # Lê dados processados
    ratings_path = PROCESSED_DIR / "critica_vs_publico.csv"
    brasil_path = PROCESSED_DIR / "brasil_oscar.csv"

    if not ratings_path.exists():
        print(f"ERRO: {ratings_path} não encontrado. Rode process_ratings.py primeiro.")
        return

    df_ratings = pd.read_csv(ratings_path)

    df_brasil = None
    if brasil_path.exists():
        df_brasil = pd.read_csv(brasil_path)
    else:
        print(f"AVISO: {brasil_path} não encontrado. Seção Brasil ficará vazia.")

    # Gera componentes
    scatter_html = build_scatter_chart(df_ratings)
    brasil_html = build_brasil_chart(df_brasil)
    highlights_html = build_highlights_html(df_ratings)
    brasil_stats_html = build_brasil_stats_html(df_brasil)

    # Renderiza template
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("index.html")

    html = template.render(
        scatter_chart_js=scatter_html,
        brasil_chart_js=brasil_html,
        highlights_html=highlights_html,
        brasil_stats_html=brasil_stats_html,
    )

    # Salva
    output_path = DOCS_DIR / "index.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Site gerado: {output_path}")
    print(f"Abra no browser: file://{output_path}")


if __name__ == "__main__":
    main()
