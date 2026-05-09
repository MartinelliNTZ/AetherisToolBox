#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aetheris ToolBox — Ponto de Entrada
====================================
Executável principal. Apenas chama o BootStrap singleton.

Uso:
    python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def main():
    # Garante que a raiz do projeto está no sys.path
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from core.config.BootStrap import BootStrap
    BootStrap().run()


if __name__ == "__main__":
    main()