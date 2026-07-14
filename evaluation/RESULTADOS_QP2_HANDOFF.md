# Resultados da QP2 — Documento de Continuidade (Handoff)

Documento para retomar o trabalho em outro computador. Reúne TODOS os resultados
fechados da **QP2** (identificação de personas, conformidade INVEST e validação por
kappa), com os números, a interpretação acordada, como reproduzir e o que ainda falta.

Data de fechamento: 2026-06-27. Ambiente: Windows (o pipeline teve problemas neste PC
— PDF do WeasyPrint e captura de tokens; ver seção "Pendências de ambiente").

---

## 1. RESUMO DOS NÚMEROS (o que vai no TCC)

### 1.1 Identificação de personas (atores do sistema)
Sobre as **7 reuniões do corpus AMI**, reprocessadas com o prompt ATUAL (v2) do Agente 2.

| Métrica | Valor |
|---|---|
| Precisão | **1,00 (100%)** |
| Revocação | **0,92 (92%)** |
| F1 | **0,96 (96%)** |

- Micromédia sobre as 7 reuniões. Precisão 1,00 = não inventa atores falsos.
- Revocação 0,92 = recupera quase todos os atores; perdeu poucos perfis pouco citados
  (ex.: "comprador" numa reunião).

### 1.2 Conformidade INVEST das histórias de usuário
Sobre **122 histórias** geradas. Avaliadas por LLM-juiz. Comparação de dois juízes:

| Critério | Juiz haiku-4-5 (fraco) | **Juiz sonnet-4-6 (REFERÊNCIA)** |
|---|---:|---:|
| Independente | 76,3% | **100,0%** |
| Negociável | 90,7% | **82,0%** |
| Valiosa | 96,6% | **98,4%** |
| Estimável | 17,8% | **73,8%** |
| Pequena | 21,2% | **77,9%** |
| Testável | 16,1% | **77,9%** |
| **Conforme (todos os 6)** | **5,9%** | **52,5%** |

- **Adota-se o juiz sonnet-4-6 como referência.** O número oficial é **52,5%**.
- O 5,9% do haiku era ARTEFATO do juiz fraco (reprovava histórias testáveis).
  A comparação haiku×sonnet é reportada de propósito como evidência de que a escolha
  do modelo-juiz afeta a métrica (reforça a QP5 custo×qualidade).

### 1.3 Validação do juiz (kappa de Cohen) — amostra de 25 histórias anotada à mão
Anotação CEGA ao veredito do juiz, congelada.

| Medida | Valor |
|---|---|
| Conforme 6/6 — humano (autor) | 60% (15/25) |
| Conforme 6/6 — juiz (sonnet) | 48% (12/25) |
| Concordância observada | 56% (14/25) |
| **Kappa de Cohen (conforme 6/6)** | **0,13 (leve)** |
| Kappa Independente | 1,00 (perfeita) |
| Concordância Valiosa | 92% (kappa indefinido por falta de variância) |
| Kappa Testável | 0,21 |
| Kappa Pequena | 0,28 · Negociável 0,24 · Estimável 0,14 |

---

## 2. INTERPRETAÇÃO ACORDADA (como escrever no TCC)

1. **Personas:** o agente identifica muito bem os atores do sistema (F1 96%, precisão
   perfeita). Parte forte do sistema.

2. **INVEST:** ~metade das histórias (52,5%) atende os 6 critérios ao mesmo tempo.
   Quase todas são **valiosas (98%)** e **independentes (100%)**. O que derruba a outra
   metade é **granularidade** (Estimável/Pequena/Testável ~74–78%): histórias amplas
   demais. Confirma que "Small" é o modo de falha predominante (já antecipado).

3. **Escolha do juiz importa:** trocar haiku→sonnet subiu de 5,9%→52,5%. Avaliação
   automática por LLM exige juiz forte + validação humana. Vira ponto de ameaça à
   validade de construto.

