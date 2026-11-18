# ProofTrace — Technical Documentation

**Versão do projeto:** 0.2.0  
**Documento:** Documentação Técnica  
**Plataforma-alvo:** Windows  
**Python mínimo declarado:** 3.12  
**Data:** 18/11/2026  
**Branch:** `docs/prooftrace-documentation`

---

## 1. Introdução

O ProofTrace é uma ferramenta de análise forense digital orientada para inspeção local de ficheiros, recolha de metadados, identificação de formatos e verificação de integridade através de hashes criptográficos.

A arquitetura atual combina:

- Um núcleo de hashing e verificação.
- Um módulo inicial de aquisição de evidências.
- Analisadores específicos para PDF.
- Um analisador universal de ficheiros.
- Uma API local baseada em FastAPI.
- Uma interface web servida localmente.

O sistema procura apresentar resultados observáveis e limitações de forma explícita.

A análise não deve ser interpretada como certificação automática de autenticidade, autoria ou histórico integral de alterações.

## 2. Arquitetura geral

A aplicação está organizada por responsabilidades.

```text
prooftrace/
|
+-- core/
|   +-- hashing.py
|   +-- verification.py
|   +-- acquisition.py
|
+-- analyzers/
|   +-- pdf.py
|   +-- pdf_revisions.py
|   +-- universal.py
|
+-- evidence/
|
+-- reporting/
|
+-- web/
|   +-- app.py
|   +-- static/
|       +-- index.html
|       +-- app.js
|       +-- style.css
|       +-- prooftrace-icon.png
|
+-- cli.py
```

### 2.1. Responsabilidades

| Módulo | Responsabilidade |
|---|---|
| `core/hashing.py` | Cálculo de hashes criptográficos |
| `core/verification.py` | Comparação de hashes com referências |
| `core/acquisition.py` | Cópia e verificação inicial de evidências |
| `analyzers/pdf.py` | Inspeção de estrutura, texto e metadados PDF |
| `analyzers/pdf_revisions.py` | Inspeção estrutural de cadeias de revisões PDF |
| `analyzers/universal.py` | Identificação e inspeção de vários formatos |
| `web/app.py` | API HTTP local e integração da interface |

Os diretórios `evidence` e `reporting` existem na estrutura atual, mas ainda não apresentam implementação funcional documentada nesta fase.

## 3. Core — integridade e aquisição

### 3.1. Hashing

Ficheiro: `src/prooftrace/core/hashing.py`

O módulo disponibiliza a função:

```python
hash_file(
    path,
    algorithms=("sha256", "sha512"),
    chunk_size=1024 * 1024
)
```

Características:

- Utiliza `hashlib`.
- Suporta SHA-256 e SHA-512.
- Processa ficheiros em blocos de 1 MiB por defeito.
- Permite selecionar algoritmos.
- Evita carregar o ficheiro completo na memória.
- Rejeita algoritmos não suportados.
- Rejeita tamanhos de bloco iguais ou inferiores a zero.

O resultado é um dicionário com os nomes dos algoritmos e os respetivos digests hexadecimais.

**Interpretação:** o hash identifica uma sequência exata de bytes. Não demonstra quem criou o ficheiro, quando foi criado ou se existiram alterações anteriores.

### 3.2. Verificação

Ficheiro: `src/prooftrace/core/verification.py`

Função principal:

```python
verify_file(path, expected)
```

Procedimento:

1. Recebe o caminho do ficheiro.
2. Recebe um ou mais hashes esperados.
3. Recalcula os hashes através de `hash_file`.
4. Compara os valores.
5. Devolve o estado global e o resultado de cada algoritmo.

Estados:

- `match`: todos os hashes correspondem.
- `mismatch`: pelo menos um hash diverge.

A verificação depende da qualidade e proveniência da referência fornecida. Um hash esperado sem origem confiável não estabelece, por si só, autenticidade.

### 3.3. Aquisição

Ficheiro: `src/prooftrace/core/acquisition.py`

A função `acquire_file` implementa um fluxo inicial de aquisição.

Recebe:

- Ficheiro de origem.
- Diretório de destino.
- Identificação do responsável pela recolha.
- Descrição da origem.

Procedimento:

1. Verifica se a origem é um ficheiro regular.
2. Valida os campos obrigatórios.
3. Cria o diretório de destino.
4. Gera um identificador de evidência.
5. Copia o ficheiro.
6. Calcula SHA-256 e SHA-512 da origem.
7. Calcula os mesmos hashes da cópia.
8. Compara os resultados.
9. Remove a cópia se existir divergência.
10. Devolve um `AcquisitionRecord` se a verificação passar.

