# Skill: Sistema de Estilos e Temas (Styles)

Esta skill documenta o sistema de estilos e temas do **Aetheris ToolBox**, descrevendo sua arquitetura baseada em tokens semânticos, como criar novos temas, e como usar estilos em widgets e plugins.

---

## 📋 Visão Geral

O sistema implementa uma **arquitetura de temas baseada em tokens semânticos** com 18 grupos de tokens organizados por categoria (ACCENT, SURFACE, TEXT, BORDER, RADIUS, SPACE, etc.). Cada tema concreto herda de `BaseTheme` e sobrescreve todos os tokens com valores específicos.

```
BaseTheme (abstrato) ← DarkCharcoalTheme, ZeroGrausTheme, BlueTheme
       ↑
ThemeManager (singleton) — carrega o tema ativo das preferências
       ↑
BaseStyle (estilos globais QSS) ← AppStyles (botões, badges, menus, logs, toolbar)
       ↑
AnimationManager (animações via QPropertyAnimation — hover grow, bounce)
```

**Novidade:** `AnimationManager` é o gerenciador central de animações Qt. Ele cria animações de hover grow, bounce e qualquer transição de propriedade numérica. Atualmente usado pelo `ToolbarButton` para animar o crescimento no hover.

**Princípios:**
- **Zero valores hardcoded** — todo QSS usa tokens do tema via `ct.theme.ATRIBUTO`
- **Tema ativo lido das preferências** — salvo em `System > "theme"` no `preferences.json`
- **Lazy loading de temas** — só importa o módulo do tema ativo no startup
- **Compatibilidade retroativa** — aliases antigos (BG_DARK, GOLD, etc.) mapeiam para tokens semânticos

---

## 🧱 Arquitetura

```
resources/styles/
├── __init__.py               — Exporta classes públicas (AnimationManager, AppStyles, BaseStyle, BaseTheme, DarkCharcoalTheme, ThemeManager, ct)
├── BaseTheme.py              — Classe base abstrata com TODOS os tokens semânticos (18 grupos)
├── DarkCharcoalTheme.py      — Tema concreto: Dark Charcoal + Gold (padrão)
├── ZeroGrausTheme.py         — Tema concreto: Ice Glass / Frozen Crystal
├── BlueTheme.py              — Tema concreto: Modern Dashboard (azul elétrico)
├── BaseStyle.py              — Gera QSS global usando o tema ativo
├── AppStyles.py              — Herda BaseStyle + estilos de botões, badges, logs, menus, tabs, toolbar
├── AnimationManager.py       — Gerenciador central de animações Qt (hover grow, bounce, QPropertyAnimation)
└── ThemeManager.py           — Singleton que mantém o tema ativo e gerencia troca de temas
```

---

## 📦 Componentes

### `BaseTheme` — `resources/styles/BaseTheme.py`

Classe base abstrata que define **todos os tokens semânticos** do sistema. Cada tema concreto deve sobrescrever todos os atributos.

**18 grupos de tokens:**

