# Plano de Ação: Implementação do Plugin `MrkSubstitutor`

## 📋 Sumário
Conversão do script legado `substituir_mrk.py` em um plugin Aetheris ToolBox, com novo widget de mapeamento em grid, classes de I/O vetorial/raster, e integração total com o sistema (logs, preferências, console, ExplorerUtils).

---

## 🔨 Etapas de Implementação

### Fase 1 — Infraestrutura: Vector/Raster I/O (utils/)

#### 1.1 Criar `utils/vector/__init__.py`
- Inicializador do pacote
- Export público consolidado

#### 1.2 Criar `utils/vector/VectorLayerSource.py`
**Classe:** `VectorLayerSource`
**Responsabilidade:** I/O de camadas vetoriais (Shapefile, GeoPackage, CSV)
**API Pública:**
```python
class VectorLayerSource:
    @staticmethod
    def read(path: str, tool_key: str = "Untraceable") -> list[dict]#ERRADO 
    def read(path: str, tool_key: str = Toolkey.Untraceable) -> list[dict]#CORRETO 
    @staticmethod
    def get_driver_name(path: str) -> str  # "ESRI Shapefile", "GPKG", "CSV"
```

**Regras:**
- Detecta formato automaticamente pela extensão (`.shp`, `.gpkg`, `.csv`)
- Usa `geopandas` para `.shp` e `.gpkg`
- Usa `csv.DictReader` para `.csv`
- Converte tipos numpy (int, float, bool, NaN) para tipos nativos Python (`str`)
- Remove coluna `geometry` automaticamente
- Implementa `_get_logger()` estático com `tool_key` (skill log_utils)
- Loga: início da leitura, quantidade de registros, erros
- Nomes de variáveis em INGLÊS

**Arquivo:** `utils/vector/VectorLayerSource.py`

#### 1.3 Criar `utils/raster/__init__.py`
- Inicializador do pacote (placeholder para uso futuro)

#### 1.4 Criar `utils/raster/RasterLayerSource.py`
**Classe:** `RasterLayerSource`
**Responsabilidade:** I/O de camadas raster (placeholder para uso futuro)
**API Pública:**
```python
class RasterLayerSource:
    @staticmethod
    def read_metadata(path: str, tool_key: str = "Untraceable") -> dict
```

**Regras:**
- Implementação mínima: lê metadados básicos de rasters GeoTIFF
- Usa `rasterio` ou `gdal`
- Loga operações
- Nomes em INGLÊS

---

### Fase 2 — Novo Widget: `MrkFieldMappingGrid`

#### 2.1 Criar `resources/widgets/MrkFieldMappingGrid.py`
**Classe:** `MrkFieldMappingGrid`
**Responsabilidade:** Grade configurável de mapeamento de campos (checkbox + label + lineedit + label + lineedit)

**Comportamento:**
- Configurado via dicionário:
  ```python
  {
      "field_key": {
          "from_label": "Campo Origem:",     # label do primeiro lineedit
          "from_placeholder": "AbsZ",
          "to_label": "Campo MRK:",          # label do segundo lineedit
          "to_placeholder": "Ellh",
          "default_from": "AbsZ",
          "default_to": "Ellh",
          "default_enabled": True,
      },
  }
  ```
- Cada linha: `[QCheckBox] [QLabel] [QLineEdit] [QLabel] [QLineEdit]`
- Checkbox unchecked → todos os widgets da linha disabled (aparencia visual)
- Checkbox checked → widgets habilitados para edição
- Grid rolável (QScrollArea)
- Todo encapsulado — o plugin só chama:
  - `self.mapping_grid.values` → dict mapeamentos ativos
  - `self.mapping_grid.all` → dict completo (inclusive inativos)
  - `self.mapping_grid.set_values(dict)` → restaurar de preferências
  - `self.mapping_grid.changed.connect(...)` → callback de mudança

**Regras:**
- Herda de `QWidget`
- `snake_case` para métodos, `PascalCase` para classe
- Usa `GridLayout` interno
- Signal `changed` emitido quando qualquer campo ou checkbox muda
- Salva estado completo (incluindo enabled/disabled)
- Nomes em INGLÊS

#### 2.2 Atualizar `docs/skills/widgets_skill.md`
- Adicionar `MrkFieldMappingGrid` ao catálogo de widgets
- Documentar API pública, parâmetros e sinais (Contrato 12)

---

### Fase 3 — Plugin Principal: `MrkSubstitutor`

#### 3.1 Criar diretório e arquivos
```
plugins/mrk_substitutor/
    __init__.py
    MrkSubstitutorPlugin.py
```

#### 3.2 Classe `MrkSubstitutorPlugin(BasePlugin)`
**Chave:** `ToolKey.MRK_SUBSTITUTOR = "MrkSubstitutor"`
**Título:** "Mrk Substituidor"
**ToolType:** `ToolType.FOLDER`
**Category:** `CategoryTool.CENTRAL`