4. **Validação (kappa 0,13, leve):** as taxas globais batem (60% vs 48%), o que dá
   confiança no número. Mas a concordância história-a-história é baixa por
   SUBJETIVIDADE INERENTE do INVEST. Ponto-chave decidido com o autor:
   - Humano e juiz **concordam sobre VALOR** (92%) e independência (κ=1,0).
   - Divergem na **TESTABILIDADE de requisitos estéticos**. O autor aplica o princípio
     de verificabilidade (IEEE 830): "design bonito/atraente" é subjetivo, não admite
     critério de aceitação objetivo → requisito fraco. O juiz é mais permissivo.
   - Restrições com referência objetiva (ex.: "dentro do orçamento") permanecem
     testáveis e valiosas.
   - Conclusão: parte da não-conformidade reflete RIGOR do avaliador humano, não erro
     do sistema gerador. Divergência conceitual e defensável, não ruído.

---

## 3. ONDE ISSO JÁ ESTÁ ESCRITO NO TCC

Arquivo: `Documentation/Monografia/tex/cap_V.tex`
- Subseção **QP2** (`\subsection{QP2: Identificação...}`): tabelas tab:qp2-personas e
  tab:qp2-invest com os números acima + parágrafos de discussão + parágrafo do kappa.
- Seção **Ameaças à Validade** → "Validade de construto": cita sensibilidade ao
  modelo-juiz e o kappa.
- `\subsection{Desenho...}` → parágrafo QP2 do protocolo (dois juízes, anotação cega).

Outras inserções já feitas (não-QP2, mas relacionadas):
- `main.tex`: `\tabelas[figtab]` (gera lista de tabelas).
- `tex/cap_VI.tex`: licença MIT citada (TODO removido).
- `pre/pre_aprovacao.tex`: banca (William Divino Ferreira; Paulo Marcos a completar).
- `LICENSE` (MIT) na raiz do repo.

Placeholders [VALOR]/[N] que AINDA faltam no cap_V.tex são das outras QPs (1, 3, 4, 5).

---

## 4. ARQUIVOS GERADOS (em evaluation/)

| Arquivo | Conteúdo |
|---|---|
| `results_qp2_personas.csv` | P/R/F1 de personas por reunião + micromédia |
| `results_qp2_invest_sonnet.csv` | INVEST por história (juiz sonnet, REFERÊNCIA) |
| `results_qp2_invest.csv` | INVEST por história (juiz haiku, comparação) |
| `results_qp2_invest_pfc1.csv` | INVEST juiz haiku sobre JSONs antigos do PFC1 (deu 0%) |
| `gold_roles.json` | Gabarito de atores do sistema por reunião (ver ressalva §6) |
| `aliases.json` | Protocolo de casamento papel previsto → canônico |
| `kappa_amostra_anotada_FINAL.csv` | Amostra de 25 anotada à mão (CONGELADA) |
| `kappa_amostra_para_anotar.csv` | Mesma planilha (separador ';') |
| `kappa_amostra_gabarito_juiz.csv` | Veredito do juiz para a amostra |
| `qp2_kappa.py` | Script que calcula o kappa humano×juiz |
| `NOTES_resultados.md` | Diário detalhado de tudo (com timestamps e ressalvas) |

Dados de entrada (JSONs do Agente 2, prompt v2):
`agente-identificacao/data/output/meeting_*_personas_2026*.json` (7 reuniões).
Backup dos JSONs antigos do PFC1: `agente-identificacao/data/output_pfc1_backup/`.

---

## 5. COMO REPRODUZIR (no outro computador)

Pré-requisitos: venv do `agente-identificacao` com `anthropic`, `python-dotenv`,
`scikit-learn` (opcional), e `ANTHROPIC_API_KEY` no `agente-identificacao/.env`.

