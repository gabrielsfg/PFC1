# Roadmap PFC2 — Artigo de Conferência (SBES 2026)

> Documento de planejamento. Cruza o que o PFC1 já afirmou, o estado real do código hoje
> e os requisitos do template SBES/CBSoft 2026. Use como checklist do que **escrever** e do
> que **calcular/testar** antes de escrever.

---

## 0. Onde você está hoje (estado real, verificado no código)

| Item | PFC1 (artigo) | Código hoje | Implicação p/ PFC2 |
|---|---|---|---|
| Nº de agentes | 3 (transcrição, identificação, formatação) | **4 implementados**: transcrição, identificação, srs (Agente 3), diagramas (Agente 4/5). `agente-casos-de-uso` **não existe** (foi absorvido pelo srs) | Reescrever a seção de arquitetura — o sistema cresceu |
| Modelos LLM | GPT-4o-mini (Agente 2) | **Tudo Claude**: identificação=`claude-haiku-4-5`, srs=`claude-sonnet-4-6`, diagramas=`claude-sonnet-4-6`. Transcrição=Groq `whisper-large-v3-turbo` (fallback faster-whisper `small`) | A seção de método precisa refletir a realidade multi-provedor (Groq + Anthropic) |
| Agente 3 (formatação) | **Não implementado** | Implementado, com **2 formatos**: IEEE 830 (SRS) e "empresa" (SGG-GO) | É a maior entrega nova do PFC2 |
| Código de avaliação | Nenhum (tudo manual) | **Nenhum** — zero scripts de WER/CER/P/R/F1 | **Precisa ser construído do zero** |
| Caso real | Não existe | **Existe**: reunião real SGG-GO (vídeo 609 MB → transcrição → docs gerados) + **documento oficial humano como gold standard** | Validação no mundo real = trunfo do artigo |
| Avaliação humana | Single-author (só você) | Formulário Google Forms **já enviado** aos avaliadores do estado | Survey é a evidência quantitativa central do Agente 3 |
| Figuras | Nenhuma no artigo | — | Criar diagrama de arquitetura + fluxo de dados |

**Ativos prontos para virar evidência:**
- `agente-identificacao/data/output/meeting_{0,2,30,58,113,117,127}_personas_*.json` — as 7 reuniões do PFC1.
- Documento oficial gold: `Documentation/20260507-PR102-ECONOMIA-EVOLUÇÃO IPOF-LOA-EMPENHO...2.pdf`.
- Docs gerados (empresa): `agente-srs/data/output/PR0102...requisitos_*.{md,pdf}`.
- Comparações manuais já escritas: `analise-tcc/comparacao_PR0102.md` e `..._v2_pos_melhorias.md`.
- Erro de transcrição documentado ("HIPOF" vs "IPOF") — anedota de propagação de erro.

---

## 0.5. ENQUADRAMENTO — o veículo é o SE4AS (muda o eixo do artigo)

**Veículo:** I Workshop on Software Engineering for Agentic Systems (SE4AS), 1ª edição, **CBSoft 2026** (SBC, IME-USP, São Paulo). Organização: grupo agents4good. Template: o **ACM-like do CBSoft** que já está nesta pasta (`samples/cbsoft-acm-like.tex`).

**Consequência:** o caráter **multi-agente / agêntico** do sistema deixa de ser "meio" e passa a ser a **contribuição central**. O paper não é mais "automatizamos elicitação de requisitos" — é "**apresentamos e avaliamos empiricamente um sistema agêntico (multi-agente) aplicado à engenharia de requisitos, e relatamos lições de engenharia sobre construir tais sistemas**". O seu projeto encaixa duplamente: é um *agentic system* **e** resolve uma tarefa de SE.