O registo inclui:

- Identificador da evidência.
- Nome original.
- Tamanho.
- Data UTC da aquisição.
- Responsável.
- Descrição da origem.
- Digests.
- Caminho da cópia preservada.
- Resultado da verificação.
- Nome e versão declarados da ferramenta.
- Versão do esquema do registo.

**Limitação:** a cópia verificada não é armazenamento imutável. O módulo não implementa bloqueio contra escrita, cadeia de custódia completa, assinatura do registo ou armazenamento inviolável.

## 4. Análise PDF

### 4.1. Inspeção principal

Ficheiro: `src/prooftrace/analyzers/pdf.py`

Função principal:

```python
inspect_pdf(path)
```

A análise utiliza `pypdf`.

Verificações e recolha:

- Existência do ficheiro.
- Cabeçalho `%PDF-`.
- Deteção de encriptação.
- Versão declarada no cabeçalho.
- Número de páginas.
- Metadados disponíveis.
- Extração de texto por página.
- Campos de formulário de assinatura `/Sig`.
- Hash SHA-256.
- Marcadores `%%EOF`.
- Referências `startxref`.

A extração de texto é executada por página. Quando ocorre uma exceção durante a extração, o erro é registado para essa página.

PDFs encriptados não são atualmente suportados por este analisador.

### 4.2. Marcadores de revisão

A função interna `_revision_markers` recolhe posições lexicais dos marcadores `%%EOF` e valores encontrados em `startxref`.

Estes elementos são indicadores estruturais.

A existência de vários marcadores não demonstra automaticamente que existam revisões incrementais válidas.

### 4.3. Assinaturas digitais

O analisador identifica campos cujo tipo `/FT` corresponde a `/Sig`.

O estado devolvido é:

```text
NOT_PERFORMED
```

Isto significa que a validação criptográfica da assinatura não foi realizada.

A presença de um campo de assinatura não demonstra:

- Que a assinatura é criptograficamente válida.
- Que o certificado é confiável.
- Que a cadeia de certificados é válida.
- Que o documento não foi alterado depois da assinatura.

### 4.4. Comparação de PDFs

Função:

```python
compare_pdf_versions(first, second)
```

Compara:

- Hash SHA-256.
- Tamanho.
- Número de páginas.
- Texto extraído por página.
- Metadados disponíveis.

O resultado distingue diferenças de bytes, diferenças de texto e alterações nos metadados.

Uma divergência de hash demonstra que os bytes são diferentes. Não demonstra que a alteração foi maliciosa ou intencional.

A comparação textual também não identifica necessariamente alterações visuais, objetos ocultos, anotações ou diferenças estruturais.

## 5. Análise de revisões PDF

Ficheiro: `src/prooftrace/analyzers/pdf_revisions.py`

O módulo disponibiliza inspeção estrutural de cadeias de referências XREF.

### 5.1. Estruturas suportadas

- Tabelas XREF tradicionais.
- XREF streams.
- Streams com `FlateDecode`.
- Referências `/Prev` entre revisões.

Funções principais:

- `find_startxref`
- `parse_xref`
- `inspect_revision_chain`

Exceção específica:

```python
PDFRevisionError
```

### 5.2. Limites de segurança

O parser aplica limites explícitos:

- Máximo de 100 revisões na cadeia.
- Máximo de 1.000.000 entradas numa subseção XREF tradicional.
- Máximo de 16 MiB após descompressão de um XREF stream.

Quando uma estrutura não pode ser interpretada, pode ser devolvido o estado `INDETERMINATE` ou lançada uma exceção específica.

Filtros de stream não suportados não são tratados como se tivessem sido validados.

### 5.3. Limitações

O parser não valida integralmente:

- Todos os objetos referenciados.
- A consistência semântica completa do documento.
- A validade criptográfica de assinaturas.
- A autenticidade do histórico de revisões.

A inspeção estrutural de uma cadeia XREF não constitui prova de que todas as revisões são legítimas.

## 6. Analisador universal

Ficheiro: `src/prooftrace/analyzers/universal.py`

O analisador universal concentra a identificação de formatos, recolha de metadados e avaliação inicial de ficheiros.

### 6.1. Hashes

Calcula SHA-256 e SHA-512 através de leitura em streaming.

### 6.2. Metadados do sistema de ficheiros

Recolhe informação disponibilizada pelo sistema operativo.

No Windows, utiliza chamadas nativas através de `ctypes` para obter:

- Identificador do volume.
- Identificador do ficheiro.
- Informação temporal disponibilizada pelo sistema.

A implementação utiliza:

