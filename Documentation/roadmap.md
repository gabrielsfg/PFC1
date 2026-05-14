# Roadmap de Implementação — Agentes 3, 4 e 5

## Visão geral do pipeline

```
Agent 2 output (.json)
    └── Agent 3 (agente-srs)         → SRS IEEE 830 (.md + .pdf)
            └── Agent 4 (agente-casos-de-uso) → Casos de uso + UML (.md + .pdf)
                    └── Agent 5 (agente-diagramas) → Diagrama de domínio + doc final (.md + .pdf)
```

---

## Agent 3 — `agente-srs/`

**Objetivo**: Ler o JSON do Agent 2 e gerar um documento SRS (IEEE 830) em Markdown e PDF.

### Passo 1 — Entender e mapear o JSON de entrada

- Ler o schema real do JSON gerado pelo `agente-identificacao`
- Mapear cada campo para a seção correspondente do SRS:
  - `metadata` → Seção 1.4 Referências
  - `analise_personas.resumo_conversa` + `tipo_interacao` → Seção 2.1 Identificação do Problema
  - `analise_personas.personas[]` → Seção 2.3 Stakeholders
  - `historias_usuario.user_stories[]` → Seção 3 (RF) e Seção 4 (US)
- Criar modelos Pydantic em `src/models.py` representando o JSON de entrada

### Passo 2 — Implementar o cliente OpenAI

- Copiar/adaptar `openai_client.py` do `agente-identificacao`
- Configurar `.env` com `OPENAI_API_KEY`, `OPENAI_MODEL`, `INPUT_DIR`, `OUTPUT_DIR`
- Testar chamada simples à API

### Passo 3 — Implementar as chamadas LLM

Criar `src/srs_generator.py` com os métodos:

- `_generate_introduction(metadata, personas, resumo)` → chama LLM com `PROBLEM_IDENTIFICATION_PROMPT`, retorna seções 1.1–1.4 e 2.1–2.2
- `_extract_functional_requirements(user_stories)` → chama LLM com `FUNCTIONAL_REQUIREMENTS_PROMPT`, retorna lista RF001...n
- `_parse_json_response(response)` → mesmo padrão do Agent 2 (strip markdown fences)

### Passo 4 — Implementar o renderizador de documento

Criar `src/document_renderer.py`:

- `render_markdown(srs_data) -> str` → usa Jinja2 com `templates/srs.md.j2`, retorna string Markdown
- `render_pdf(markdown_str, output_path)` → converte Markdown para PDF via WeasyPrint ou Pandoc subprocess
- Salvar `.md` e `.pdf` em `data/output/` com timestamp no nome

### Passo 5 — Implementar o orquestrador principal

Criar `src/srs_processor.py`:

- `process_file(json_path) -> dict` → método principal que chama os passos 3 e 4 em sequência
- `process_directory(dir_path)` → itera sobre todos `.json` do diretório
- `_save_result(result, source_path)` → salva os arquivos de saída

### Passo 6 — Implementar o monitor de arquivos

Criar `src/file_monitor.py`:

- Copiar padrão do `agente-identificacao/src/file_monitor.py`
- Adaptar para monitorar arquivos `.json` (não `.txt`)
- Ignorar arquivos que já estão em `processed_files.txt`

### Passo 7 — Conectar o `main.py`

- Implementar os três modos: `--file`, `--dir`, `--monitor`
- Substituir o `raise NotImplementedError` pelas chamadas reais

### Passo 8 — Testar com output real do Agent 2

- Rodar o Agent 2 em um arquivo do AMI corpus para gerar um `.json` real
- Processar esse `.json` com o Agent 3
- Validar o documento gerado contra a estrutura IEEE 830
- Verificar se os RF estão corretos e se as US aparecem na tabela

---

## Agent 4 — `agente-casos-de-uso/`

**Objetivo**: Ler o SRS gerado pelo Agent 3 e gerar casos de uso estruturados + diagrama UML via kroki.io.

### Passo 1 — Definir o schema de entrada

- Ler o `.json` de saída do Agent 3 (ou o JSON do Agent 2 diretamente — decidir)
- Criar modelos Pydantic para representar os dados de entrada