**O que esse tipo de workshop valoriza** (inferido dos irmãos AGENT@ICSE, AgenticDev@ASE, AgenticSE@CAIS — que listam explicitamente requisitos, coordenação/orquestração multi-agente, confiabilidade e estudos de aplicação real):
- Arquitetura de agentes e **especialização** (por que 4 agentes e não 1 prompt monolítico).
- **Orquestração / comunicação inter-agente** (seu watchdog file-based + contrato JSON entre agentes).
- **Seleção de modelo por agente** (`haiku` na identificação vs `sonnet` no srs/diagramas) — decisão clássica de *engenharia* de sistema agêntico (custo × qualidade).
- **Propagação de erro entre agentes** — em pipeline agêntico, erro de um estágio cascateia. Isto deixa de ser anedota e vira **resultado de primeira classe** (RQ própria).
- **Confiabilidade/custo/latência por agente** — preocupações de engenharia, não só de acurácia.
- **Estudo de aplicação no mundo real** (SGG-GO) — exatamente o que esses workshops pedem.

**Ajustes diretos no paper por causa disso:**
- Título e abstract com "multi-agent / agentic system" em destaque.
- Seção de Método reorganizada em torno do *design agêntico* (§3), não da tarefa.
- Adicionar **RQ5 de propagação de erro + custo/latência por agente** (ver §2).
- ⚠️ **Confirmar na chamada oficial** (página do workshop) o **limite de páginas** e tipos de submissão — workshops do CBSoft costumam ser mais curtos que o SBES full (tipicamente ~6–10 pg full / ~4 pg short). 1ª edição tende a acolher *experience/application papers*, mas ainda quer sinal empírico.

---

## 1. Decisões (RESOLVIDAS)

1. **Corpus WER/CER do Agente 1:** ✅ **Common Voice PT + AMI release com áudio** (os dois). CV-PT cobre o idioma real; AMI-áudio cobre o domínio de reunião. Reportar WER/CER separados por corpus (e a diferença PT × reunião é discussão rica).
2. **Veículo:** ✅ **SE4AS @ CBSoft 2026** (workshop). Não é Research/Tools Track do SBES — ver enquadramento §0.5.
3. **Idioma:** ✅ **Inglês** (como o PFC1; reaproveita texto). Cabeçalho em EN de qualquer forma.
4. **Pontuação INVEST:** ✅ **LLM-judge (Claude) no conjunto grande + validação manual de uma amostra com Cohen's kappa**. Defensável e escalável.

---

## 2. Estrutura do artigo (seção por seção) — o que escrever

Ordem esperada num paper empírico do SBES (ACM-like). Headings em Title Case, citações ACM numéricas, figuras com `\Description`.

### Abstract + Keywords
- Reescrever com os **novos números quantitativos** do PFC2 (WER, F1, alfa de Cronbach, etc.).
- 5–8 keywords. (Se Tools Track: link de vídeo demo no fim.)

### 1. Introdução
- Problema: elicitação de requisitos é cara, manual, sujeita a perda de informação.
- **Gap principal:** pouquíssimos pipelines end-to-end áudio→requisitos; datasets escassos; falta de validação real com times.
- **Research Questions explícitas** (PFC1 só tinha "objetivos"; formalize e foregrounde o ângulo agêntico):
  - **RQ1 (acurácia por agente — transcrição):** Qual a acurácia da transcrição automática (WER/CER) em português e em domínio de reunião?
  - **RQ2 (acurácia por agente — identificação):** Com que precisão o agente identifica personas/atores e gera histórias de usuário (Precision/Recall/F1, conformidade INVEST)?
  - **RQ3 (qualidade do artefato final):** Qual a qualidade percebida do documento de requisitos gerado, avaliada por profissionais reais (survey)?
  - **RQ4 (cobertura vs gold humano):** Quão bem o documento gerado cobre um documento de requisitos oficial produzido manualmente (P/R/F1 de requisitos)?
  - **RQ5 (engenharia do sistema agêntico):** Como os erros se propagam ao longo do pipeline de agentes, e como a escolha de modelo por agente (haiku × sonnet) afeta o trade-off custo × qualidade? *(esta é a RQ que fala diretamente ao SE4AS)*
- Contribuições: **sistema multi-agente completo, end-to-end, implementado**; **validação no mundo real (SGG-GO)**; **análise de propagação de erro e custo por agente** (lição de engenharia de sistemas agênticos); métricas quantitativas substituindo a avaliação qualitativa do PFC1; artefato open-source.