- `CreateFileW`
- `GetFileInformationByHandle`
- `CloseHandle`

Os handles são tratados e fechados no fluxo de execução.

A interpretação dos timestamps é dependente do sistema operativo. Os metadados do sistema de ficheiros não constituem, isoladamente, prova histórica da criação ou modificação do conteúdo.

### 6.3. Identificação de formatos

A identificação por assinatura binária abrange atualmente:

- PDF.
- PNG.
- JPEG.
- GIF.
- TIFF.
- BMP.
- ELF.
- Executáveis Windows com assinatura MZ.
- MP3.
- FLAC.
- OGG.
- RIFF.

O analisador separa:

1. Formato identificado pelo conteúdo.
2. Extensão declarada.
3. Tipo MIME inferido.

Quando o formato não é reconhecido, utiliza `UNKNOWN`.

Uma divergência entre extensão e conteúdo pode originar um aviso. A extensão não deve prevalecer sobre a assinatura identificada.

### 6.4. Contentores ZIP

O módulo verifica se o ficheiro pode ser interpretado como contentor ZIP.

Estados e classificações incluem:

- `ZIP_INVALID`
- `ZIP_BASED`
- `VALID_ZIP_CONTAINER`
- `INVALID_ZIP_CONTAINER`

Para arquivos válidos, recolhe informação das entradas sem necessidade de extrair todos os ficheiros.

A listagem está limitada a 5.000 entradas.

Os metadados recolhidos incluem:

- Nome da entrada.
- Tamanho.
- Tamanho comprimido.
- Timestamp declarado.
- CRC declarado.

A recolha destes valores não equivale à validação integral dos dados de todas as entradas.

### 6.5. Formatos Office

A validação estrutural procura componentes característicos:

**DOCX**
- `[Content_Types].xml`
- `_rels/.rels`
- `word/document.xml`

**XLSX**
- `[Content_Types].xml`
- `_rels/.rels`
- `xl/workbook.xml`

**PPTX**
- `[Content_Types].xml`
- `_rels/.rels`
- `ppt/presentation.xml`

A presença destes componentes permite uma classificação estrutural, mas não certifica que todo o conteúdo seja semanticamente válido ou seguro.

### 6.6. OpenDocument

São reconhecidos:

- ODT.
- ODS.
- ODP.

A identificação verifica os componentes estruturais e o MIME interno:

- `mimetype`
- `content.xml`
- `META-INF/manifest.xml`

A identificação considera o MIME interno, podendo detetar uma divergência com a extensão do ficheiro.

### 6.7. Metadados Office

As propriedades principais são recolhidas através das bibliotecas específicas de cada formato:

- DOCX: `python-docx`.
- XLSX: `openpyxl`.
- PPTX: `python-pptx`.

Campos normalizados podem incluir:

- `title`
- `subject`
- `author`
- `keywords`
- `comments`
- `last_modified_by`
- `category`
- `identifier`
- `language`
- `created`
- `modified`
- `revision`
- `version`

A disponibilidade depende do formato e do conteúdo do documento.

### 6.8. Imagens

A inspeção utiliza Pillow e pode recolher:

- Formato.
- Dimensões.
- Modo de cor.
- Informação EXIF básica.
- Chaves de informação incorporada.

Nem todos os formatos ou ficheiros contêm EXIF ou metadados adicionais.

### 6.9. Avaliação

A avaliação inicial pode assumir o estado:

```text
INDETERMINATE
```

O analisador não deve transformar ausência de metadados em prova de ausência de alterações.

Os resultados devem ser interpretados em conjunto com os avisos e limitações associados.

## 7. API e interface web

Localização: `src/prooftrace/web/`

Tecnologia principal:

- FastAPI.
- Uvicorn.
- HTML.
- CSS.
- JavaScript.

A API disponibiliza os seguintes endpoints:

| Endpoint | Função |
|---|---|
| `/` | Interface principal |
| `/api/health` | Estado do serviço |
| `/api/dashboard` | Dados do dashboard |
| `/api/evidence/inspect` | Inspeção universal |
| `/api/pdf/inspect` | Inspeção PDF |
| `/api/pdf/compare` | Comparação de PDFs |
| `/docs` | Documentação OpenAPI |
| `/openapi.json` | Esquema OpenAPI |
| `/static` | Recursos estáticos |

### 7.1. Uploads

O fluxo de upload utiliza ficheiros temporários e estabelece um limite de 50 MB.

Respostas de erro observadas:

- HTTP 400: upload vazio.
- HTTP 413: ficheiro acima do limite.
- HTTP 422: falha de processamento.

A implementação utiliza diretórios temporários com limpeza após o processamento.