| # | Grupo | Prefixo | Descrição | Exemplo |
|---|-------|---------|-----------|---------|
| 1 | **ACCENT** | `ACCENT_*` | Cores de destaque principal | `ACCENT`, `ACCENT_HOVER`, `ACCENT_GRADIENT` |
| 2 | **SURFACE** | `SURFACE_*` | Níveis de profundidade (0=fundo…5=topo) | `SURFACE_0` a `SURFACE_5`, `TITLE_BAR` |
| 3 | **TEXT** | `TEXT_*` | Hierarquia tipográfica | `TEXT_HIGH`, `TEXT_MEDIUM`, `TEXT_LOW`, `TEXT_DISABLED` |
| 4 | **BORDER** | `BORDER_*` | Hierarquia de bordas | `BORDER_SUBTLE`, `BORDER_DEFAULT`, `BORDER_STRONG` |
| 5 | **SHADOW** | `SHADOW_*` | Sombras por tamanho | `SHADOW_SM`, `SHADOW_MD`, `SHADOW_LG`, `SHADOW_XL` |
| 6 | **RADIUS** | `RADIUS_*` | Escala global de cantos arredondados | `RADIUS_XS`(2) a `RADIUS_XL`(16), `RADIUS_FULL` |
| 7 | **SPACE** | `SPACE_*` | Escala global de espaçamento | `SPACE_XXS`(2) a `SPACE_3XL`(48) |
| 8 | **ICON** | `ICON_*` | Tamanhos de ícone | `ICON_XS`(12) a `ICON_XL`(32), `TOOLBAR_ICON_SIZE`(20) |
| 9 | **ANIMATION** | `ANIMATION_*` | Durações de animação (ms) | `ANIMATION_FAST`(120), `ANIMATION_SLOW`(260) |
| 10 | **OPACITY** | `OPACITY_*` | Níveis de opacidade | `OPACITY_DISABLED`(0.35), `OPACITY_ACTIVE`(1.0) |
| 11 | **LAYOUT** | `*` | Layout global | `PAGE_PADDING`, `SECTION_GAP`, `GRID_GAP` |
| 12 | **ELEVATION** | `ELEVATION_*` | Níveis de elevação (z-index) | `ELEVATION_FLAT` a `ELEVATION_HIGH` |
| 13 | **OVERLAY** | `OVERLAY_*` | Sobreposições / glass effect | `OVERLAY_BG`, `BACKDROP_BLUR` |
| 14 | **FOCUS_RING** | `FOCUS_RING_*` | Anel de foco visual | `FOCUS_RING_COLOR`, `FOCUS_RING_WIDTH` |
| 15 | **STATUS** | `COLOR_*` | Cores de estado semântico | `COLOR_SUCCESS`, `COLOR_WARNING`, `COLOR_DANGER`, `COLOR_INFO` |
| 16 | **FONT** | `FONT_*` | Tipografia | `FONT_FAMILY_DEFAULT`, `FONT_SIZE_NORMAL`, `FONT_WEIGHT_BOLD` |
| 17 | **DIMENSIONS** | `*` | Alturas e tamanhos de widgets | `INPUT_HEIGHT`, `BUTTON_HEIGHT`, `SCROLLBAR_WIDTH`, `TOOLBAR_BTN_SIZE` |
| 18 | **SPECIFICS** | `BORDER_RADIUS_*`, `*_PADDING`, etc. | Tokens específicos de implementação | `BORDER_RADIUS_CARD`, `BADGE_PADDING_V`, `MENU_PADDING` |

**Aliases de compatibilidade retroativa** (mapeiam nomes antigos → tokens semânticos):

| Alias Antigo | Token Semântico |
|-------------|-----------------|
| `BG_DEEPEST` | `SURFACE_0` |
| `BG_DARK` | `SURFACE_1` |
| `BG_PANEL` | `SURFACE_2` |
| `BG_CARD` | `SURFACE_3` |
| `BG_ELEVATED` | `SURFACE_4` |
| `BG_SURFACE` | `SURFACE_5` |
| `GOLD` | `ACCENT` |
| `GOLD_HOVER` | `ACCENT_HOVER` |
| `GOLD_DIM` | `ACCENT_DIM` |
| `TEXT_BRIGHT` | `TEXT_HIGH` |
| `TEXT_PRIMARY` | `TEXT_MEDIUM` |
| `TEXT_SECONDARY` | `TEXT_LOW` |
| `TEXT_MUTED` | `TEXT_DISABLED` |
| `TEXT_GOLD` | `ACCENT_TEXT` |
| `BORDER` | `BORDER_DEFAULT` |
| `BORDER_HOVER` | `BORDER_ACCENT` |
| `SUCCESS` | `COLOR_SUCCESS` |
| `WARNING` | `COLOR_WARNING` |
| `DANGER` | `COLOR_DANGER` |

---

### `ThemeManager` — `resources/styles/ThemeManager.py`

Singleton que mantém a instância do tema ativo. Gerencia carregamento dinâmico e troca de temas.

