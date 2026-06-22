# -*- coding: utf-8 -*-
"""
LasBlackFilterTask — Task para filtrar pontos pretos em nuvens LAS/LAZ
======================================================================
Remove pontos onde R, G e B estão todos abaixo de um limiar configurável.
Gera novo arquivo com sufixo _filtrado.las/.laz sem alterar o original.
Opção de salvar os pontos pretos removidos em arquivo separado.

ATENÇÃO: Emite progresso via SignalManager durante _run().
Os sinais Qt são thread-safe — funcionam de dentro da QThread.
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np

from core.manager.SignalManager import SignalManager
from utils.LasUtil import LasUtil
from ..BaseTask import BaseTask


class LasBlackFilterTask(BaseTask):
    """
    Task que filtra pontos pretos de um arquivo LAS/LAZ.

    Context requer:
        - file_path: Caminho do arquivo LAS/LAZ de entrada
        - limiar: Valor máximo de R/G/B para considerar preto (0–255)
        - output_limpo: Caminho para salvar o LAS filtrado
        - output_pretos: Caminho para salvar pontos pretos (opcional, string vazia se não salvar)

    Result produz (dict):
        - n_total: Total de pontos no arquivo original
        - n_removidos: Quantidade de pontos removidos
        - n_mantidos: Quantidade de pontos mantidos
        - n_pretos: Quantidade de pontos pretos salvos (0 se não salvou)
        - output_limpo: Caminho do arquivo filtrado gerado
        - output_pretos: Caminho do arquivo de pretos gerado ("" se não salvou)
    """

    def __init__(
        self,
        file_path: str,
        limiar: int,
        salvar_pretos: bool,
        output_limpo: str,
        output_pretos: str,
    ):
        super().__init__(description=f"Filtrar pontos pretos: {os.path.basename(file_path)}")
        self._file_path = file_path
        self._limiar = limiar
        self._salvar_pretos = salvar_pretos
        self._output_limpo = output_limpo
        self._output_pretos = output_pretos

    def _run(self) -> bool:
        """
        Executa a filtragem em background thread emitindo progresso.

        4 etapas (stages) sincronizadas com o HUD Modo 3:
          Stage 0: Leitura          (0% → 25%)
          Stage 1: Filtragem        (25% → 50%)
          Stage 2: Salvar Filtrado  (50% → 75%)
          Stage 3: Salvar Pretos    (75% → 100%)
        """
        signals = SignalManager.instance()

        # ── Stage 0: Leitura (0% → 25%) ────────────────────────────
        signals.hud_update.emit({"message": "Lendo arquivo LAS...", "progress": 5.0})
        signals.progress_update.emit(5.0)

        # Lê arrays RGB via LasUtil
        rgb = LasUtil.get_rgb_arrays(self._file_path)
        if not rgb:
            raise RuntimeError("Falha ao ler arrays RGB do arquivo LAS")

        n_total = len(rgb["red"])

        signals.hud_update.emit({
            "message": f"Analisando {n_total:,} pontos...",
            "progress": 20.0,
        })
        signals.progress_update.emit(20.0)

        signals.hud_stage_done.emit(0)  # Stage 0 concluído

        # ── Stage 1: Filtragem (25% → 50%) ─────────────────────────
        mask_valido = (
            (rgb["red"] > self._limiar)
            | (rgb["green"] > self._limiar)
            | (rgb["blue"] > self._limiar)
        )
        n_removidos = n_total - int(np.sum(mask_valido))

        signals.hud_update.emit({
            "message": f"Removendo {n_removidos:,} pontos pretos...",
            "progress": 50.0,
        })
        signals.progress_update.emit(50.0)

        signals.hud_stage_done.emit(1)  # Stage 1 concluído

        # ── Stage 2: Salvar LAS filtrado (50% → 75%) ───────────────
        # Reabre o LAS completo para criar o arquivo filtrado
        import laspy
        las = laspy.read(self._file_path)

        n_mantidos = LasUtil.create_filtered_las(
            las, mask_valido, self._output_limpo,
        )
        if n_mantidos is None:
            raise RuntimeError(f"Erro ao salvar LAS filtrado: {self._output_limpo}")

        signals.hud_update.emit({
            "message": f"Salvando LAS filtrado ({n_mantidos:,} pontos)...",
            "progress": 75.0,
        })
        signals.progress_update.emit(75.0)

        signals.hud_stage_done.emit(2)  # Stage 2 concluído

        # ── Stage 3: Salvar pontos pretos (opcional, 75% → 100%) ───
        n_pretos = 0
        output_pretos_final: Optional[str] = None
        if self._salvar_pretos and n_removidos > 0 and self._output_pretos:
            mask_pretos = ~mask_valido
            n_pretos_salvos = LasUtil.create_filtered_las(
                las, mask_pretos, self._output_pretos,
            )
            if n_pretos_salvos is not None:
                n_pretos = n_pretos_salvos
                output_pretos_final = self._output_pretos

            signals.hud_update.emit({
                "message": f"Salvando {n_pretos:,} pontos pretos...",
                "progress": 95.0,
            })
            signals.progress_update.emit(95.0)

        signals.hud_stage_done.emit(3)  # Stage 3 concluído → HUD vai a 100%

        # ── Resultado ───────────────────────────────────────────────
        self.result = {
            "n_total": n_total,
            "n_removidos": n_removidos,
            "n_mantidos": n_mantidos,
            "n_pretos": n_pretos,
            "output_limpo": self._output_limpo,
            "output_pretos": output_pretos_final or "",
        }
        return True

    def __repr__(self) -> str:
        return (
            f"<LasBlackFilterTask '{self._file_path}' "
            f"limiar={self._limiar}>"
        )