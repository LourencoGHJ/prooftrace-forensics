# ProofTrace — Development Log

**Projeto:** ProofTrace  
**Tipo:** Aplicação local de análise forense digital  
**Plataforma-alvo:** Windows  
**Ambiente de desenvolvimento:** Windows 11, PowerShell 7.6.9, Python 3.13.17  
**Data deste registo:** 18/11/2026  
**Branch de trabalho:** `docs/prooftrace-documentation`

---

## 1. Objetivo do projeto

O ProofTrace pretende disponibilizar uma ferramenta local de análise forense digital para examinar ficheiros, recolher metadados, calcular hashes criptográficos e identificar indícios de alterações.

A aplicação está a ser desenvolvida com os seguintes princípios:

- Processamento local, sem dependência de APIs externas.
- Ausência de telemetria ou envio automático de evidências para serviços cloud.
- Preservação da distinção entre factos observados, indícios e conclusões.
- Recolha de hashes para identificação e verificação de integridade.
- Documentação explícita das limitações de cada análise.
- Interface acessível através de um browser, servida localmente.
- Relatórios que não afirmam autenticidade ou ausência de alterações sem evidência suficiente.

O objetivo é construir uma ferramenta tecnicamente transparente, não um sistema que prometa determinar automaticamente se qualquer ficheiro é autêntico.

---

## 2. Ambiente de desenvolvimento

Ambiente conhecido durante esta fase:

| Componente | Versão / configuração |
|---|---|
| Sistema operativo | Windows 11 |
| Shell | PowerShell 7.6.9 |
| Python | 3.13.17 |
| Ambiente virtual | `.venv` |
| FastAPI | 0.163.2 |
| Uvicorn | 0.54.0 |
| pypdf | 7.1.0 |
| PyInstaller | 6.22.3 |
| Testes | pytest |

Dependências e bibliotecas utilizadas nesta fase:

- Pillow
- python-docx
- openpyxl
- python-pptx
- olefile
- mutagen
- hachoir
- ExifRead
- defusedxml
- FastAPI
- Uvicorn
- pypdf
- pytest

Nota: `httpx2` foi instalado no ambiente para permitir os testes com `TestClient`. A sua inclusão definitiva nas dependências do projeto ainda precisa de ser avaliada.

---

## 3. Arquitetura e módulos implementados

### 3.1. Core

Localização: `src/prooftrace/core/`

**hashing.py**
- Cálculo de SHA-256 e SHA-512.
- Processamento em streaming, evitando carregar ficheiros completos na memória.

**verification.py**
- Comparação de digests.
- Identificação de correspondência (`MATCH`) ou divergência (`MISMATCH`).

**acquisition.py**
- Cópia de evidências.
- Cálculo de hashes.
- Verificação da cópia através da comparação dos hashes.

### 3.2. Análise PDF

Localização: `src/prooftrace/analyzers/`

**pdf.py**
- Leitura de metadados PDF.
- Contagem de páginas.
- Extração de texto.
- Identificação de campos de assinatura `/Sig`.
- Inspeção de marcadores `%%EOF` e `startxref`.
- Cálculo de hashes.
- Comparação entre documentos PDF.
- Estado de validação criptográfica de assinaturas: `NOT_PERFORMED`.

A presença de um campo de assinatura não demonstra, por si só, que a assinatura é válida.

**pdf_revisions.py**
- Análise de revisões incrementais de PDF.
- Inspeção de estruturas XREF.
- Suporte à leitura de XREF em formato de tabela e streams com `FlateDecode`.

Limitação: a análise de revisões não constitui uma reconstrução universal de todas as operações históricas realizadas sobre um PDF. A robustez do parser e a cobertura de estruturas PDF complexas continuam a exigir validação adicional.

### 3.3. Analisador universal

Ficheiro: `src/prooftrace/analyzers/universal.py`

Funcionalidades implementadas:

**Hashes**
- SHA-256.
- SHA-512.
- Leitura em streaming.

**Metadados do sistema de ficheiros**
- Tamanho.
- Datas disponibilizadas pelo sistema de ficheiros.
- Identificação do volume e do ficheiro em Windows, através de chamadas nativas.

No Windows:
- Utilização de `CreateFileW`.
- Utilização de `GetFileInformationByHandle`.
- Utilização de `CloseHandle`.
- Recolha de volume serial e file ID.

Foi corrigida a configuração dos tipos de argumentos e retornos (`argtypes` e `restype`) das funções nativas, bem como o tratamento de handles inválidos e o fecho dos handles.

A semântica dos timestamps depende do sistema operativo. No Windows, o valor de criação é tratado como `windows_creation_time`. Em POSIX, `st_ctime` representa alteração de metadados, não necessariamente criação.

**Identificação de formatos**
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

A identificação por assinatura binária é separada da extensão do ficheiro e da inferência MIME.