**UI (build_ui):**
1. Título → ExecutionButtons (seguindo Contrato 18)
   - "EXECUTAR" (primary) → executa substituição
   - "CARREGAR MRK" (secondary) → seleciona arquivo(s) .MRK
   - "SALVAR CONFIG" (secondary) → salva preferências
2. GroupPainel "Arquivos MRK"
   - SimpleSelector para pasta de origem
   - GridCheckBox para opções (subpastas)
3. GroupPainel "Mapeamento de Campos"
   - MrkFieldMappingGrid (widget novo)
4. GroupPainel "Dados de Origem"
   - SimpleSelector para arquivo de dados (.csv/.shp/.gpkg)
   - GridLabel mostrando info do arquivo (registros, colunas)
5. GroupPainel "Saída"
   - SimpleSelector (save_file) para pasta destino
   - GridLabel com status

**Lógica Central (core_logic):**
- `_find_mrk_files(root_path, recursive: bool) -> list[Path]`
  - Usa **ExplorerUtils** para navegação de diretório
  - Busca arquivos `.MRK` (case insensitive)
  - Loga descoberta

- `_find_data_file(mrk_path: str) -> str | None`
  - Usa ExplorerUtils para encontrar dados correspondentes
  - Busca por CHAVE no nome (ex: nome_base do MRK), não por match exato
  - Usa `os.path.splitext` corretamente
  - Ordem de busca: .gpkg → .shp → .csv (mesmo diretório)
  - Loga: arquivo encontrado/não encontrado/ e exibe no console tb 

- `_load_data(path: str) -> list[dict]`
  - Delega para `VectorLayerSource.read()`
  - Loga quantidade de registros

- `_parse_mrk_line(line: str) -> dict`
  - Extrai campos `{campo: {valor_str, len, idx}}`
  - Regex para extrair `valor,NAMEDOCAMPO`

- `_build_mrk_line(parts, indices, novos_valores, originais) -> str`
  - Reconstrói linha preservando tabulação

- `_pad_value(original, novo) -> str`
  - Preserva comprimento e casas decimais

- `process_mrk(mrk_path, data, mapping, output_dir) -> int`
  - Substituições por linha
  - Suporte a MAPPING via MrkFieldMappingGrid
  - Loga cada substituição
  - Emite progress via SignalManager
  - Emite console_message via SignalManager

**Preferências (load/save):**
- `load_prefs()`:
  - Restaura origem, destino, dados, mapeamento, opções
- `save_prefs()`:
  - Salva todos os widgets

**Integrações Obrigatórias:**
- ✅ `self.logger` em todos os pontos críticos (início, fim, erros)
- ✅ `SignalManager.progress_update` durante processamento
- ✅ `SignalManager.console_message` para feedback ao usuário
- ✅ `self.preferences` para persistência
- ✅ `MessageBox` para diálogos com usuário (Contrato 1)
- ✅ `ExplorerUtils` para seleção de arquivos (Contrato 17)
- ✅ `ExecutionButtons` para botões de ação (Contrato 18)

---

### Fase 4 — Registro e Integração

#### 4.1 Adicionar `ToolKey.MRK_SUBSTITUTOR`
**Arquivo:** `core/enum/ToolKey.py`
```python
MRK_SUBSTITUTOR = "MrkSubstitutor"
```

#### 4.2 Registrar no `ToolRegistry`
**Arquivo:** `core/config/ToolRegistry.py`
```python
ToolKey.MRK_SUBSTITUTOR.value: Tool(
    name=ToolKey.MRK_SUBSTITUTOR.value,
    title="Mrk Substituidor",
    widget_factory=_make_factory(
        "plugins.mrk_substitutor.MrkSubstitutorPlugin",
        "MrkSubstitutorPlugin",
    ),
    tooltip="Substitui valores de altitude (Ellh) em arquivos MRK",
    tool_type=ToolType.FOLDER,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

---

### Fase 5 — Tratamento de Nomes e Busca

#### 5.1 Refatorar Busca de Arquivos
A busca atual é frágil:
```python
f'MrkFile_{nome_mrk}.csv'  # busca nome exato com extensão .MRK
```

**Nova lógica:**
- Extrair `nome_base` do MRK (sem extensão)
- Buscar arquivos de dados que CONTENHAM o nome_base como substring (não match exato)
- Usar `fnmatch` ou `glob` com patterns flexíveis
- **Nunca incluir extensão do MRK na busca** (ex: se MRK é `ponto123.MRK`, busca `ponto123.*`, não `ponto123.MRK.*`)

```python
def _find_data_file(mrk_path: str, data_dir: str = "") -> str | None:
    """
    Busca arquivo de dados correspondente ao MRK.
    
    Lógica:
    1. Extrai nome_base do MRK (sem extensão)
    2. Se data_dir for informado, busca lá
    3. Procura arquivos contendo nome_base + .gpkg/.shp/.csv
    4. Prioriza: .gpkg > .shp > .csv
    5. Se não achar, busca qualquer .gpkg/.shp/.csv no diretório
    """