```python
from resources.styles.ThemeManager import ct

# Acessar tokens do tema atual
cor_fundo = ct.theme.SURFACE_1
cor_texto = ct.theme.TEXT_MEDIUM
fonte = ct.theme.FONT_FAMILY_DEFAULT

# Metadados do tema ativo
chave = ct.current_key          # "dark_charcoal"
info = ct.current_info          # {"module": ..., "label": ..., "description": ...}

# Listar temas disponíveis
temas = ThemeManager.available_themes()
for key, meta in temas.items():
    print(f"{meta['label']}: {meta['description']}")

# Recarregar tema (após alterar preferência)
ct.reload_theme()
```

**Propriedades e métodos:**

| Método/Propriedade | Retorno | Descrição |
|-------------------|---------|-----------|
| `ct.theme` | `BaseTheme` | Instância do tema atual |
| `ct.current_key` | `str` | Chave do tema ativo (lida das preferências) |
| `ct.current_info` | `dict` | Metadados completos do tema ativo |
| `ThemeManager.available_themes()` | `dict[str, dict]` | Todos os temas registrados |
| `ct.reload_theme()` | `None` | Recria a instância do tema |

**Temas registrados no dicionário `THEMES`:**

| Chave | Classe | Label | Descrição |
|-------|--------|-------|-----------|
| `"dark_charcoal"` | `DarkCharcoalTheme` | Dark Charcoal | Tema escuro minimalista com detalhes em dourado |
| `"zero_graus"` | `ZeroGrausTheme` | Zero Graus | Tema cristalino Ice Glass, tons azulados profundos |
| `"blue_theme"` | `BlueTheme` | Blue Theme | Tema inspirado em Modern Dashboard UI, azul elétrico |

**Tema ativo é lido das preferências do sistema:**

```python
# Salvo em config/preferences.json na seção System
# Chave: "theme" → valor: "dark_charcoal" | "zero_graus" | "blue_theme"
sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
tema_atual = sys_prefs.get("theme", "dark_charcoal")  # padrão: dark_charcoal
```

---

### `BaseStyle` — `resources/styles/BaseStyle.py`

Gera o **stylesheet global** do Qt usando o tema ativo. Cobre todos os widgets base do sistema.

```python
from resources.styles.AppStyles import AppStyles

# Aplicar stylesheet global na aplicação
app.setStyleSheet(AppStyles.global_stylesheet())
```

**Componentes cobertos pelo QSS global:**

| Seção | Widgets |
|-------|---------|
| **ScrollBar** | `QScrollBar:vertical`, `QScrollBar::handle:vertical` |
| **GroupBox** | `QGroupBox`, `QGroupBox::title` |
| **Label** | `QLabel`, `QLabel#header_title`, `QLabel#header_subtitle`, `QLabel#section_badge` |
| **Title Bar** | `QWidget#title_bar`, `QLabel#window_title`, `QPushButton#title_btn`, `QPushButton#title_btn_close` |
| **AppBar Toolbar** | `QWidget#appbar_toolbar`, `QPushButton#toolbar_btn` |
| **Side Panel** | `QWidget#tool_side_panel`, `QPushButton#tool_selector_btn` |
| **Console Toolbar** | `QWidget#console_toolbar` |
| **Workspace Tabs** | `QTabBar#workspace_tabs`, `QTabBar::tab`, `QTabBar::close-button` |
| **Splitter** | `QSplitter::handle`, `QSplitter#workspace_splitter::handle` |
| **Line Edit** | `QLineEdit`, `QLineEdit:focus`, `QLineEdit:disabled` |
| **Spin Box** | `QSpinBox`, `QDoubleSpinBox`, `QSpinBox::up-button` |
| **Combo Box** | `QComboBox`, `QComboBox::drop-down`, `QComboBox QAbstractItemView` |
| **Check Box** | `QCheckBox`, `QCheckBox::indicator` |
| **Table** | `QTableWidget`, `QTableWidget::item`, `QHeaderView::section` |
| **Text Browser/Edit** | `QTextBrowser`, `QTextEdit` |
| **Progress Bar** | `QProgressBar`, `QProgressBar::chunk` |

---

### `AnimationManager` — `resources/styles/AnimationManager.py`

Gerenciador central de animações Qt via `QPropertyAnimation`. Cria animações reutilizáveis sem necessidade de subclasses ou event filters manuais.

Atualmente usado pelo `ToolbarButton` para animar hover grow (botão + ícone aumentam ao passar o mouse).