Quando não existe uma assinatura reconhecida, o formato é identificado como `UNKNOWN`, em vez de ser presumido apenas pela extensão.

**Validação de contentores ZIP e formatos Office**
- Verificação da estrutura ZIP.
- Identificação de contentores inválidos.
- Deteção de componentes internos de DOCX, XLSX e PPTX.
- Recolha de nomes, tamanhos, timestamps e CRC declarados nas entradas ZIP.
- Limitação da listagem a 5.000 entradas.

A recolha de CRC declarados não equivale à validação integral do conteúdo de cada entrada.

**Formatos OpenDocument**
- ODT.
- ODS.
- ODP.

A identificação utiliza o MIME interno e exige componentes estruturais:
- `mimetype`
- `content.xml`
- `META-INF/manifest.xml`

Foram adicionados testes para impedir a identificação incorreta de ZIP genérico como ODF.

**Metadados Office**
- DOCX: propriedades do documento.
- XLSX: propriedades do workbook.
- PPTX: propriedades da apresentação.

Campos normalizados incluem:
- Título.
- Assunto.
- Autor.
- Palavras-chave.
- Comentários.
- Último responsável pela modificação.
- Categoria.
- Identificador.
- Idioma.
- Datas de criação e modificação.
- Revisão e versão, quando disponíveis.

**Imagens**
- Formato identificado pela biblioteca de imagem.
- Dimensões.
- Modo de cor.
- Informação EXIF básica.
- Chaves de informação incorporada.

**Avaliação**
O resultado inclui um estado inicial `INDETERMINATE` quando a análise não permite uma conclusão sustentada.

São incluídos avisos sobre o âmbito dos timestamps e sobre as limitações de uma inspeção isolada.

---

## 4. Interface e API local

Localização: `src/prooftrace/web/`

Componentes:
- `app.py`
- `__init__.py`
- `static/app.js`
- `static/index.html`
- `static/style.css`
- `static/prooftrace-icon.png`

A aplicação utiliza FastAPI e disponibiliza:

| Endpoint | Finalidade |
|---|---|
| `/` | Interface web |
| `/api/health` | Verificação de estado |
| `/api/dashboard` | Dados do dashboard |
| `/api/evidence/inspect` | Análise universal de ficheiros |
| `/api/pdf/inspect` | Análise específica de PDF |
| `/api/pdf/compare` | Comparação de PDF |
| `/docs` | Documentação OpenAPI |
| `/openapi.json` | Esquema OpenAPI |
| `/static` | Ficheiros estáticos |

O servidor foi configurado para trabalhar localmente em `127.0.0.1`.

### Gestão de uploads

- Limite de upload: 50 MB.
- Processamento através de ficheiros temporários.
- Utilização de `TemporaryDirectory`.
- Remoção dos ficheiros temporários após o processamento.
- Registo de atividade mantido em memória.
- O caminho temporário do servidor não é exposto como caminho da evidência original na resposta universal.

O timestamp do ficheiro recebido pelo servidor refere-se à cópia temporária, não ao ficheiro original do utilizador.

---

## 5. Problemas encontrados e correções

### 5.1. Chamadas nativas Windows

**Problema:** configuração incompleta dos tipos de argumentos e retornos nas chamadas nativas.

**Causa:** utilização inadequada de `ctypes` para funções Windows.

**Correção:**
- Definição explícita de `argtypes`.
- Definição explícita de `restype`.
- Verificação de handles inválidos.
- Fecho de handles no bloco `finally`.

**Resultado observado:** recolha real de identificadores de volume e ficheiro num ambiente Windows.

### 5.2. Assinaturas binárias

**Problema:** identificação incorreta de algumas assinaturas de ficheiros.

**Causa:** escapes incorretos na representação de bytes.

**Correção:** revisão dos valores binários utilizados na identificação dos formatos.

**Resultado observado:** teste de identificação PNG passou com `SIGNATURE_MATCH`.

### 5.3. Validação de contentores Office

**Problema:** contentores ZIP genéricos podiam ser tratados de forma demasiado permissiva.

**Causa:** validação insuficiente dos componentes internos esperados para cada formato.

**Correção:** validação dos ficheiros estruturais necessários para DOCX, XLSX e PPTX.

### 5.4. Avisos de incompatibilidade entre extensão e conteúdo

**Problema:** determinados formatos baseados em ZIP podiam ocultar avisos de divergência entre extensão declarada e formato detetado.

**Causa:** exceção na lógica de comparação entre os dois valores.

**Correção:** revisão da condição para emitir aviso quando existe uma extensão declarada e esta não corresponde ao formato identificado.

### 5.5. Identificação OpenDocument

**Problema:** a identificação baseada apenas em elementos genéricos de ZIP podia produzir falsos positivos.

**Correção:**
- Verificação de `mimetype`.
- Verificação de `content.xml`.
- Verificação de `META-INF/manifest.xml`.
- Leitura do MIME interno.
- Testes específicos para ODT, ODS e ODP.

