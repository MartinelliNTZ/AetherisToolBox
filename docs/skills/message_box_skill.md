# Skill: Exibição de Mensagens para o Usuário (MessageBox)

O sistema de mensagens centraliza **todas** as chamadas a `QMessageBox` em uma única classe utilitária `MessageBox`. Nenhum código no projeto pode importar ou usar `QMessageBox` diretamente — **sempre** utilize `MessageBox`.

## 📦 Onde fica

```python
from utils.MessageBox import MessageBox
```

## 🧩 Métodos Disponíveis

### `show_error` — Erro
Exibe uma mensagem de erro com ícone de crítica.

```python
MessageBox.show_error("Falha ao carregar o arquivo")
MessageBox.show_error(
    "Conexão com o servidor perdida",
    title="Erro de Rede",           # opcional, padrão: "Erro"
    detail="Detalhes técnicos...",  # opcional, seção "Mostrar Detalhes"
)
```

### `show_info` — Informação
Exibe uma mensagem informativa.

```python
MessageBox.show_info("Operação concluída com sucesso")
MessageBox.show_info("Arquivo salvo em: dados/resultado.tif", title="Sucesso")
```

### `show_warning` — Aviso
Exibe um aviso amarelo.

```python
MessageBox.show_warning("Espaço em disco baixo")
MessageBox.show_warning("Campo obrigatório não preenchido", title="Validação")
```

### `show_critical` — Erro Crítico
Exibe um erro crítico (igual ao `show_error` mas com título padrão diferente).

```python
MessageBox.show_critical(
    "Falha fatal na inicialização do sistema",
    title="Erro Fatal",
    detail=traceback_text,
)
```

### `show_question` — Pergunta (retorna botão pressionado)
Exibe uma pergunta ao usuário e retorna o botão pressionado.

```python
resposta = MessageBox.show_question("Deseja salvar as alterações?")
if resposta == MessageBox.YES:
    salvar()

# Com botões personalizados
resposta = MessageBox.show_question(
    "O que deseja fazer?",
    title="Salvar?",
    detail="Você tem alterações não salvas.",
    buttons=MessageBox.YES_NO_CANCEL,       # opcional
    default_button=MessageBox.NO,           # foco no "Não"
)
```

### `show` — Genérico (uso avançado)
Para casos específicos não cobertos pelos métodos acima.

```python
MessageBox.show(
    "Mensagem personalizada",
    title="Título",
    detail="Detalhes...",
    icon=QMessageBox.Icon.Warning,          # custom
    buttons=MessageBox.OK_CANCEL,
    default_button=MessageBox.CANCEL,
)
```

## 🎯 Constantes de Botões

| Constante | Botões |
|---|---|
| `MessageBox.OK` | OK |
| `MessageBox.YES` | Yes |
| `MessageBox.NO` | No |
| `MessageBox.CANCEL` | Cancel |
| `MessageBox.YES_NO` | Yes + No |
| `MessageBox.YES_NO_CANCEL` | Yes + No + Cancel |
| `MessageBox.OK_CANCEL` | OK + Cancel |

## 📝 Regras de Uso

### 🔴 Obrigatório
- **Sempre** importe de `utils.MessageBox` — nunca use `QMessageBox` diretamente.
- Use os métodos nomeados (`show_error`, `show_info`, `show_warning`, `show_critical`, `show_question`) em vez do genérico `show` sempre que possível.

### 🟡 Boas Práticas
- **Mensagens curtas e diretas** no primeiro parâmetro (`text`).
- Use `detail` para informações técnicas extensas (traceback, logs, etc.).
- Para perguntas com `YES_NO`, prefira `MessageBox.show_question` sem precisar de `buttons=YES_NO` (já é o padrão).
- Para confirmações destrutivas, use `default_button=MessageBox.NO`.

### 🟢 Recomendado
```python
# ✅ Correto
MessageBox.show_error("Falha ao abrir arquivo", detail=traceback_text)

# ✅ Correto — pergunta com padrão seguro
if MessageBox.show_question(
    "Excluir arquivo permanentemente?",
    title="Confirmar Exclusão",
    default_button=MessageBox.NO,
) == MessageBox.YES:
    excluir()
```

```python
# ❌ ERRADO — importar QMessageBox diretamente
from PySide6.QtWidgets import QMessageBox  # NUNCA FAÇA ISSO

# ❌ ERRADO — usar QMessageBox diretamente
QMessageBox.warning(self, "Aviso", "Texto")  # NUNCA FAÇA ISSO
```

## 🔧 Comportamento Interno

A classe `MessageBox` cuida automaticamente de:

1. **Parent automático** — Se `parent` não for informado, busca a janela ativa da aplicação.
2. **Criação da QApplication** — Se não houver `QApplication` rodando (ex: erro antes do startup), cria uma nova para garantir que o diálogo apareça.
3. **Tratamento de erros silencioso** — Se algo falhar na exibição do diálogo, o erro é logado mas não quebra a aplicação.

## 🧪 Exemplo Completo

```python
from utils.MessageBox import MessageBox

class MinhaTool(BasePlugin):
    def _validar(self):
        if not self._campo.text().strip():
            MessageBox.show_warning(
                "O campo não pode estar vazio.",
                title="Validação",
            )
            return False

        confirm = MessageBox.show_question(
            "Deseja processar os dados?",
            title="Confirmar",
            buttons=MessageBox.YES_NO,
            default_button=MessageBox.YES,
        )
        if confirm != MessageBox.YES:
            return False

        return True

    def _processar(self):
        try:
            resultado = self._executar_pipeline()
            MessageBox.show_info(f"Processamento concluído: {resultado}")
        except Exception as e:
            MessageBox.show_error(
                "Erro durante o processamento",
                title="Pipeline",
                detail=traceback.format_exc(),
            )
```

---