### 2. Trabalhos Relacionados
- Reaproveitar a estrutura temática do PFC1, mas **aprofundar a bibliografia** (o PFC1 tinha só ~9 fontes, várias preprints 2024–2025 com DOI placeholder).
- Adicionar fontes seminais: origem do INVEST, fundamentos de user stories (Cohn), surveys de elicitação de requisitos, LLM-as-judge, métricas de ASR.
- Verificar todos os DOIs (o template usa `ACM-Reference-Format.bst`).

### 3. Método / Arquitetura
- **Reescrever para 4 agentes** + 2 formatos de saída (IEEE 830 e empresa).
- Diagrama de arquitetura + fluxo de dados (criar — ver §5).
- Modelos reais: Groq whisper-large-v3-turbo; Claude haiku/sonnet por agente. Comunicação via watchdog (file-based).
- Descrever o caso real SGG-GO (reunião → documento) como objeto de estudo.

### 4. Desenho da Avaliação (Evaluation Setup)
- Datasets: AMI (texto, p/ personas) + corpus de áudio escolhido (p/ WER) + caso real SGG-GO.
- Para cada RQ, qual métrica, qual dado, qual protocolo. (Detalhe em §3 deste roadmap.)
- Protocolo do survey (constructos, escala Likert 5 pontos, n de respondentes).

### 5. Resultados e Discussão
- Um bloco por RQ, com tabelas e figuras. Números reais (ver §3).
- Discussão de propagação de erro entre estágios (anedota HIPOF/IPOF).

### 6. Ameaças à Validade
- Construto, interna, externa, de conclusão (ver §6 deste roadmap). **SBES espera esta seção.**

### 7. Conclusão e Trabalhos Futuros

### Disponibilidade de Artefatos *(seção obrigatória, não numerada)*
- Link do repositório GitHub + licença. Obrigatório mesmo que diga "código disponível em...".

### Agradecimentos *(opcional, não numerado)* + Referências

---

## 3. Experimentos e métricas — o que calcular/testar e ver resultados

Legenda de viabilidade: 🟢 dados já existem · 🟡 precisa de protocolo de anotação · 🔴 precisa adquirir dados novos.

### 3.1 Agente 1 — Transcrição (RQ1)

| Métrica | Como calcular | Dado | Ferramenta | Viab. |
|---|---|---|---|---|
| **WER** (Word Error Rate) = (S+D+I)/N | comparar hipótese vs referência | corpus áudio+transcrição (Common Voice PT / AMI áudio) | `jiwer` | 🔴 |
| **CER** (Character Error Rate) | idem nível de caractere | idem | `jiwer` | 🔴 |
| **RTF** (Real-Time Factor) = tempo_proc / duração_áudio | cronometrar | qualquer áudio | timestamps | 🟢 |
| Comparação Groq vs faster-whisper local | rodar os dois no mesmo set | idem | jiwer | 🔴 |

- **Construir:** script que roda `transcription_service` sobre o corpus e cospe WER/CER/RTF em CSV. Adicionar `jiwer` ao requirements.
- **Âncoras de expectativa** (literatura, para você saber se o resultado está coerente): whisper-large-v3 em reunião (AMI) ~15–20% WER (fala sobreposta é difícil); leitura limpa (LibriSpeech) ~2–4%; Common Voice PT ~7–10%.
- **Importante:** teste em **português** (idioma do uso real) — é o número que mais importa para o artigo.

### 3.2 Agente 2 — Personas + Histórias (RQ2)

| Métrica | Como calcular | Dado | Ferramenta | Viab. |
|---|---|---|---|---|
| **Precision/Recall/F1 de personas** | personas previstas vs papéis-gold do AMR (PM/Marketing/UI/Industrial Designer) | AMI texto (importável já) | `scikit-learn` | 🟡 (precisa codificar gold + protocolo de match) |
| **Acurácia de contagem de personas** | nº correto / nº esperado | 7 reuniões já rodadas (28/28) → escalar | script | 🟢→🔴 (escalar p/ 50–100) |
| **Taxa de conformidade INVEST** | % histórias que cumprem os 6 critérios | histórias geradas | LLM-judge (Claude) + validação manual | 🟡 |
| **Concordância entre avaliadores** (INVEST/match) | Cohen's kappa | amostra com 2 anotadores | sklearn | 🟡 |
| Descritivas: histórias/reunião, personas/reunião | média, DP | saídas | pandas | 🟢 |