### 5.6. Teste ODF com expectativa incorreta

**Problema:** um teste esperava `ZIP_BASED` quando o MIME interno identificava ODS.

**Análise:** a identificação do conteúdo interno como ODS era coerente com a evidência disponível. A extensão incorreta deveria produzir um aviso, não apagar a identificação interna.

**Correção:** atualização da expectativa do teste para preservar o formato identificado e verificar o aviso de incompatibilidade.

Este caso foi tratado como correção da expectativa do teste, não como alteração artificial do comportamento do analisador.

### 5.7. Uploads e ficheiros temporários

**Validações observadas:**
- Upload vazio: HTTP 400.
- Upload acima de 50 MB: HTTP 413.
- Erro de processamento: HTTP 422.
- Inspeções de vários formatos: HTTP 200.
- Limpeza de diretórios temporários após processamento.

### 5.8. Limpeza de whitespace

Foram removidos espaços em branco finais e linhas vazias excedentes em ficheiros incluídos no commit.

A validação `git diff --cached --check` passou depois dessa limpeza.

O Git apresentou avisos de normalização LF/CRLF no Windows. Estes avisos não impediram o commit.

---

## 6. Testes automatizados

Suite principal:

```powershell
python -m pytest -q
```

Resultado mais recente confirmado em 18/11/2026:

```text
26 passed in 0.89s
```

Os testes abrangem:
- Análise universal.
- Identificação de formatos.
- Metadados.
- Comportamento específico de Windows.
- Validação OpenDocument.
- Revisões PDF.

A suite foi executada após o primeiro commit e passou integralmente.

Nota: os testes aprovados não demonstram cobertura exaustiva de todos os formatos, variantes ou cenários de manipulação.

---

## 7. Git e controlo de versões

Branch de origem conhecida:
`feat/pdf-revision-chain`

Branch atual:
`docs/prooftrace-documentation`

Primeiro commit desta branch:

```text
28fa510 feat: expand universal forensic analysis and format validation
```

Conteúdo do commit:
- 11 ficheiros.
- 2.756 linhas adicionadas.

Foram mantidos fora do commit ficheiros de backup locais, identificados por nomes como `.backup-*` e `.before-*`.

Estes ficheiros não foram apagados nem incluídos no primeiro commit.

Estado observado após o commit:
- Nenhuma alteração pendente em ficheiros versionados.
- Nove ficheiros de backup ainda não versionados.

---

## 8. Limitações conhecidas

1. A presença de metadados não prova a identidade do autor.
2. Datas de criação e modificação não demonstram, isoladamente, quando o conteúdo foi originalmente produzido.
3. Uma inspeção isolada não reconstrói necessariamente todo o histórico de alterações.
4. Campos de assinatura PDF não equivalem a validação criptográfica da assinatura.
5. A validação de CRC de todas as entradas ZIP ainda não está demonstrada.
6. A identificação por assinatura suporta um conjunto definido de formatos; não é universal.
7. Os metadados extraídos dependem do formato e da biblioteca utilizada.
8. A análise de revisões PDF necessita de testes adicionais com documentos complexos.
9. A validação ODF foi testada com estruturas sintéticas; a validação com ficheiros reais produzidos por diferentes suites Office ainda precisa de ser ampliada.
10. O limite atual de upload é 50 MB.
11. O sistema não deve emitir conclusões de autenticidade ou integridade histórica sem evidência suficiente.

---

## 9. Trabalho futuro

- Completar a documentação técnica da arquitetura.
- Criar um guia de testes reproduzíveis.
- Documentar a matriz de formatos e limitações.
- Rever as dependências declaradas em `pyproject.toml`.
- Ampliar os testes com documentos reais de diferentes aplicações.
- Melhorar a análise de metadados multimédia.
- Aprofundar a validação de estruturas PDF.
- Avaliar a validação criptográfica de assinaturas PDF.
- Rever a segurança do processamento de ficheiros não confiáveis.
- Validar o empacotamento Windows com PyInstaller.
- Testar a abertura da aplicação por duplo clique.
- Avaliar a experiência de utilização e a apresentação dos relatórios.

---

## 10. Princípio de integridade técnica

O ProofTrace deve comunicar claramente a diferença entre:

- **Facto observado:** informação efetivamente recolhida.
- **Indício:** elemento que pode sugerir determinada situação, mas não a prova.
- **Ausência de informação:** dado que não foi encontrado ou não estava disponível.
- **Limitação:** condição que impede uma conclusão mais forte.
- **Conclusão:** interpretação sustentada pelos resultados e pelo âmbito real da análise.

A ferramenta deve privilegiar conclusões conservadoras e reproduzíveis.

A ausência de um indício não prova a ausência de alteração. Um hash corresponde a uma identificação do conteúdo observado num determinado momento, não a uma certificação automática da sua origem.

---

**Fim do registo de desenvolvimento — versão inicial.**