```python
from resources.styles.AnimationManager import AnimationManager
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `animate_property(widget, prop, start, end, duration, easing)` | Animação genérica de qualquer propriedade Qt |
| `animate_hover_grow(widget, grow_px, grow_icon_px, duration)` | Configura hover grow (enter/leave) no widget |
| `animate_bounce(widget, prop, start, peak, end, duration)` | Animação bounce (vai ao pico e retorna) |
| `clear_hover_grow(widget)` | Remove animação hover grow |

**Uso — Hover Grow (padrão para ToolbarButton):**

```python
from resources.styles.AnimationManager import AnimationManager

# Hover grow com valores default do tema
AnimationManager.animate_hover_grow(widget)

# Custom:
AnimationManager.animate_hover_grow(
    widget,
    grow_px=4,          # botão aumenta 4px
    grow_icon_px=24,    # ícone vai para 24x24 no hover
    duration=120,       # duração em ms
)
```

**Uso — Animação genérica:**

```python
anim = AnimationManager.animate_property(
    widget,
    b"minimumSize",
    QSize(32, 32),
    QSize(52, 52),
    duration=180,
    easing=QEasingCurve.Type.OutCubic,
)
```

**Como funciona `animate_hover_grow`:**
1. Salva os handlers `enterEvent`/`leaveEvent` originais do widget
2. No Enter: anima `minimumSize`, `maximumSize` e `iconSize` para valores maiores
3. No Leave: anima de volta para os valores originais
4. Propaga o evento para o handler original (preservando tooltip, cursor, etc.)

**Tokens do tema usados:**
- `TOOLBAR_BTN_HOVER_GROW` — pixels extras no hover
- `ANIMATION_FAST` — duração da animação (ms)

---

### `AppStyles` — `resources/styles/AppStyles.py`

Herda de `BaseStyle` e adiciona estilos específicos da aplicação: botões, badges, logs, menus, tabs e diálogos.

**Métodos de botões:**

| Método | Descrição | Uso |
|--------|-----------|-----|
| `btn_secondary_style()` | Botão secundário — gradiente suave, hover com glow | `SimpleSecondaryButton` |
| `btn_primary_style()` | Botão primário — gradiente dourado/acento | `SimplePrimaryButton` |
| `btn_danger_style()` | Botão de perigo — vermelho escuro | `SimpleDangerButton` |
| `btn_ghost_style()` | Botão ghost — invisível, aparece no hover | `SimpleGhostButton` |
| `btn_remove_style()` | Botão remover — preto, hover vermelho | `SimpleRemoveButton` |

**Métodos de badges:**

| Método | Cor | Uso |
|--------|-----|-----|
| `badge_success()` | `COLOR_SUCCESS` | Operação concluída |
| `badge_running()` | `COLOR_WARNING` | Processando |
| `badge_error()` | `COLOR_DANGER` | Erro |
| `badge_canceled()` | `COLOR_WARNING` | Cancelado |
| `badge_info()` | `COLOR_INFO` | Informativo |

**Métodos de menu:**

| Método | Descrição |
|--------|-----------|
| `menu_bar_style()` | Estilo da `QMenuBar` (tabs + barra) |
| `menu_dropdown_style()` | Estilo do `QMenu` (dropdown suspenso) |

**Métodos de diálogo:**

| Método | Descrição |
|--------|-----------|
| `dialog_stylesheet()` | QSS genérico para `QDialog` |
| `dialog_content_border_style()` | Borda sutil para content widget do `BaseDialog` |
| `about_dialog_stylesheet()` | QSS completo para `AboutDialog` |

**Métodos de tab (cores para paintEvent custom):**

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `tab_common_colors()` | `dict[str, str]` | Cores padronizadas para tabs (vertical e horizontal) |
| `theme_colors()` | `dict[str, str]` | Todas as cores do tema atual (cacheado) |
| `vertical_tab_colors()` | `dict[str, str]` | Cores para pintura manual do `VerticalTab` |

**Métodos de log HTML:**

| Método | Descrição |
|--------|-----------|
| `log_html(text, timestamp, color, ts_color, weight)` | Linha de log formatada com timestamp |
| `log_link_html(text, url)` | Link clicável para log |
| `log_section_html(text)` | Título de seção para log |

**Métodos de CollapsibleParams:**

| Método | Descrição |
|--------|-----------|
| `collapsible_header_height()` | Altura do header |
| `collapsible_header_style()` | Estilo do header clicável |
| `collapsible_content_style()` | Estilo do container de conteúdo |

**Métodos de RecentProjectsMenu:**

| Método | Descrição |
|--------|-----------|
| `recent_project_name_style(active)` | Estilo do nome do projeto |
| `recent_project_sub_style(active)` | Estilo do path/data |
| `recent_project_hover_style()` | Cor de fundo hover |
| `recent_project_hover_name_style()` | Estilo do nome no hover |
| `recent_project_hover_sub_style()` | Estilo do path/data no hover |

---

### Temas Concretos

#### `DarkCharcoalTheme` — `resources/styles/DarkCharcoalTheme.py`

Tema padrão do sistema. Visual minimalista escuro com detalhes em dourado.

```python
ACCENT = "#C9A84C"           # Dourado
SURFACE_0 = "#08080A"        # Fundo absoluto (quase preto)
SURFACE_1 = "#0C0C0F"        # Fundo padrão
SURFACE_2 = "#121216"        # Painéis
SURFACE_3 = "#18181D"        # Cards
SURFACE_4 = "#1E1E24"        # Elementos elevados
SURFACE_5 = "#24242B"        # Superfície hover
TEXT_HIGH = "#F0F0F0"        # Títulos
TEXT_MEDIUM = "#DCDCDC"      # Corpo
TEXT_LOW = "#888890"         # Secundário
```

#### `ZeroGrausTheme` — `resources/styles/ZeroGrausTheme.py`

Tema cristalino Ice Glass. Tons azulados profundos com acento ciano.

```python
ACCENT = "#7FE8FF"           # Crystal Cyan
SURFACE_0 = "#02060A"        # Deep Arctic Glass
SURFACE_1 = "#071018"
SURFACE_2 = "#0C1824"
SURFACE_3 = "#122131"
SURFACE_4 = "#173046"
SURFACE_5 = "#1C3E59"
TEXT_HIGH = "#F7FDFF"        # Branco gelo
```

#### `BlueTheme` — `resources/styles/BlueTheme.py`

Tema inspirado em Modern Dashboard UI. Azul elétrico vibrante.

```python
ACCENT = "#1EA7FF"           # Azul elétrico
SURFACE_0 = "#050B1A"        # Navy profundo
SURFACE_1 = "#081426"
SURFACE_2 = "#0C1D35"
SURFACE_3 = "#102744"
SURFACE_4 = "#183355"
SURFACE_5 = "#21426B"
TEXT_HIGH = "#FFFFFF"        # Branco puro
```

---

## 🎯 Como Usar

### Em Widgets (QSS via stylesheet)

```python
from resources.styles.AppStyles import AppStyles

