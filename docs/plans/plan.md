📋 Plano de Ação: Ferramenta "Filtro de Pontos Pretos LAS/LAZ"
🎯 Funcionalidades
Filtrar pontos pretos (R=G=B=0 ou abaixo de limiar configurável) de uma nuvem de pontos LAS/LAZ
Não altera o arquivo original — sempre gera um novo arquivo
Checkbox para salvar os pontos pretos filtrados em um arquivo separado - USE GRIDCHECKBOX
Campo para definir o nome base do(s) arquivo(s) de saída - SelectorGrid    O ARQUIVO DE PONTOS PRETOS DEVE SER SALVO APENAS SE O CHECKBOX ESTIVER MARCADO E ONOME DELE PODE SER O NOME DO ARQUIVO ORIGINAL + "_pretos.las" OU "_pretos.laz" DEPENDENDO DO FORMATO DE ENTRADA

BOTOES EXTRAS 
    SALVAR O ARQUIVO NA ORIGEM = NOME ORIGINAL + _filtrado.las/laz e SE MARCADO SALVAR O ARQUIVO DE PONTOS PRETOS NA ORIGEM COM NOME ORIGINAL + _pretos.las/laz
    SALVAR NO PROJETO VERIFICA SE EXISTE UM PROJETO ATIVO SE NAO TIVER NAO FAZ NADA SO EXIBE MENSAGEM, SE TIVER PROJETO ATIVO SALVA NA PASTA DO PROJETO COM NOME ORIGINAL + _filtrado.las/laz e SE MARCADO SALVA O ARQUIVO DE PONTOS PRETOS NA PASTA DO PROJETO COM NOME ORIGINAL + _pretos.las/laz O CAMINHO  DE SALVAMENTO DEVE SER  RAIZ PROJETO/las/black_points_filter/ + NOME DO ARQUIVO use a explorer utils + @/plugins\project_manager\SaveProjectPlugin.py (current project provavelmente ta nas prefs leia a doc) A RESPONSABILIDADE É DE QUEM FAZER ISSO? ESSA RESPONSABILIDADE DEVE SER PASSADO PARA O WIDGET, simplector e selectorgrid ele ja tem esse sistema de pasta do projeto basta implementar corretamten 


Progresso via SignalManager (ProgressBar + HUD + Console)
Logs estruturados via BasePlugin.logger USE self.logger ja que basepluign e pai 
1. 📁 Arquivos a Criar
1.1 plugins/las_black_filter/LasBlackFilterPlugin.py
Propósito: Widget principal da ferramenta. Herda de BasePlugin, implementa toda a UI e lógica de filtragem.

1.2 plugins/las_black_filter/__init__.py
Propósito: Inicializador do pacote (vazio, apenas para tornar o diretório um pacote Python).

2. 🔧 Arquivos a Modificar
2.1 core/enum/ToolKey.py
O que muda: Adicionar LAS_BLACK_FILTER = "LasBlackFilter" ao enum.

2.2 core/config/ToolRegistry.py
O que muda: Adicionar entrada no dict _TOOLS:


