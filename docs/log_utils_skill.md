# Skill: Utilizando o Sistema de Logs (LogUtils)

O **LogUtils** fornece uma maneira estruturada de registrar eventos em formato JSON. Ele centraliza logs de múltiplas instâncias em um único arquivo por sessão, facilitando o debug e a auditoria de processos.

## 1. Uso em Plugins (Ferramentas Registradas)

Plugins que herdam de `BasePlugin` já possuem uma instância de logger configurada automaticamente. **É obrigatório** utilizar o logger em pontos críticos (carregamento de dados, início de processos pesados e capturas de exceção).

```python
from core.model.BasePlugin import BasePlugin

class MinhaTool(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(tool_key="MinhaTool", parent=parent)
        # O self.logger já está disponível via BasePlugin
        self.logger.info("Plugin carregado e pronto")

    def processar_dados(self, dados):
        self.logger.info("Iniciando processamento", count=len(dados))
        try:
            # ... lógica ...
            pass
        except Exception as e:
            self.logger.error("Falha no processamento", error=str(e))
```

## 2. Uso em Classes Genéricas (Utils/Helpers)

Classes que não são ferramentas (e não devem ter uma `ToolKey` própria) devem aceitar um parâmetro nomeado para receber a chave da ferramenta que as chamou. Por padrão, utiliza-se `ToolKey.UNTRACEABLE` quando a origem é desconhecida.

```python
from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey

class CalculadoraEspacial:
    def __init__(self, tool_key: str = ToolKey.UNTRACEABLE.value):
        # Instancia o logger com a chave recebida
        self.logger = LogUtils(tool=tool_key, class_name=self.__class__.__name__)
        self.logger.debug("Helper instanciado")

    def calcular(self, x, y):
        self.logger.info("Executando calculo", x=x, y=y)
        return x + y
```

## 3. Uso em Classes com Métodos Estáticos

Classes utilitárias que não são instanciadas (apenas métodos estáticos) devem seguir um padrão rigoroso:
1. **Receber `tool_key`** em todos os métodos públicos.
2. **Implementar um `_get_logger` interno** para instanciar o `LogUtils` sob demanda.

```python
from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey

class FileHelper:
    @staticmethod
    def _get_logger(tool_key: str):
        """Método interno para gerar o logger com o contexto correto."""
        return LogUtils(tool=tool_key, class_name="FileHelper")

    @staticmethod
    def save_data(path, data, tool_key: str = ToolKey.UNTRACEABLE.value):
        logger = FileHelper._get_logger(tool_key)
        logger.info(f"Tentando salvar arquivo em {path}")
        
        try:
            # Lógica de salvamento...
            logger.info("Arquivo salvo com sucesso")
        except Exception as e:
            logger.error("Falha ao salvar", error=str(e))
```

---

## 4. Níveis de Log e Metadados

O logger aceita argumentos nomeados extras (`**data`) que são injetados diretamente no JSON:

| Método | Uso Recomendado |
| :--- | :--- |
| `info()` | Fluxo normal, marcos de sucesso e início/fim de tarefas. |
| `debug()` | Detalhes técnicos úteis apenas para desenvolvedores. |
| `warning()` | Situações inesperadas que não impedem a execução (ex: config faltando). |
| `error()` | Falhas que impedem uma ação específica. |
| `critical()` | Erros que podem causar crash ou corrupção de dados. |

**Exemplo com metadados:**
```python
self.logger.warning("Memória RAM atingindo limite", 
                    code="MEM_WARN", 
                    pct_used=85.5, 
                    threshold=80.0)
```