- **Escalar de 7 → 50–100 reuniões** AMI (use `import_ami_dataset.py` para baixar; `data/ami_dataset/` está vazio hoje).
- **Teste de estresse "sem speaker labels"** (prometido no PFC1): rodar Agente 2 em texto corrido sem rótulos de falante — mede a robustez do prompt, não só do dado fácil.
- **Nota de dado:** o JSON de história hoje **não tem campo de score INVEST** — ou adiciona um passo de scoring, ou pontua à parte. Sem isso, INVEST não é nem armazenado nem computado.

### 3.3 Agente 3 — Documento gerado (RQ3 e RQ4) — o trunfo do artigo

**(a) Avaliação humana via Google Forms — JÁ EM COLETA:**

| Métrica | Como calcular | Ferramenta |
|---|---|---|
| **Média ± DP por constructo** (Completude/Acurácia, Clareza/Organização, Utilidade/Satisfação) | agregar respostas Likert 1–5 | pandas |
| **Alfa de Cronbach por constructo** (consistência interna; alvo ≥ 0,70) | fórmula sobre os itens do constructo | `pingouin` ou cálculo manual |
| **Distribuição de frequência** (gráfico de barras divergentes — padrão Likert) | contagem por nível | matplotlib |
| **NPS** (questão 0–10) = %promotores − %detratores | classificar 9–10 / 7–8 / 0–6 | pandas |
| **Comparação de subgrupos**: participou da reunião vs não | teste de Mann-Whitney U (Likert é ordinal) | scipy |
| **n** (nº de respondentes) | contar | — |

- ⚠️ **n pequeno é a maior ameaça** — reporte n explicitamente, use mediana além de média, e teste não-paramétrico.
- O constructo "participou da reunião" (P1 do form) habilita uma análise comparativa interessante (quem esteve na reunião percebe a acurácia diferente).

**(b) Cobertura vs documento oficial (RQ4) — gold standard existe:**

| Métrica | Como calcular | Dado | Viab. |
|---|---|---|---|
| **Recall de requisitos** = itens gerados que casam com o oficial / itens do oficial | protocolo de match item-a-item | PDF oficial + doc gerado | 🟡 |
| **Precision** = itens gerados válidos / itens gerados | idem | idem | 🟡 |
| **F1** | harmônica | — | 🟡 |

- Números brutos já levantados à mão em `analise-tcc/`: RF 5 vs 16 (oficial), RN 3 vs 27, UC 3 vs 26. Isso vira tabela de cobertura. Formalize o protocolo de match (manual ou assistido por LLM, com 2 anotadores → kappa).
- **Discussão honesta:** o sistema gera menos itens que o documento humano (recall baixo em RN/UC) — isso é um achado, não um fracasso. Discuta por quê (densidade de regras de negócio só ditas implicitamente, etc.).

### 3.4 End-to-end (RQ transversal)

| Métrica | Como calcular | Viab. |
|---|---|---|
| **Propagação de erro** | estudo de caso qualitativo (HIPOF→IPOF) mostrando erro de WER se propagando até o doc final | 🟢 |
| **Tempo de processamento por estágio** e total/reunião | cronometrar pipeline | 🟢 |
| **Custo por reunião** (tokens × preço da API) | somar tokens dos agentes | 🟢 |

- Custo e tempo são ótimos para o argumento de "viabilidade prática" — algo que o PFC1 não tinha.

---

## 4. Tabela-resumo: tudo que precisa virar número

| # | Métrica | Agente | Dado necessário | Status do dado |
|---|---|---|---|---|
| 1 | WER / CER | 1 | corpus áudio+ref (CV-PT / AMI áudio) | 🔴 adquirir |
| 2 | RTF, tempo, custo | 1+todos | rodar pipeline | 🟢 |
| 3 | Precision/Recall/F1 personas | 2 | AMI texto + gold roles | 🟡 protocolo |
| 4 | Conformidade INVEST + kappa | 2 | histórias + 2 anotadores | 🟡 protocolo |
| 5 | Média/DP/Cronbach/NPS por constructo | 3 | respostas do Google Forms | 🟢 coletando |
| 6 | Mann-Whitney subgrupos | 3 | respostas + P1 | 🟢 coletando |
| 7 | Cobertura (P/R/F1) vs doc oficial | 3 | PDF gold + doc gerado | 🟡 protocolo |
| 8 | Propagação de erro (qualitativo) | end-to-end | caso SGG-GO | 🟢 |

