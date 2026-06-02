# -*- coding: utf-8 -*-
"""
MdManager — Lógica de extração e transformação de Markdown a partir de DoclingDocument
=======================================================================================
Genérico: não apenas colunas, mas qualquer manipulação futura de markdown.
Sem dependências Qt — puro Python + docling-core.

Uso:
    from plugins.docling.MdManager import MdManager

    md = MdManager.export_by_columns(doc, page_no=0, manual_columns=0)
"""

from __future__ import annotations

import statistics
from typing import Optional

from docling_core.types.doc import (
    CodeItem,
    DocItem,
    DocItemLabel,
    DoclingDocument,
    ListItem,
    SectionHeaderItem,
    TableItem,
    TextItem,
    TitleItem,
)
from docling_core.types.doc.document import FormulaItem


class MdManager:
    """
    Métodos estáticos para extrair e transformar DoclingDocument em Markdown.
    """

    # ── Constantes internas ────────────────────────────────────────────
    _COLUMN_NAMES = (
        "Esquerda", "Centro", "Direita",
        "Coluna 4", "Coluna 5", "Coluna 6",
    )

    # ══════════════════════════════════════════════════════════════════
    # API Pública
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def export_by_columns(
        doc: DoclingDocument,
        *,
        manual_columns: int = 0,
        page_no: int = 0,
    ) -> Optional[str]:
        """
        Monta Markdown com seções por coluna (da esquerda para a direita),
        usando caixas normalizadas.

        Retorna None se não houver dados suficientes para layout multi-coluna.

        Args:
            doc: DoclingDocument carregado.
            manual_columns: 0 para automático, 2-6 para forçar colunas.
            page_no: Número da página para processar (0 = primeira).

        Returns:
            str com markdown dividido por colunas, ou None.
        """
        blocks: list[tuple[float, float, str]] = []
        for item, _level in doc.iterate_items(traverse_pictures=True):
            if not isinstance(item, DocItem):
                continue
            geo = MdManager._norm_center_top(doc, item)
            if geo is None:
                continue
            cx, top, pno = geo
            if pno != page_no:
                continue
            snip = MdManager._snippet_for_item(doc, item)
            if not snip:
                continue
            blocks.append((cx, top, snip))

        if len(blocks) < 4:
            return None

        cx_list = [b[0] for b in blocks]
        k = manual_columns if manual_columns >= 2 else MdManager._infer_column_count(cx_list)
        if k < 2:
            return None

        labels, centroids = MdManager._kmeans1d_assign(cx_list, k)
        order = sorted(range(k), key=lambda i: centroids[i])

        by_col: list[list[tuple[float, str]]] = [[] for _ in range(k)]
        for lab, (_cx, top, snip) in zip(labels, blocks, strict=True):
            by_col[lab].append((top, snip))

        # Separador <hr> em markdown
        rule = "\n\n---\n\n"
        sections: list[str] = []
        for rank, old_idx in enumerate(order):
            title = (
                MdManager._COLUMN_NAMES[rank]
                if rank < len(MdManager._COLUMN_NAMES)
                else f"Coluna {rank + 1}"
            )
            col_blocks = sorted(by_col[old_idx], key=lambda x: x[0])
            texts = [t for _, t in col_blocks]
            body = "\n\n".join(texts)
            sections.append(
                f"## **Painel {rank + 1}** — _{title}_\n\n{body}\n"
            )

        return rule.join(sections).strip() + "\n"

    # ══════════════════════════════════════════════════════════════════
    # Métodos Internos (estáticos)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _norm_center_top(
        doc: DoclingDocument, item: DocItem
    ) -> Optional[tuple[float, float, int]]:
        """
        Centro horizontal e topo normalizados (0..1) e número da página.
        Retorna (cx, top, page_no) ou None se item não tiver prov.
        """
        if not item.prov:
            return None
        prov = item.prov[0]
        page = doc.pages.get(prov.page_no)
        if not page:
            return None
        b = prov.bbox.normalized(page.size)
        cx = (b.l + b.r) / 2.0
        top = min(b.t, b.b)
        return cx, top, prov.page_no

    @staticmethod
    def _snippet_for_item(doc: DoclingDocument, item: DocItem) -> Optional[str]:
        """Trecho Markdown aproximado para um item isolado."""
        if isinstance(item, TableItem):
            try:
                return item.export_to_markdown(doc).strip()
            except Exception:
                return None
        if isinstance(item, CodeItem) and item.text.strip():
            lang = getattr(item.code_language, "value", str(item.code_language))
            if lang in ("unknown", "UNKNOWN", "Unknown"):
                lang = ""
            fence = (
                f"```{lang}\n{item.text.strip()}\n```"
                if lang
                else f"```\n{item.text.strip()}\n```"
            )
            return fence
        if isinstance(item, FormulaItem) and getattr(item, "text", "") and item.text.strip():
            return f"$${item.text.strip()}$$"
        if not isinstance(item, TextItem) or not item.text.strip():
            return None
        if item.label in (DocItemLabel.PAGE_HEADER, DocItemLabel.PAGE_FOOTER):
            return None
        t = item.text.strip()
        if isinstance(item, TitleItem):
            return f"# {t}"
        if isinstance(item, SectionHeaderItem):
            return f"## {t}"
        if isinstance(item, ListItem):
            return f"- {t}"
        return t

    @staticmethod
    def _infer_column_count(cx_values: list[float]) -> int:
        """Infere número de colunas pela distribuição dos centros horizontais."""
        if len(cx_values) < 6:
            return 1
        xs = sorted(cx_values)
        gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
        if not gaps:
            return 1
        med = statistics.median(gaps)
        mg = max(gaps)
        if mg < 0.06 and med < 0.025:
            return 1
        threshold = max(0.08, 2.2 * med)
        splits = sum(1 for g in gaps if g >= threshold)
        k = splits + 1
        return max(1, min(6, k))

    @staticmethod
    def _kmeans1d_assign(
        xs: list[float], k: int
    ) -> tuple[list[int], list[float]]:
        """
        Atribui cada x a um cluster 0..k-1.
        Retorna (labels, centroids) na mesma ordem de xs.
        """
        if k <= 1 or not xs:
            return [0] * len(xs), [0.5]
        lo, hi = min(xs), max(xs)
        if hi - lo < 1e-6:
            return [0] * len(xs), [(lo + hi) / 2]
        centroids = [lo + (hi - lo) * (i + 0.5) / k for i in range(k)]
        labels: list[int] = []
        for _ in range(18):
            clusters: list[list[float]] = [[] for _ in range(k)]
            for x in xs:
                j = min(range(k), key=lambda i: abs(x - centroids[i]))
                clusters[j].append(x)
            for i in range(k):
                if clusters[i]:
                    centroids[i] = sum(clusters[i]) / len(clusters[i])
            labels = [
                min(range(k), key=lambda i: abs(x - centroids[i])) for x in xs
            ]
        return labels, centroids