ToolKey.LAS_BLACK_FILTER.value: Tool(
    name=ToolKey.LAS_BLACK_FILTER.value,
    title="Filtro Pontos Pretos",
    widget_factory=_make_factory(
        "plugins.las_black_filter.LasBlackFilterPlugin",
        "LasBlackFilterPlugin",
    ),
    tooltip="Remove pontos pretos (R=G=B=0) de nuvens LAS/LAZ",
    tool_type=ToolType.RASTER,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
2.3 requirements.txt
O que muda: Adicionar laspy como dependência (biblioteca para leitura/escrita de LAS/LAZ).

3. 🧱 Estrutura da UI
Layout seguindo Contrato 18 (Título → Separator → ExecutionButtons → conteúdo):


┌─────────────────────────────────────────────────┐
│  PluginPage (title="Filtro de Pontos Pretos")    │
│  ─ Separator ────────────────                     │
│  [ExecutionButtons]                               │
│    [SELECIONAR LAS][USAR ORIGEM] ← secondary                  │
│    [EXECUTAR]       ← primary                    │
│                                                   │
│  ── GroupPainel "Arquivo de Entrada" ──           │
│    GRIDSelector (LAS/LAZ)                       │
│    GridLabel (info do arquivo)                    │
│                                                   │
│  ── GroupPainel "Configurações" ──                │
│    GridDoubleSpinBox (limiar preto)               │
│    GridLineEdit (nome base saída)                 │
│    GridCheckBox (salvar pontos pretos)            │
│                                                   │
│  ── GroupPainel "Arquivos de Saída" ──            │
│    GridLabel (caminhos gerados)                   │
└─────────────────────────────────────────────────┘
Widgets reutilizáveis (já existentes em resources/widgets/):
Widget	Uso
SimpleSelector	Selecionar arquivo LAS/LAZ de entrada
ExecutionButtons	Botões "SELECIONAR LAS" e "EXECUTAR" (botao usar origem  ele adicionam o caminho ao simpleselector)
GroupPainel	Agrupar seções (Entrada, Config, Saída)
GridDoubleSpinBox	Campo do limiar de preto (0–255, default 0)
GridLineEdit	Campo do nome base do arquivo de saída NAO SERA NOME BASE E sim SULFIXO _filtrado.las/laz e para o arquivo de pontos pretos _pretos.las/laz 
        (regra complexa, quando clicar em usar pasta do projeto o nome do arquivo deve usar o path + nome do aruqivo de orgibem mais o sulfixo do filtrado, )
GridCheckBox	Checkbox "Salvar pontos pretos filtrados"
GridLabel	Exibir info do LAS carregado e caminhos de saída
PluginPage	Container base (já usado pelo BasePlugin._build_ui())
Nenhum widget novo precisa ser criado — todos os componentes necessários já existem no catálogo.

4. 🔄 Fluxo de Execução
Passo a passo:
Usuário clica "SELECIONAR LAS" → ExplorerUtils.open_file() com filtro "LAS/LAZ (*.las *.laz)"
Caminho é exibido no SimpleSelector e info do arquivo carregada via laspy:
Total de pontos
Tem RGB? (se não tiver, desabilita EXECUTAR com warning)
Bounding box
GridLabel atualizado com metadata
Usuário configura:
Limiar de preto (default 0, significa R=G=B=0)
Nome base do arquivo filtrado (default: <original>_sem_pretos.las)
Checkbox "Salvar pontos pretos" + nome base
Usuário clica "EXECUTAR":
SignalManager.execution_started.emit("LasBlackFilter") — MainWindow mostra HUD + reseta ProgressBar
SignalManager.hud_show.emit({"message": "Filtrando pontos pretos..."})
SignalManager.console_message.emit("[LasBlackFilter] Iniciando filtro...")
Logger: self.logger.info("Iniciando filtro", code="FILTER_START", ...)
Abre o LAS com laspy.read()
Aplica filtro: (red > limiar) | (green > limiar) | (blue > limiar)
Salva LAS limpo com nome definido
Se checkbox marcado, salva LAS apenas com pontos pretos
Durante o processo, emite progress_update (0–100) e hud_update
SignalManager.execution_finished.emit("LasBlackFilter")
SignalManager.console_message.emit("[LasBlackFilter] Concluído! N pontos removidos.")
MessageBox.show_info() exibindo resultado: total de pontos, removidos, restantes, caminhos salvos
Logger: self.logger.info("Filtro concluído", code="FILTER_DONE", removidos=n, ...)
Tratamento de erros:
Arquivo sem RGB: MessageBox.show_warning() + desabilita EXECUTAR
Arquivo não encontrado: log + mensagem via SignalManager
Exceção durante leitura/escrita: except Exception as e: self.logger.error(...) + execution_cancelled + MessageBox.show_error()
5. ⚡ Sinais e Comunicação
Sinal	Quando emitir
execution_started	Início do filtro
execution_finished	Filtro concluído com sucesso
execution_cancelled	Erro ou cancelamento
progress_update	Durante leitura do LAS e escrita (0.0–100.0)
hud_show	Início do processamento
hud_update	Durante processamento (progresso + mensagem)
hud_hide	Fim do processamento (MainWindow faz automaticamente via execution_finished)
console_message	Mensagens de status para o ConsolePlugin
tool_opened	Automático (BasePlugin)
tool_closed	Automático (BasePlugin.closeEvent)
Logger (via self.logger):

info("Ferramenta inicializada", code="TOOL_READY") — no __init__
info("Arquivo LAS carregado", code="LAS_LOADED", path=path, points=n) — ao carregar
info("Iniciando filtro", code="FILTER_START", limiar=limiar) — ao executar
info("Filtro concluído", code="FILTER_DONE", removidos=n, restantes=n) — sucesso
error("Erro no filtro", code="FILTER_ERR", error=str(e)) — exceção
6. 💾 Preferências
Persistidas via load_prefs() / save_prefs():

Chave	Tipo	Default	Widget
last_path	str	""	Último LAS carregado
limiar	int	0	GridDoubleSpinBox
nome_base_limpo	str	""	GridLineEdit
salvar_pretos	bool	False	GridCheckBox
nome_base_pretos	str	""	GridLineEdit (do checkbox)
7. ✅ Checklist de Verificação
 ToolKey adicionado ao Enum (ToolKey.LAS_BLACK_FILTER = "LasBlackFilter")
 Widget herda de BasePlugin
 Implementa load_prefs() e save_prefs()
 Registrado no ToolRegistry com factory, category=CENTRAL, tool_type=RASTER
 Widgets reutilizáveis consultados (Contrato 11) — SimpleSelector, ExecutionButtons, GroupPainel, GridDoubleSpinBox, GridLineEdit, GridCheckBox, GridLabel
 ExecutionButtons usado para botões de ação (Contrato 18)
 SignalManager para comunicação (progress_update, hud_, console_message, execution_)
 Logs obrigatórios inseridos (inicialização, início/fim de processo, erros)
 Contratos respeitados: sem QMessageBox (usa MessageBox), sem QFileDialog (usa ExplorerUtils), sem except: sem log
 Dependências adicionadas ao requirements.txt (laspy)
 Atualização de documentação se necessário (Contrato 12) — nenhuma skill precisa ser alterada pois não criamos widgets novos
 Nenhum widget novo criado em resources/widgets/ — tudo já existe no catálogo
📝 Observações Finais
EST3.PY usado como referência para a lógica de filtragem (_filtrar_pontos_pretos()), que será adaptada para o padrão de plugin.
Sem dependência GDAL/rasterio — apenas laspy para LAS/LAZ + numpy já presente.
Interface enxuta — apenas 2 botões no ExecutionButtons (selecionar + executar).
Modo SEGURO — nunca altera o arquivo original, apenas cria novos.