# Skill: Utilitários Compartilhados (`utils`)

O pacote `utils/` reúne helpers reutilizáveis para toda a aplicação. Sempre que você precisar de funcionalidade genérica que não pertence a um plugin específico, verifique se já existe um utilitário no `utils/` antes de criar código novo.

> ⚠️ Esta skill é um complemento da regra de documentação e arquitetura: utilitários devem ser centralizados e não duplicados entre plugins.

---

## 🧠 Quando usar `utils`

Use `utils` sempre que precisar de:
- diálogos de sistema (`MessageBox`)
- seleção de arquivos/pastas (`ExplorerUtils`)
- formatação de datas e tamanhos (`FormatUtils`)
- gerenciamento de diretórios de configuração de plugin (`ExplorerUtils.get_plugin_config_dir`)
- criação/edição de JSONs temporários (`JsonUtil`)
- arquivos de projeto `.mtl` (`ProjectUtil`)
- catálogos de extensões e dicionários padronizados (`DictManager`)
- cores consistentes para logs, tools e classes (`ColorProvider`)
- metadados de arquivos (`BasicExtractor`)
- extração de markdown de DoclingDocument (`MdManager`)
- logger centralizado via `BaseUtil._get_logger()`
- monitoramento de tempo/ETA de processamento (`ProcessStatisticsUtil`)
- leitura de metadados de arquivos LAS/LAZ (`LasUtil`)

## 📦 Módulos principais e suas responsabilidades

### `utils.BaseUtil` (Classe Base)

**Toda classe em `utils/` DEVE herdar de `BaseUtil`.**

`BaseUtil` centraliza o método `_get_logger()` que todas as utils usam para logging. Em vez de instanciar `LogUtils` diretamente, use:

```python
from utils.BaseUtil import BaseUtil

class MinhaUtil(BaseUtil):
    @staticmethod
    def meu_metodo(tool_key: str = ToolKey.UNTRACEABLE.value):
        logger = BaseUtil._get_logger(tool_key, "MinhaUtil")
        logger.info("Executando", code="EXEC")
```

**Regras:**
- Todo método público de util DEVE aceitar `tool_key: str = ToolKey.UNTRACEABLE.value` como parâmetro nomeado.
- Use `BaseUtil._get_logger(tool_key, "ClassName")` para obter o logger — nunca instancie `LogUtils` diretamente.

### `utils.ExplorerUtils`

Responsável por todas as interações com `QFileDialog`.

Use quando precisar:
- abrir ou salvar um arquivo
- selecionar uma pasta
- garantir a existência de um diretório
- resolver o diretório inicial para diálogos
- obter o diretório de config de um plugin
- gerar caminhos padrão por categoria de asset

```python
from utils.ExplorerUtils import ExplorerUtils

path = ExplorerUtils.open_file("Selecionar imagem", file_filter="GeoTIFF (*.tif)")
output = ExplorerUtils.save_file("Salvar como", file_filter="JSON (*.json)")
folder = ExplorerUtils.select_directory("Selecionar pasta")
config_dir = ExplorerUtils.get_plugin_config_dir("hotkey")
```

### `utils.MessageBox`

Use sempre `MessageBox` para qualquer diálogo modal. É a única classe permitida para acessar `QMessageBox`.

```python
from utils.MessageBox import MessageBox

MessageBox.show_error("Falha ao carregar arquivo")
MessageBox.show_warning("Campo obrigatório não preenchido")
MessageBox.show_info("Processamento concluído")
if MessageBox.show_question("Deseja salvar as alterações?") == MessageBox.YES:
    salvar()
```

### `utils.JsonUtil`

Use para criar e manipular arquivos JSON temporários. Não escreva JSON temporário com `open()` + `json.dump()` manualmente.

```python
from utils.JsonUtil import JsonUtil

path = JsonUtil.create_temp_json({"key": "value"})
data = JsonUtil.read_json(path)
JsonUtil.update_json(path, {"status": "ok"})
JsonUtil.cleanup_temp_json(path)
```

### `utils.FormatUtils`

Use para formatação de dados padronizada.

```python
from utils.FormatUtils import FormatUtils

size = FormatUtils.format_size(2048)
date = FormatUtils.format_date(time.time())
```

### `utils.ProjectUtil`

Use para criar, carregar ou atualizar arquivos de projeto `.mtl`.

```python
from utils.ProjectUtil import ProjectUtil

info = ProjectUtil.create_project("C:/meu_projeto", "MeuProjeto")
project = ProjectUtil.load_project("C:/meu_projeto/MeuProjeto.mtl")
updated = ProjectUtil.update_last_modified("C:/meu_projeto/MeuProjeto.mtl")
```

Para criar com substituição segura, use:

```python
safe_info = ProjectUtil.create_project_safe("C:/meu_projeto", "MeuProjeto", parent_widget=self)
```

### `utils.DictManager`

