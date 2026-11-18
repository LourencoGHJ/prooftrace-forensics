# ProofTrace — Testing Guide

**Projeto:** ProofTrace  
**Documento:** Guia de Testes  
**Data:** 18/11/2026  
**Ambiente validado:** Windows 11, Python 3.13.17  
**Branch:** `docs/prooftrace-documentation`

---

## 1. Objetivo

Este documento descreve como executar os testes automatizados do ProofTrace, que cenários estão cobertos e quais são as limitações da validação atual.

Os testes verificam comportamentos específicos do código. Não constituem uma certificação de segurança, autenticidade forense ou compatibilidade universal com todos os formatos.

## 2. Ambiente de testes

Configuração observada:

| Componente | Valor |
|---|---|
| Sistema operativo | Windows 11 |
| Python | 3.13.17 |
| Versão mínima declarada | Python 3.12 |
| Ambiente virtual | `.venv` |
| Framework | pytest |
| Configuração | `pyproject.toml` |

Dependências relevantes para os testes observados:

- pytest
- pypdf
- Pillow

O analisador universal utiliza ainda bibliotecas específicas para os formatos suportados.

A instalação reproduzível exige que todas as dependências necessárias estejam corretamente declaradas no projeto. A configuração atual do `pyproject.toml` ainda não declara todas as bibliotecas utilizadas pelos analisadores.

## 3. Preparar o ambiente

Na raiz do repositório, abrir PowerShell.

Criar o ambiente virtual, caso ainda não exista:

```powershell
python -m venv .venv
```

Ativar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar o projeto e as dependências de desenvolvimento:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev,web]"
```

Nota: esta instalação utiliza as dependências atualmente declaradas no `pyproject.toml`. Como algumas bibliotecas utilizadas pelo analisador universal ainda não estão declaradas, poderá ser necessário completar a configuração de dependências antes de reproduzir todos os testes num ambiente limpo.

## 4. Executar a suite

Com o ambiente virtual ativo:

```powershell
python -m pytest -q
```

Para obter informação mais detalhada:

```powershell
python -m pytest -v
```

Para mostrar os testes ignorados e os respetivos motivos:

```powershell
python -m pytest -ra
```

Para executar apenas os testes PDF:

```powershell
python -m pytest tests/test_pdf_revisions.py -v
```

Para executar apenas os testes universais:

```powershell
python -m pytest tests/test_universal_analyzer.py -v
```

Para executar um teste individual:

```powershell
python -m pytest tests/test_pdf_revisions.py::test_inspect_incremental_revision_chain -v
```

## 5. Configuração pytest

A configuração atualmente declarada em `pyproject.toml` é:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Significado:

- `testpaths = ["tests"]`: diretório padrão de descoberta dos testes.
- `addopts = "-ra"`: apresenta informação adicional sobre testes ignorados e resultados não aprovados.

## 6. Inventário dos testes analisados

Foram inspecionados diretamente dois ficheiros de testes.

| Ficheiro | Testes identificados |
|---|---:|
| `tests/test_pdf_revisions.py` | 6 |
| `tests/test_universal_analyzer.py` | 12 |
| Total inspecionado | 18 |

A suite completa apresentou 26 testes aprovados. Os restantes testes não estão individualizados neste inventário porque os respetivos ficheiros ainda não foram analisados.

## 7. Testes PDF

Ficheiro: `tests/test_pdf_revisions.py`

São utilizados `pytest` e `pypdf` para gerar documentos PDF de teste.

### 7.1. Localização de startxref

Teste:

`test_find_terminal_startxref`

Verifica se o parser encontra o offset terminal `startxref` e se o valor aponta para uma posição dentro do ficheiro.

### 7.2. PDF com uma revisão

Teste:

`test_inspect_single_revision_pdf`

Verifica:

- Contagem de uma revisão.
- Estado `INDETERMINATE`.
- Presença de avisos.
- Ausência de referência `/Prev`.

O estado indeterminado é intencional: uma cadeia estruturalmente interpretável não equivale a uma validação integral do documento.

### 7.3. PDF com revisão incremental

Teste:

`test_inspect_incremental_revision_chain`

Cria um PDF inicial e uma segunda versão incremental.

Verifica:

- Deteção de duas revisões.
- Existência de referência para a revisão anterior.
- Identificação da estrutura XREF tradicional na revisão anterior.

### 7.4. Offset fora dos limites

Teste:

`test_reject_terminal_startxref_outside_file`

Verifica se uma referência `startxref` para além dos limites do ficheiro provoca `PDFRevisionError`.

### 7.5. Ausência de startxref

Teste:

`test_reject_missing_terminal_startxref`

Verifica se o parser rejeita um documento sem sequência terminal válida de `startxref` e `%%EOF`.

### 7.6. Ciclo na cadeia de revisões

Teste:

`test_reject_revision_chain_cycle`

Cria uma estrutura com referência `/Prev` cíclica.

Verifica se o parser identifica o ciclo e lança `PDFRevisionError`.

## 8. Testes do analisador universal

Ficheiro: `tests/test_universal_analyzer.py`

### 8.1. Ficheiro de texto e hashes

Teste:

`test_inspect_text_file`

Verifica:

- Nome do ficheiro.
- Tamanho.
- SHA-256.
- SHA-512.
- Estado `INDETERMINATE`.

Os hashes esperados são calculados independentemente com `hashlib`.

### 8.2. Identificação PDF

Teste:

`test_identify_pdf_signature`

Verifica a identificação de um ficheiro com cabeçalho `%PDF-`.

Confirma também a presença de um aviso que recomenda o analisador PDF dedicado.

Este teste verifica a identificação por assinatura, não a validade integral do PDF.

### 8.3. Metadados PNG

Teste:

`test_inspect_png_metadata`

Cria uma imagem PNG através de Pillow.

Verifica:

- Identificação `PNG`.
- Largura.
- Altura.

### 8.4. Inspeção ZIP

Teste:

`test_inspect_zip_entries`

Cria um arquivo ZIP com uma entrada.

Verifica:

- Identificação `ZIP_BASED`.
- Contagem de entradas.
- Nome da entrada.

### 8.5. Ficheiro inexistente

Teste:

`test_missing_file_raises_error`

Verifica se a inspeção de um caminho inexistente provoca `FileNotFoundError`.

### 8.6. Preservação do original

Teste:

`test_analysis_does_not_modify_original`

Cria um ficheiro de texto, executa a análise e compara os bytes após a inspeção.

O teste verifica que o conteúdo original permanece igual no cenário testado.

Não demonstra, por si só, que todos os caminhos de execução possíveis são incapazes de modificar ficheiros.

## 9. Teste específico de Windows

Teste:

`test_windows_filesystem_metadata`

Este teste é condicionado pelo sistema operativo.

Em sistemas diferentes de Windows, utiliza `pytest.skip`.

Em Windows, verifica:

- Semântica `windows_creation_time`.
- Presença dos campos de criação, modificação e acesso.
- Formato do identificador do ficheiro, quando disponível.
- Formato do identificador do volume, quando disponível.
- Estado `UNAVAILABLE`, caso o identificador não possa ser recolhido.

A execução confirmada da suite no Windows inclui este cenário, salvo indicação contrária no relatório detalhado do pytest.

## 10. Testes OpenDocument

O ficheiro universal contém cinco testes específicos de ODF.

### 10.1. ODT

Teste:

`test_identify_odt_format`

Verifica a identificação de ODT através do MIME interno e da estrutura ZIP esperada.

### 10.2. ODS

Teste:

`test_identify_ods_format`

Verifica a identificação de ODS através do MIME interno.

### 10.3. ODP

Teste:

`test_identify_odp_format`

Verifica a identificação de ODP através do MIME interno.

### 10.4. MIME divergente da extensão

Teste:

`test_odf_wrong_mimetype_is_not_misidentified`

Cria um ficheiro com extensão `.odt`, mas com MIME interno de ODS.

Verifica que:

- O formato identificado é ODS.
- A estrutura é reconhecida como válida.
- É emitido um aviso de incompatibilidade.

Este comportamento privilegia a evidência interna em vez de assumir que a extensão está correta.

### 10.5. ZIP genérico não deve ser identificado como ODF

Teste:

`test_generic_zip_with_content_xml_is_not_odf`

Cria um ZIP com `content.xml` e MIME genérico.

Verifica que o ficheiro é identificado como `ZIP_BASED`, e não como ODF.

## 11. Resultado de execução confirmado

Execução observada em 18/11/2026:

```text
python -m pytest -q