---

## 5. Figuras a criar (o PFC1 não tinha nenhuma)

1. **Diagrama de arquitetura** dos 4 agentes (pipeline file-based via watchdog).
2. **Fluxo de dados**: áudio → transcrição → personas/histórias JSON → documento (2 formatos).
3. **Gráfico de barras divergentes** das respostas Likert por constructo.
4. **Tabela/gráfico de cobertura** gerado vs oficial (RF/RN/UC).
5. (Opcional) screenshot de um trecho do documento gerado.
- Lembrete SBES: legenda de figura **embaixo**, de tabela **em cima**, toda figura com `\Description{}`.

---

## 6. Ameaças à validade (seção esperada no SBES)

- **Construto:** o questionário mede mesmo "qualidade do documento"? (mitigação: constructos Likert + alfa de Cronbach).
- **Interna:** quem avaliou participou da reunião? viés. Pontuação INVEST/match por um só anotador → use 2 + kappa.
- **Externa:** generalização — 1 caso real (SGG-GO) + reuniões AMI (cenário fictício de design de produto, não representa todo domínio). n pequeno no survey.
- **Conclusão:** n pequeno → use testes não-paramétricos, reporte mediana e intervalo, não só média.

---

## 7. Checklist de submissão SBES/CBSoft 2026

- [ ] Template ACM-like (`acmart.cls` já na pasta Escrita).
- [ ] Remover CCS Concepts e rodapé ACM de copyright.
- [ ] Headings em Title Case; seções numeradas até `\subsubsection`.
- [ ] Citações ACM numéricas (`\bibliographystyle{ACM-Reference-Format}`); nomes completos; DOIs verificados.
- [ ] Toda figura com `\Description{}`; legenda de tabela em cima, figura embaixo; `booktabs` (só `\midrule`).
- [ ] Emails de todos os autores; short title que caiba no cabeçalho.
- [ ] **Seção "Disponibilidade de Artefatos"** (obrigatória) com link do GitHub + licença.
- [ ] Artigo em **inglês** (decidido) — abstract, keywords, referências em EN.
- [ ] **Confirmar na chamada oficial do SE4AS o limite de páginas e tipos de submissão** (workshop ≠ SBES full; provável ~6–10 pg). Página: https://agents4good.github.io/se4as26-workshop/
- [ ] Foregrounding do ângulo **multi-agente/agêntico** no título, abstract e método (ver §0.5).
- [ ] Não mexer em margens/espaçamento/fonte (causa rejeição).

---

## 8. Ordem de execução sugerida (prioridade)

**Fase A — colher o que já está pronto (rápido, alto valor):**
1. Fechar o survey, calcular média/DP/Cronbach/NPS/Mann-Whitney (🟢, depende só dos respondentes).
2. Estudo de caso de propagação de erro + tempo + custo (🟢).
3. Tabela de cobertura vs documento oficial a partir do `analise-tcc/` (🟡, dados já levantados).

**Fase B — construir o harness de métricas:**
4. Script de Precision/Recall/F1 de personas no AMI; escalar para 50–100 reuniões (🟡→).
5. Scoring INVEST (LLM-judge + amostra manual com kappa) (🟡).

**Fase C — adquirir dado de áudio e fechar WER:**
6. Escolher corpus (Common Voice PT recomendado), rodar Groq vs local, calcular WER/CER/RTF (🔴).

**Fase D — escrever:**
7. Figuras (arquitetura + fluxo).
8. Redigir seção por seção (§2 deste roadmap), reescrevendo método para 4 agentes e bibliografia aprofundada.
9. Threats to validity + Artifact Availability + checklist final.

---

### Dependências novas a instalar (não existem hoje no projeto)
`jiwer` (WER/CER), `scikit-learn` (P/R/F1, kappa), `pandas`, `scipy` (Mann-Whitney), `pingouin` (Cronbach), `matplotlib` (figuras Likert).