```

#### 5.2 Renomear Variáveis pt→en
| Português (atual) | Inglês (novo) |
|---|---|
| `nome_mrk` | `mrk_name` |
| `nome_base` | `base_name` |
| `caminho_dados` | `data_path` |
| `pasta_destino` | `output_dir` |
| `total_substituicoes` | `total_replacements` |
| `linhas_mrk` | `mrk_lines` |
| `linhas_saida` | `output_lines` |
| `valor_original` | `original_value` |
| `valor_str` | `value_str` |
| `col_dados` | `data_column` |
| `campo_mrk` | `mrk_field` |
| `substituicoes` | `replacements` |
| `indices` | `indices` (mantido) |
| `resultado` | `results` |
| `novo_valor`, `novo_valor_padded` | `new_value`, `new_value_padded` |
| `tam_original` | `original_length` |
| `casas_orig`, `casas_novo` | `original_decimals`, `new_decimals` |
| `partes_orig`, `partes_novo` | `original_parts`, `new_parts` |

---

## 📦 Entregáveis

| # | Arquivo | Descrição |
|---|---|---|
| 1 | `utils/vector/__init__.py` | Init pacote vector |
| 2 | `utils/vector/VectorLayerSource.py` | Leitura de vetores |
| 3 | `utils/raster/__init__.py` | Init pacote raster |
| 4 | `utils/raster/RasterLayerSource.py` | Leitura de rasters (placeholder) |
| 5 | `resources/widgets/MrkFieldMappingGrid.py` | Widget de mapeamento em grid |
| 6 | `plugins/mrk_substitutor/__init__.py` | Init do plugin |
| 7 | `plugins/mrk_substitutor/MrkSubstitutorPlugin.py` | Plugin principal |
| 8 | `core/enum/ToolKey.py` | + ToolKey.MRK_SUBSTITUTOR |
| 9 | `core/config/ToolRegistry.py` | + registro MrkSubstitutor |
| 10 | `docs/skills/widgets_skill.md` | + MrkFieldMappingGrid documentado |

---

## ✅ Checklist de Qualidade

- [ ] Código compila (`py_compile`)
- [ ] Nenhum `QMessageBox` direto (só via `MessageBox`)
- [ ] Todo `except` tem `as e` e `logger.error()`
- [ ] Nenhum import morto
- [ ] Widget `MrkFieldMappingGrid` consultado antes de criar UI bruta (Contrato 11 OK)
- [ ] Skill de criação de ferramentas seguida (`create_tool_skill.md`)
- [ ] Skill de logs seguida (`log_utils_skill.md`)
- [ ] Skill de preferências seguida (`preferences_skill.md`)
- [ ] Skill de widgets consultada (`widgets_skill.md`)
- [ ] Contratos respeitados (1-22)
- [ ] Nomes em INGLÊS (variáveis, métodos, classes)
- [ ] Documentação atualizada (Contrato 12)
- [ ] Busca de arquivos não inclui extensão .MRK no pattern
- [ ] ExplorerUtils usado para seleção de arquivos
- [ ] SignalManager usado para progresso e console
- [ ] ExecutionButtons usado para botões de ação

---

## 📐 Arquitetura - Fluxo de Dados

```
Usuário → MrkSubstitutorPlugin
                │
                ├── MrkFieldMappingGrid (widget)
                │     └── config dict → checkbox + label + linha1 + label + linha2
                │
                ├── VectorLayerSource (utils/vector/)
                │     └── .shp / .gpkg / .csv → list[dict]
                │
                ├── ExplorerUtils (seleção de arquivos)
                │
                ├── SignalManager (progresso + console)
                │
                └── Preferences (persistência)
                      └── self.preferences → JSON
```

**Fluxo de Execução:**
1. Usuário configura mapeamento no `MrkFieldMappingGrid`
2. Seleciona pasta de MRKs via `SimpleSelector` (ExplorerUtils)
3. Seleciona dados de origem via `SimpleSelector` (ExplorerUtils)
4. Clica "EXECUTAR"
5. Plugin busca arquivos `.MRK` → encontra dados correspondentes
6. `VectorLayerSource.read()` carrega dados
7. Plugin processa cada MRK linha a linha
8. `SignalManager.progress_update.emit()` a cada MRK
9. `SignalManager.console_message.emit()` a cada substituição
10. Arquivos gerados na pasta de saída
11. `MessageBox.show_info()` ao finalizar