Fornece catálogos padronizados de extensões e dicionários usados pelo sistema.

```python
from utils.DictManager import DictManager

all_extensions = DictManager.file_extensions()
```

### `utils.ColorProvider`

Use para cores consistentes em logs, tools e classes.

```python
from utils.ColorProvider import ColorProvider

color = ColorProvider.level_color("INFO")
tool_color = ColorProvider.tool_color("Console")
class_color = ColorProvider.class_color("MainWindow")
```

### `utils.BasicExtractor`

Extrai metadados básicos de arquivos (nome, tamanho, datas, etc).

```python
from utils.basic_extractor import BasicExtractor

props = BasicExtractor.extract("c:/arquivo.txt")
data = BasicExtractor.enrich_json("c:/temp/123.json", "c:/arquivo.txt")
```

### `utils.MdManager`

Extrai e transforma DoclingDocument em Markdown, com suporte a layout multi-coluna.

```python
from utils.MdManager import MdManager

md = MdManager.export_by_columns(doc, page_no=0, manual_columns=0)
```

### `utils.Preferences`

Gerencia preferências de ferramentas em `config/preferences.json`.

```python
from utils.Preferences import Preferences
from core.enum.ToolKey import ToolKey

Preferences.save_tool_prefs(ToolKey.CONSOLE, {"font_size": 12})
data = Preferences.load_tool_prefs(ToolKey.CONSOLE)
```

### `utils.ProcessStatisticsUtil`

Monitora tempo de execução, contagem de itens e estima ETA para operações longas. Os dados são persistidos via `Preferences` em `config/preferences.json` para acúmulo entre execuções.

```python
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil

stats = ProcessStatisticsUtil(tool_key="LasBlackFilter")
stats.start(n=0, ntype=ProcessStatisticsUtil.POINTS, ntotal=50000)
# ... processamento ...
stats.end()

print(stats.summary)           # "ETA: 10:35:08 (restam 30.0s, media historica: 0.0s)"
print(stats.eta_str)           # "10:35:08"
print(stats.remaining_str)     # "30.0s"
print(stats.total_time_str)    # "0.0s"
print(stats.elapsed_str)       # "25.3s"
```

**Constantes de tipo (NType):**
```python
ProcessStatisticsUtil.PIXELS    # "pixels"
ProcessStatisticsUtil.FEATURES  # "features"
ProcessStatisticsUtil.MBYTES    # "mbytes"
ProcessStatisticsUtil.POINTS    # "points"
ProcessStatisticsUtil.FILES     # "files"
ProcessStatisticsUtil.LINES     # "lines"
ProcessStatisticsUtil.ITEMS     # "items"
```

**Regras:**
- A classe é instanciada automaticamente em `BasePlugin` como `self.statistics`.
- `start()` carrega o histórico do disco via `Preferences.load_tool_prefs()`.
- `end()` persiste os dados acumulados via `Preferences.save_tool_prefs()`.
- Na primeira execução (sem dados históricos), assume **30s** como ETA padrão.
- Herda de `BaseUtil`.

### `utils.LasUtil`

Utilitário estático para leitura de metadados e processamento de arquivos LAS/LAZ (nuvens de pontos).

```python
from utils.LasUtil import LasUtil

info = LasUtil.get_info("nuvem.las", tool_key=ToolKey.LAS_BLACK_FILTER.value)
print(info["point_count"])   # 1_234_567
print(info["has_rgb"])       # True

n = LasUtil.get_point_count("nuvem.las")
has = LasUtil.has_rgb("nuvem.las")
bbox = LasUtil.get_bounding_box("nuvem.las", sample_size=10000)

rgb = LasUtil.get_rgb_arrays("nuvem.las")
print(rgb["red"].shape)     # (1234567,)

# Filtrar pontos com máscara
las = laspy.read("nuvem.las")
mask = las.red > 10
n_salvos = LasUtil.create_filtered_las(las, mask, "saida_filtrada.las")

# Resolver caminho de saída com sufixo
output = LasUtil.resolve_output_path("nuvem.las", suffix="_filtrado")
# → "nuvem_filtrado.las"

# Garantir diretório de saída
LasUtil.ensure_output_dir("pasta/saida/arquivo.las")
```

**Métodos:**

| Método | Descrição | Retorno |
|--------|-----------|---------|
| `get_info(path)` | Metadados completos (point_count, has_rgb, dimension_names) | `dict` |
| `get_point_count(path)` | Total de pontos (0 se erro) | `int` |
| `has_rgb(path)` | True se possui bandas red/green/blue | `bool` |
| `get_bounding_box(path, sample_size=10000)` | Bounding box aproximada (x/y/z min/max) | `dict` |
| `get_rgb_arrays(path)` | Lê bandas RGB como arrays numpy int64 | `dict[str, np.ndarray]` |
| `create_filtered_las(las, mask, output_path)` | Cria LAS filtrado a partir de máscara booleana | `Optional[int]` |
| `ensure_output_dir(output_path)` | Garante que o diretório do output existe | `bool` |
| `resolve_output_path(input_path, suffix, output_dir)` | Resolve caminho com sufixo no nome | `str` |