.......................... [100%]
26 passed in 0.89s
```

Interpretação:

- 26 testes passaram.
- Não foram apresentados testes falhados.
- A execução terminou em aproximadamente 0,89 segundos.

Este resultado corresponde à suite existente naquele momento. Uma alteração posterior ao código ou aos testes exige nova execução.

## 12. Verificações adicionais recomendadas

### 12.1. Verificação de whitespace Git

```powershell
git diff --check
git diff --cached --check
```

Estas verificações ajudam a identificar problemas de whitespace em alterações não staged e staged.

### 12.2. Verificação de estilo

A configuração Ruff encontra-se no `pyproject.toml`.

Execução:

```powershell
ruff check .
```

A existência da configuração não significa que a análise Ruff já tenha sido aprovada.

### 12.3. Cobertura

A dependência `pytest-cov` está declarada no grupo de desenvolvimento.

Para executar:

```powershell
python -m pytest --cov=prooftrace --cov-report=term-missing
```

Não existe ainda uma percentagem de cobertura confirmada neste registo.

### 12.4. Testes após alterações

Sempre que sejam alterados analisadores, core, API ou testes:

1. Executar os testes específicos do módulo.
2. Executar a suite completa.
3. Inspecionar falhas e avisos.
4. Rever as alterações no Git.
5. Registar novos cenários e limitações.

## 13. Limitações da validação atual

Os testes atuais não demonstram:

- Compatibilidade com todas as variantes de PDF.
- Validação criptográfica de assinaturas digitais.
- Reconstrução integral de qualquer histórico de revisões PDF.
- Compatibilidade com todos os documentos Office reais.
- Compatibilidade com todas as implementações OpenDocument.
- Validação integral dos conteúdos de todas as entradas ZIP.
- Segurança contra todos os ficheiros maliciosos.
- Ausência universal de efeitos secundários em todos os caminhos de execução.
- Fiabilidade forense dos timestamps em qualquer sistema.
- Funcionamento final do executável Windows empacotado.

Os testes ODF apresentados utilizam arquivos ZIP sintéticos. São necessários testes adicionais com documentos reais produzidos por diferentes aplicações.

## 14. Próximos testes a desenvolver

- Documentos DOCX reais e variantes malformadas.
- Workbooks XLSX reais.
- Apresentações PPTX reais.
- Documentos ODT, ODS e ODP reais.
- PDFs com XREF streams e filtros não suportados.
- PDFs com cadeias de revisões extensas.
- PDFs encriptados.
- Ficheiros com extensões deliberadamente incorretas.
- ZIPs com entradas corrompidas.
- Ficheiros grandes e limites de recursos.
- Uploads simultâneos na API.
- Falhas durante a limpeza de ficheiros temporários.
- Testes de segurança com ficheiros adversariais.
- Testes de empacotamento e execução Windows.

---

**Fim do guia de testes — versão inicial.**