# Aplicar estilo de botão primário
btn.setStyleSheet(AppStyles.btn_primary_style())

# Aplicar badge de sucesso
badge.setStyleSheet(AppStyles.badge_success())

# Aplicar estilo de menu dropdown
menu.setStyleSheet(AppStyles.menu_dropdown_style())
```

### Em paintEvent (cores para pintura manual)

```python
from resources.styles.AppStyles import AppStyles

def paintEvent(self, event):
    colors = AppStyles.theme_colors()
    painter.fillRect(rect(), QColor(colors["BG_DEEPEST"]))
    painter.setPen(QColor(colors["GOLD"]))
    painter.drawText(rect(), "Texto")
```

### Em tabs custom (VerticalTab, HorizontalTab)

```python
from resources.styles.AppStyles import AppStyles

P = AppStyles.tab_common_colors()
if self.selected:
    painter.fillRect(rect(), QColor(P["bg_selected"]))
    painter.setPen(QColor(P["fg_selected"]))
else:
    painter.fillRect(rect(), QColor(P["bg_default"]))
    painter.setPen(QColor(P["fg_default"]))
```

### Em logs HTML

```python
from resources.styles.AppStyles import AppStyles
from resources.styles.ThemeManager import ct

html = AppStyles.log_html(
    text="Processamento concluído",
    timestamp="14:30:00",
    color=ct.theme.COLOR_SUCCESS,
    ts_color=ct.theme.TEXT_LOW,
)
browser.append(html)
```

### Aplicar stylesheet global

```python
from PySide6.QtWidgets import QApplication
from resources.styles.AppStyles import AppStyles