**Detalhamento:**

**`get_rgb_arrays(path, tool_key)`** — Lê as bandas RGB de um LAS como arrays numpy dtype int64.
Retorna dict vazio se o LAS não tiver RGB ou em caso de erro.
Levanta `FileNotFoundError` / `ValueError` nas validações de path.

**`create_filtered_las(las, mask, output_path, tool_key)`** — Cria um novo arquivo LAS aplicando uma máscara booleana aos pontos do objeto `LasData` original.
- `las`: objeto `laspy.LasData` original (fornece header e pontos).
- `mask`: array booleano numpy (True = manter).
- `output_path`: caminho para salvar o novo LAS.
- Retorna `int` (nº de pontos salvos) ou `None` se houve erro.
- Se a máscara for vazia (0 pontos), retorna 0 sem salvar.

**`ensure_output_dir(output_path, tool_key)`** — Cria o diretório pai do caminho com `os.makedirs(exist_ok=True)`.
Retorna True se o diretório existe (ou foi criado), False em caso de erro.

**`resolve_output_path(input_path, suffix="_filtrado", output_dir=None)`** — Gera um caminho de saída combinando diretório (opcional), nome base do input e sufixo antes da extensão.
- Se `output_dir` for None, mantém o mesmo diretório do input.
- Exemplo: `"c:/dados/nuvem.las"` + `"_filtrado"` → `"c:/dados/nuvem_filtrado.las"`

**Regras:**
- Todos os métodos aceitam `tool_key: str = ToolKey.UNTRACEABLE.value`.
- Herda de `BaseUtil`.
- `get_info`, `get_rgb_arrays`: levantam `FileNotFoundError` se o arquivo não existir.
- `get_info`, `get_rgb_arrays`: levantam `ValueError` se a extensão não for `.las` ou `.laz`.
- `create_filtered_las` delega a criação de diretório para `ensure_output_dir`.

### `utils.RecentProjectsManager`

Gerencia a lista de projetos recentes em arquivo próprio.

```python
manager = RecentProjectsManager()
manager.add_recent("C:/projetos/MeuProjeto.mtl")
recents = manager.get_recents()
```

### `utils/vector/VectorLayerSource`

Leitura de dados vetoriais (.shp, .gpkg, .csv).

```python
from utils.vector.VectorLayerSource import VectorLayerSource
data = VectorLayerSource.read("dados.shp", tool_key=ToolKey.MEU_PLUGIN.value)
```

### `utils/raster/RasterLayerSource`

Leitura de metadados de rasters GeoTIFF (placeholder).

```python
from utils.raster.RasterLayerSource import RasterLayerSource
meta = RasterLayerSource.read_metadata("imagem.tif", tool_key=ToolKey.MEU_PLUGIN.value)
```

## ✅ Regras de uso

- **Nunca** duplique lógica de utilitário em plugins se já houver implementação em `utils/`.
- **Nunca** use `QFileDialog` diretamente fora de `utils.ExplorerUtils`.
- **Nunca** use `QMessageBox` diretamente fora de `utils.MessageBox`.
- **Sempre** use `JsonUtil` para JSON temporários em vez de manipulação manual de arquivos.
- **Use `FormatUtils`** para datas e tamanhos, não adicione formatação personalizada em cada lugar.
- **Use `ProjectUtil`** para `.mtl`; não manipule manualmente o formato JSON do projeto.
- **Se um utilitário não existe, crie-o em `utils/`** e documente a nova função nesta skill.
- **Toda classe util DEVE herdar de `BaseUtil`.**

## 🔧 Boas práticas

- Prefira interfaces estáticas simples e fáceis de chamar em plugins.
- Ao criar um novo utilitário, mantenha-o genérico e sem dependências de UI sempre que possível.
- Registre a nova dependência em `requirements.txt` se o utilitário precisar de uma biblioteca externa.
- Se o utilitário exige UI, a implementação deve ficar em `utils/` e expor API limpa para plugins.
- Todo método público DEVE aceitar `tool_key: str = ToolKey.UNTRACEABLE.value` como parâmetro nomeado.
- Use `BaseUtil._get_logger(tool_key, "ClassName")` para logging, nunca `LogUtils` diretamente.

## 📌 Exemplo de uso correto

```python
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.FormatUtils import FormatUtils
from utils.JsonUtil import JsonUtil

path = ExplorerUtils.open_file("Abrir arquivo", file_filter="JSON (*.json)")
if not path:
    MessageBox.show_warning("Arquivo não selecionado")
    return

content = JsonUtil.read_json(path)
MessageBox.show_info("Arquivo carregado com sucesso")
print(FormatUtils.format_size(len(str(content))))