O timestamp de uma cópia temporária recebida pela API não deve ser apresentado como timestamp original da evidência.

### 7.2. Execução local

A configuração conhecida utiliza:

```text
127.0.0.1
```

O serviço destina-se a utilização local.

A exposição a outras interfaces de rede, execução remota e utilização multiutilizador não fazem parte das capacidades que devem ser presumidas nesta fase.

## 8. Configuração e dependências

Ficheiro: `pyproject.toml`

Metadados atualmente declarados:

- Nome: `prooftrace-forensics`
- Versão: `0.2.0`
- Python mínimo: `>=3.12`
- Sistema de build: setuptools.

Dependência principal declarada:

```toml
dependencies = ["pypdf>=5.0"]
```

Dependências opcionais:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0", "ruff>=0.6"]
web = ["fastapi>=0.115", "uvicorn>=0.30", "python-multipart>=0.0.20"]
```

**Nota importante sobre dependências:**

O ambiente de desenvolvimento contém outras bibliotecas utilizadas pelos analisadores, incluindo Pillow, `python-docx`, `openpyxl`, `python-pptx`, `olefile`, `mutagen`, `hachoir`, `ExifRead` e `defusedxml`.

Estas bibliotecas ainda não aparecem na lista de dependências apresentada no `pyproject.toml` analisado.

A instalação reproduzível do projeto noutro computador exige uma revisão desta configuração.

## 9. Segurança e privacidade

Princípios de arquitetura:

- Processamento local.
- Ausência de dependência funcional de serviços cloud na arquitetura atual.
- Utilização de diretórios temporários para uploads.
- Limite de tamanho para uploads.
- Leitura de evidências sem edição intencional do conteúdo original.
- Limites de processamento em estruturas PDF e ZIP.
- Utilização de `defusedxml` como dependência instalada no ambiente.

A presença de uma biblioteca no ambiente não prova que todos os caminhos de processamento utilizem as suas proteções.

### 9.1. Considerações de segurança

Ficheiros não confiáveis podem conter estruturas malformadas, conteúdo inesperado ou dados concebidos para explorar parsers.

Antes de utilização forense em contexto operacional, devem ser aprofundados:

- Isolamento de processos.
- Limites de memória e CPU.
- Proteção contra ZIP bombs.
- Validação de XML.
- Tratamento de caminhos e nomes maliciosos em arquivos.
- Gestão de erros e exceções.
- Testes com ficheiros adversariais.
- Controlo de acesso à interface local.

A execução em `127.0.0.1` reduz a exposição de rede, mas não substitui uma análise de segurança completa.

## 10. Modelo de interpretação dos resultados

O ProofTrace deve distinguir:

**Facto observado**

Valor diretamente recolhido, como um hash, dimensão ou campo de metadados.

**Indício**

Elemento que pode sugerir uma situação, mas não a prova isoladamente.

**Ausência de informação**

Campo ou artefacto que não foi encontrado ou não estava disponível.

**Limitação**

Condição técnica que impede uma conclusão mais forte.

**Conclusão**

Interpretação sustentada pelos dados efetivamente recolhidos e pelo âmbito da análise.

Uma divergência de hash demonstra diferença de bytes entre duas referências. Não identifica automaticamente a causa ou intenção da alteração.

## 11. Funcionalidades ainda não documentadas como concluídas

Os seguintes elementos exigem implementação, validação ou documentação adicional antes de serem considerados capacidades concluídas:

- Persistência estruturada de evidências.
- Cadeia de custódia completa.
- Relatórios forenses exportáveis.
- Assinatura digital dos relatórios.
- Validação criptográfica de assinaturas PDF.
- Proteção de armazenamento contra escrita.
- Empacotamento final com PyInstaller.
- Instalação e execução final por duplo clique.
- Cobertura de formatos multimédia mais ampla.
- Testes extensivos com ficheiros reais de diferentes aplicações.
- Auditoria de segurança e testes adversariais.

A existência dos diretórios `evidence` e `reporting` não significa que estas funcionalidades estejam implementadas.

## 12. Referências internas

Código-fonte principal:

- `src/prooftrace/core/hashing.py`
- `src/prooftrace/core/verification.py`
- `src/prooftrace/core/acquisition.py`
- `src/prooftrace/analyzers/pdf.py`
- `src/prooftrace/analyzers/pdf_revisions.py`
- `src/prooftrace/analyzers/universal.py`
- `src/prooftrace/web/app.py`

Configuração:

- `pyproject.toml`

Registo de desenvolvimento:

- `DEVELOPMENT_LOG.md`

---

**Fim da documentação técnica — versão inicial.**