app = QApplication([])
app.setStyleSheet(AppStyles.global_stylesheet())
```

---

## 🆕 Como Criar um Novo Tema

1. **Crie o arquivo** em `resources/styles/MeuTema.py`
2. **Herde de `BaseTheme`** e sobrescreva **todos** os atributos
3. **Registre no `ThemeManager.THEMES`** adicionando entrada no dicionário
4. **Altere a preferência** `System > "theme"` para a chave do novo tema
5. **Recarregue** com `ct.reload_theme()` ou reinicie a UI

```python
# resources/styles/MeuTema.py
from resources.styles.BaseTheme import BaseTheme

class MeuTema(BaseTheme):
    ACCENT = "#FF6600"
    ACCENT_HOVER = "#FF8833"
    # ... sobrescrever TODOS os tokens ...
    SURFACE_0 = "#0A0A0A"
    SURFACE_1 = "#141414"
    # ...
```

```python
# Em ThemeManager.THEMES:
"meu_tema": {
    "module":      "resources.styles.MeuTema",
    "label":       "Meu Tema",
    "description": "Descrição visual do tema",
},
```

---

## ⚠️ Regras e Boas Práticas

| Regra | Descrição |
|-------|-----------|
| **Contrato 19** | Fora de `resources/styles/`, importe APENAS `AppStyles`. Nunca importe `BaseTheme`, `ThemeManager`, temas concretos ou `ct` diretamente. |
| **Zero hardcoded** | Todo QSS deve usar tokens do tema via `ct.theme.ATRIBUTO`. Nunca use cores fixas em stylesheets. |
| **Cache em paintEvent** | Use `AppStyles.theme_colors()` (cacheado) em vez de acessar `ct.theme` diretamente a 60fps. |
| **Aliases para legado** | Código antigo pode usar `BG_DARK`, `GOLD`, etc. — eles mapeiam para tokens semânticos. |
| **Tema padrão** | `dark_charcoal` é o tema padrão se não houver preferência salva. |
| **Lazy loading** | Temas são carregados sob demanda — só o módulo do tema ativo é importado. |
| **Compatibilidade** | Ao modificar `BaseTheme`, atualize todos os temas concretos para sobrescrever os novos tokens. |

---

## ✅ Checklist ao criar novo tema

- [ ] A classe herda de `BaseTheme`?
- [ ] Todos os 18 grupos de tokens foram sobrescritos?
- [ ] Os aliases de compatibilidade (BG_*, GOLD*, etc.) foram mapeados?
- [ ] O tema foi registrado no dicionário `THEMES` do `ThemeManager`?
- [ ] O módulo foi adicionado ao `__init__.py` de `resources/styles/`?
- [ ] Esta skill foi atualizada com o novo tema?

## ✅ Checklist ao usar estilos em widget

- [ ] Usei `AppStyles.método()` em vez de escrever QSS manual com cores fixas?
- [ ] Para paintEvent, usei `AppStyles.theme_colors()` ou `AppStyles.tab_common_colors()`?
- [ ] Para logs HTML, usei `AppStyles.log_html()`?
- [ ] Para badges, usei `AppStyles.badge_*()`?
- [ ] Para botões, usei `AppStyles.btn_*_style()`?
- [ ] Importei apenas `AppStyles` (nunca `BaseTheme` ou `ct` diretamente)?

---

## 🔗 Referências

- `docs/skills/SKILL_PLUGIN_CONTRACT.md` — Contrato 19 (importação de estilos)
- `docs/skills/SKILL_WIDGETS.md` — Widgets que usam estilos do AppStyles
- `resources/styles/BaseTheme.py` — Definição completa de todos os tokens
- `resources/styles/ThemeManager.py` — Gerenciamento de temas e preferências