```bash
# 1) Personas P/R/F1
cd evaluation
python qp2_personas.py \
    --pred-dir ../agente-identificacao/data/output \
    --gold gold_roles.json --aliases aliases.json \
    --out results_qp2_personas.csv

# 2) INVEST com o juiz de REFERÊNCIA (sonnet)
cd ../agente-identificacao
python ../evaluation/qp2_invest.py \
    --pred-dir data/output \
    --model claude-sonnet-4-6 \
    --out ../evaluation/results_qp2_invest_sonnet.csv

# 3) Kappa humano×juiz (após anotar a amostra)
cd ../evaluation
python qp2_kappa.py \
    --human kappa_amostra_anotada_FINAL.csv \
    --judge kappa_amostra_gabarito_juiz.csv
```

O prompt do juiz INVEST (já calibrado) está em `evaluation/qp2_invest.py`
(JUDGE_SYSTEM + JUDGE_PROMPT), com definições explícitas de cada critério.

---

## 6. RESSALVAS METODOLÓGICAS (ser honesto com a banca)

1. **Gabarito de personas (circularidade parcial):** o `gold_roles.json` foi
   construído lendo as predições para definir a taxonomia de atores. Há risco de
   circularidade que infla a precisão. Para a versão final, o ideal é anotar o
   gabarito ÀS CEGAS (direto das transcrições AMI) + 2º anotador. O F1=0,96 é um
   "piso de viabilidade", não a métrica definitiva.

2. **Re-anotação do kappa (3 rodadas):** a amostra foi re-anotada 3x enquanto o autor
   calibrava sua interpretação dos critérios (estética = valiosa mas não testável;
   custo/orçamento = valioso e testável; estimabilidade do id 21). Isso é legítimo
   (construção de rubrica), mas, se a banca perguntar, a resposta é: "refinei minha
   rubrica de anotação até estabilizar minha interpretação, e então congelei". A
   anotação final está congelada em `kappa_amostra_anotada_FINAL.csv`.

3. **Comparação PFC1 (83%) vs PFC2 (52,5%):** NÃO são comparáveis diretamente —
   mudaram o gerador (prompt v1→v2) E o avaliador (rubrica humana frouxa → LLM-juiz
   estrito). Sob o MESMO juiz estrito, o PFC1 dá 0% e o v2 dá 5,9% (haiku). Não
   apresentar como regressão.

---

## 7. PENDÊNCIAS DE AMBIENTE (resolver no outro PC)

Problemas observados neste Windows que devem ser checados no outro computador:
- **WeasyPrint não gera PDF** ("cannot load library 'gobject-2.0-0'"). Falta o GTK
  runtime. O Markdown é gerado normalmente; só o PDF falha. Instalar GTK/gobject ou
  usar o engine pandoc para PDF.
- **Captura de tokens (QP5):** instrumentei `agente-identificacao/src/anthropic_client.py`
  e `agente-srs/src/anthropic_client.py` para imprimir `[tokens]`. O Agente 3 imprimiu
  certo; o Agente 2 via main.py não apareceu no log (verificar se persona_identifier
  usa o AnthropicClient instrumentado, ou capturar stdout sem filtro).

---

## 8. O QUE FALTA (outras QPs — não-QP2)

- **QP1 (WER/CER):** baixar corpus PT (Mozilla Common Voice), rodar
  `evaluation/qp1_wer_cer.py` com GROQ_API_KEY. Script pronto.
- **QP3 (pesquisa Likert):** montar Google Forms, coletar respostas de profissionais,
  criar `qp3_survey.py` (média/DP/Cronbach/Mann-Whitney). Sem respostas ainda.
- **QP4 (cobertura P/R/F1):** casamento item-a-item do documento gerado vs PR0102
  (escopo item 2.1). Documento gerado já existe:
  `agente-srs/data/output/Controle de Saldo Orcamentario_requisitos_20260627_001823.md`.
  Oficial em `analise-tcc/comparacao_PR0102*.md`. Falta montar a planilha de casamento.
- **QP5 (custo/latência):** ver pendências de ambiente §7. Latência já parcialmente
  medida na reunião real: Agente 1 ~106–125s (RTF~0,018), Agente 2 ~73s, Agente 3
  ~499s. Tokens do Agente 3 (sonnet): in=12.896, out=36.953. Preços em
  `evaluation/prices.json`.
```