### Passo 2 — Implementar o gerador de casos de uso

Criar `src/use_case_generator.py`:

- `_extract_use_cases(personas, user_stories)` → chama LLM para gerar, para cada user story relevante, um caso de uso no template:
  - **Ator principal**
  - **Pré-condição**
  - **Pós-condição**
  - **Fluxo principal** (passos numerados)
  - **Fluxos alternativos**
  - **Fluxos de exceção**

### Passo 3 — Implementar a geração do diagrama UML

Criar `src/diagram_generator.py`:

- `_generate_plantuml_usecase(use_cases) -> str` → chama LLM para gerar código PlantUML do diagrama de casos de uso
- `_render_diagram(plantuml_code) -> bytes` → envia o código para kroki.io e retorna a imagem PNG/SVG
  - Endpoint: `POST https://kroki.io/plantuml/png` com body = código PlantUML (ou base64 na URL)
- Salvar imagem em `data/output/`

### Passo 4 — Criar o template de documento

Criar `templates/use_cases.md.j2`:

- Seção por caso de uso com todos os campos do template
- Diagrama UML embebido como imagem

### Passo 5 — Renderizar Markdown + PDF

- Mesmo padrão do Agent 3: Jinja2 → Markdown → PDF

### Passo 6 — Monitor de arquivos, orquestrador e `main.py`

- Mesmo padrão do Agent 3 (passos 5, 6 e 7)
- Monitorar arquivos `.md` ou `.json` gerados pelo Agent 3

### Passo 7 — Testar end-to-end (Agents 2 → 3 → 4)

- Validar que os casos de uso fazem sentido em relação às personas e user stories
- Verificar que o diagrama PlantUML é válido e renderiza corretamente

---

## Agent 5 — `agente-diagramas/`

**Objetivo**: Gerar o diagrama de domínio e montar o documento final unificado com o output de todos os agentes anteriores.

### Passo 1 — Definir o schema de entrada

- Consolidar outputs dos Agents 2, 3 e 4 como fontes de dados
- Identificar quais entidades do domínio emergem das personas, requisitos e casos de uso

### Passo 2 — Implementar o extrator de entidades de domínio

Criar `src/domain_extractor.py`:

- `_extract_domain_entities(personas, requirements, use_cases)` → chama LLM para identificar:
  - Entidades (classes do domínio)
  - Atributos relevantes de cada entidade
  - Relacionamentos entre entidades (associação, composição, herança)

### Passo 3 — Implementar a geração do diagrama de domínio

Criar `src/diagram_generator.py`:

- `_generate_plantuml_domain(entities) -> str` → chama LLM para gerar código PlantUML de diagrama de classes
- `_render_diagram(plantuml_code) -> bytes` → mesma integração kroki.io do Agent 4
- Salvar imagem em `data/output/`

### Passo 4 — Implementar o montador do documento final

Criar `src/document_assembler.py`:

- `assemble(srs_md, use_cases_md, domain_diagram_path) -> str` → concatena todas as seções em um único Markdown
- Adiciona capa, índice e numeração de páginas
- Gera PDF final unificado

### Passo 5 — Criar o template do documento final

Criar `templates/final_document.md.j2`:

```
Capa (título, data, origem da reunião)
Índice
--- [conteúdo do SRS — Agent 3] ---
--- [casos de uso — Agent 4] ---
--- [diagrama de domínio] ---
```

### Passo 6 — Monitor de arquivos, orquestrador e `main.py`

- Mesmo padrão dos agentes anteriores
- Monitorar output do Agent 4

### Passo 7 — Testar pipeline completo (Agents 1 → 2 → 3 → 4 → 5)

- Rodar o pipeline completo a partir de um áudio ou transcrição do AMI corpus
- Validar coerência do documento final: personas → requisitos → casos de uso → diagrama de domínio
- Verificar qualidade do PDF gerado

---

## Ordem de implementação recomendada

```
1. Agent 3 completo e testado
2. Agent 4 (usa mesmos padrões do 3)
3. Agent 5 (depende dos dois anteriores)
```

Não avançar para o Agent 4 antes de ter o Agent 3 gerando documentos válidos, pois o Agent 4 depende da estrutura de saída do 3.
