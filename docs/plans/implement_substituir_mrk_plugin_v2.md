 cada item de # Plano de Ação v2: Plugin `MrkSubstitutor`

## Correções baseadas no feedback

### 🔴 Correções Obrigatórias

1. **`VectorLayerSource.read()`** — usar `ToolKey.UNTRACEABLE.value` não string `"Untraceable"`
2. **`RasterLayerSource`** — apenas stub, mínimo possível
3. **`GridFieldMapping`** (renomeado de `MrkFieldMappingGrid`):
   - Widget **genérico** (Contrato 11)
   - Config dict com `tooltip` que propaga para todos sub-widgets
   - NÃO usar `SignalManager` para mudanças internas (apenas `Signal`)
4. **`GridRadio`** — novo widget genérico, similar a `GridCheckBox`:
   - Configurado por dict com `label`, `description`, `default`, `tooltip`
   - `num_columns=3` default, responsivo
   - Se receber 2 itens, divide igualmente em 2 colunas
5. **Plugin cenários**:
   - **Cenário 1**: Usuário informa CSV/SHP + MRK → processa 1 MRK
   - **Cenário 2**: Usuário informa pasta → nome do MRK é chave para match com dados
   - `SimpleSelector` muda browse_mode conforme cenário (file vs folder)
6. **Log + Console**: quando logar "arquivo encontrado/não encontrado", também emitir `console_message`
7. **Novo Contrato 24**: SignalManager é para comunicação entre plugins/ferramentas, não para mudanças internas de widgets

### 📦 Entregáveis Finais

| # | Arquivo | Ação |
|---|---|---|
| 1 | `utils/vector/__init__.py` | Criar |
| 2 | `utils/vector/VectorLayerSource.py` | Criar |
| 3 | `utils/raster/__init__.py` | Criar |
| 4 | `utils/raster/RasterLayerSource.py` | Criar (stub) |
| 5 | `resources/widgets/GridFieldMapping.py` | Criar (genérico) |
| 6 | `resources/widgets/GridRadio.py` | Criar (genérico) |
| 7 | `plugins/mrk_substitutor/__init__.py` | Criar |
| 8 | `plugins/mrk_substitutor/MrkSubstitutorPlugin.py` | Criar |
| 9 | `core/enum/ToolKey.py` | Modificar |
| 10 | `core/config/ToolRegistry.py` | Modificar |
| 11 | `docs/ia/contracts.md` | Modificar (+ Contrato 24) |
| 12 | `docs/skills/widgets_skill.md` | Modificar |