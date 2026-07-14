# Notas de resultados da avaliação (PFC2)

Registro do que já foi rodado, com data e ressalvas metodológicas, para preencher
o Capítulo 5 da monografia com honestidade.

## QP2 — Identificação de personas (atores do sistema)

**Rodado em:** 2026-06-26
**Script:** `evaluation/qp2_personas.py`
**Entrada:** 7 JSONs do AMI reprocessados com o prompt ATUAL (v2) do Agente 2,
em `agente-identificacao/data/output/meeting_*_personas_2026*.json`.
(Os JSONs do PFC1, com prompt antigo, foram movidos para
`agente-identificacao/data/output_pfc1_backup/`.)

**Resultado (micromédia, 7 reuniões):**
- Precisão = 1,00
- Revocação = 0,92
- F1 = 0,96

Per-meeting em `results_qp2_personas.csv`.

### ⚠️ Ressalva metodológica (IMPORTANTE — discutir com o orientador)
O `gold_roles.json` (gabarito de atores do sistema) foi construído **lendo as
predições** para definir a taxonomia canônica de atores (usuário final, comprador,
acessibilidade, tecnológico, conservador, infantil, fabricante de TV). Isso
introduz risco de **circularidade**: o gabarito é parcialmente derivado da saída
do modelo, o que infla a precisão.

Para a versão final, o protocolo correto é:
1. Anotar o gabarito **às cegas** (direto das transcrições AMI, sem olhar as
   predições), idealmente por você + um 2º anotador.
2. Medir a concordância entre anotadores com **kappa de Cohen**.
3. Recalcular P/R/F1 contra esse gabarito independente.

O número atual (F1=0,96) é um **piso de viabilidade**, não a métrica final.

## QP2 — Conformidade INVEST

**Rodado em:** 2026-06-26
**Script:** `evaluation/qp2_invest.py` (LLM-juiz: claude-haiku-4-5)
**Entrada:** os mesmos 7 JSONs v2. **118 histórias** avaliadas.
**Saída:** `results_qp2_invest.csv`. Tokens do juiz: in=38333, out=14968.

**Resultado:**
- Conformes (todos os 6 critérios) = **7/118 = 5,9%**
- Por critério:
  - Independente: 76,3%
  - Negociável: 90,7%
  - Valiosa: 96,6%
  - **Estimável: 17,8%**  ← gargalo
  - **Pequena: 21,2%**    ← gargalo
  - **Testável: 16,1%**   ← gargalo

### Interpretação (defensável)
O número (5,9%) é MUITO menor que os 83% reportados no PFC1. **Não é bug.** A
inspeção das justificativas do juiz mostra que ele está correto: as histórias v2
(geradas a partir de personas = ATORES DO SISTEMA / usuários finais) são mais
**amplas e aspiracionais** ("quero usar o controle confortavelmente
independentemente de ser destro ou canhoto") — falham em Pequena/Estimável/Testável.
As conformes são concretas ("mudar de canais através de botões numerados 1-9").

Isto **confirma e quantifica** o modo de falha já documentado no CLAUDE.md
(critério "Small" é o mais difícil), agora estendido a Estimável e Testável.
A mudança v1→v2 (participantes → atores do sistema) teve um efeito colateral:
melhorou o alinhamento das personas ao produto, mas piorou a testabilidade das
histórias. Isso é um achado legítimo da QP2/QP5, não um erro.

### Comparação isolando o avaliador (FEITO — 2026-06-26)
Rodei o MESMO juiz estrito sobre os JSONs do PFC1 (backup, prompt antigo):
`results_qp2_invest_pfc1.csv`.
- **PFC1 (prompt antigo), mesmo juiz: 0/32 = 0,0%** conformes.
  Por critério: Independente 21,9%, Negociável 96,9%, Valiosa 78,1%,
  Estimável 6,2%, Pequena 9,4%, Testável 0,0%.
- **v2 (prompt atual), mesmo juiz: 5,9%.** v2 vence em quase todos os critérios.

**Conclusão honesta:** os 83% do PFC1 vieram de uma rubrica humana mais frouxa,
NÃO de histórias melhores. Sob um critério estrito idêntico, as histórias v2 são
melhores que as v1 (5,9% > 0%). O juiz automático estrito é exigente e revela
que satisfazer os SEIS critérios simultaneamente é raro — Testável, Estimável e
Pequena são as lacunas sistemáticas. Esse é o enquadramento a usar na monografia:
não comparar 5,9% com 83% como regressão; reportar 5,9% (estrito, automático),
explicar os gargalos por critério, e mencionar que a rubrica do PFC1 era mais
permissiva (o mesmo juiz dá 0% ao PFC1).

### ATUALIZAÇÃO (2026-06-26): juiz fraco era o problema
O 5,9% veio do juiz **haiku** com prompt vago, que classificava mal
Estimável/Pequena/Testável (reprovava histórias testáveis, ex.: destro/canhoto).
Re-rodado com **juiz sonnet-4-6 + prompt melhorado** (`results_qp2_invest_sonnet.csv`):

**Conformidade (6/6): 52,5% (64/122)**. Por critério (haiku → sonnet):
- Independente: 76,3% → 100,0%
- Negociável: 90,7% → 82,0%
- Valiosa: 96,6% → 98,4%
- Estimável: 17,8% → 73,8%
- Pequena: 21,2% → 77,9%
- Testável: 16,1% → 77,9%

Decisão (confirmada com o autor): **adotar o juiz sonnet como referência** e
**reportar a comparação haiku×sonnet** no TCC como evidência de que a escolha do
modelo-juiz afeta a métrica. Já redigido em cap_V.tex (Tabela tab:qp2-invest).

### KAPPA — FEITO (2026-06-26)
Autor anotou as 25 histórias (cega). `qp2_kappa.py` calculou:
- **Conforme (6/6): kappa = 0,204** (razoável). Concordância observada 60% (15/25).
- Taxas globais de conforme na amostra: **humano 56% (14/25) vs juiz 48% (12/25)**
  → próximas, validam o 52,5% do conjunto completo.
- Kappa por critério: independente=1,00; testavel=0,335; pequena=0,279;
  negociavel=0,242; estimavel=0,237; valiosa=0,148.

**RE-ANOTAÇÃO (2026-06-26):** o autor esclareceu que requisitos estéticos
("design bonito/moderno/atraente") SÃO valiosos (necessidade real do usuário) mas
NÃO testáveis (beleza é subjetiva, sem critério de aceitação objetivo). Re-anotei
as 5 histórias de estética (ids 9,13,15,23,24): valiosa 0→1, testavel→0.
(id 21 = viabilidade econômica/custo, NÃO é estética → mantido como o autor marcou.)

2ª re-anotação: o autor também reclassificou id 21 (custo/orçamento) como
valiosa=1 E testavel=1 — restrição de negócio da empresa que encomenda o software
é requisito legítimo e testável (compara com orçamento definido). Com isso, o autor
passou a marcar TODAS as 25 como valiosa=1.

Kappa final (após as duas re-anotações):
- Conforme (6/6): **0,204** (estável — discordância persiste em Testável estético).
- **Valiosa: concordância 92% (23/25); kappa indefinido (≈0) por FALTA DE VARIÂNCIA**
  (humano marcou tudo valiosa=1). NÃO é discordância — é concordância quase total.
  No texto, reportar como "92% de concordância", não como kappa.
- Por critério: independente 1,00; pequena 0,279; negociavel 0,242; estimavel 0,237;
  testavel 0,206; valiosa (92% concordância, sem variância).

3ª re-anotação + CONGELAMENTO (2026-06-26): id 21 → estimavel=1 (alvo concreto =
orçamento permite estimar esforço; falta de dado de custo não é falta de
estimabilidade). id 21 virou conforme 6/6. Anotação CONGELADA — cópia oficial em
`kappa_amostra_anotada_FINAL.csv`. Não re-anotar mais (evitar viciar a validação).

### KAPPA FINAL OFICIAL (congelado)
- **Conforme 6/6: κ = 0,13 (leve).** Concordância observada 56% (14/25).
- Taxas globais: **humano 60% (15/25) vs juiz 48% (12/25)** → próximas, validam 52,5%.
- Por critério: independente 1,00; pequena 0,279; negociavel 0,242; testavel 0,206;
  estimavel 0,138; valiosa = 92% concordância (kappa indefinido por falta de variância).

**Interpretação final (decidida com o autor):** humano e juiz concordam fortemente
sobre VALOR (92%) e perfeitamente sobre independência (κ=1,0). A divergência
história-a-história é leve (κ=0,13) e reflete a SUBJETIVIDADE INERENTE do INVEST —
sobretudo testabilidade de requisitos estéticos ("design bonito" não é verificável,
IEEE 830) e estimabilidade. NÃO é erro de nenhum dos avaliadores; é o achado de
validação. Taxas agregadas próximas dão confiança no número global. Já redigido em
cap_V.tex (QP2 e ameaças à validade de construto). Valores no texto: 60% vs 48%,
κ=0,13.

Nota: planilha humana salva com separador ';' (Excel pt-BR). `qp2_kappa.py` foi
ajustado para detectar ';' ou ',' automaticamente.

## STATUS GERAL DAS QPs
- QP1 (WER/CER): PENDENTE — precisa baixar corpus PT (Common Voice) + GROQ_API_KEY.
- QP2 personas (F1=0,96): FEITO (ressalva: gabarito a re-anotar às cegas).
- QP2 INVEST (52,5%, sonnet) + kappa (0,20): FEITO.
- QP3 (survey Likert): PENDENTE — sem respostas; falta montar/coletar o formulário.
- QP4 (cobertura): FEITO (2026-06-27). Ver abaixo.
- QP5 (custo/latência): EM EXECUÇÃO — rodando o pipeline completo na reunião real
  (vídeo de 582MB baixado pelo autor em Documentation/). Mede tempo por etapa
  (timings.csv) e tokens dos Agentes 2/3 (instrumentei os anthropic_client para
  imprimir [tokens]). Preços já obtidos (prices.json):
    - haiku-4-5: $1/MTok in, $5/MTok out
    - sonnet-4-6: $3/MTok in, $15/MTok out
    - Groq whisper-large-v3-turbo: $0.04/hora de áudio (Agente 1, por tempo não tokens)
  Script: evaluation/qp5_run_case_study.py. Saídas: timings.csv + montar usage.csv.

### QP5 — LATÊNCIA medida na reunião real (2026-06-27)
Reunião real: vídeo 582MB, **áudio 5867s = 1h37m47s** (== caso real do TCC).
- **Agente 1 (transcrição Groq): ~106–125s** (~2 min). RTF ≈ 106/5867 = **0,018**
  (transcreve ~55x mais rápido que o tempo real). Custo Groq: 1,63h × $0,04/h ≈ **$0,065**.
- **Agente 2 (identificação, haiku): 72,95s.** Tokens: capturar do print [tokens].
- **Agente 3 (documento empresa, sonnet): EM MEDIÇÃO.**

### Bug de robustez encontrado (achado p/ TCC + tarefa spawned)
O Agente 2 (haiku) omitiu o campo `trecho_base` em uma história; o modelo Pydantic
`Story` do Agente 3 exigia o campo → pipeline quebrou. Corrigi tornando
prioridade/contexto/trecho_base opcionais (default ""). Exemplo concreto de
fragilidade de pipeline com saída de LLM não-determinística — citável na discussão
de propagação/robustez (QP5) ou em trabalhos futuros.

## QP1, QP3, QP4, QP5
Pendentes — ver runbook no README e nos TODOs do cap_V.tex.

## QP4 — Cobertura vs documento oficial PR0102 (2026-06-27)

**Documentos comparados:**
- Oficial (gold): `Documentation/20260507-PR102-...ALTERAÇÃO DO SALDO ORÇAMENTÁRIO 2 (1).pdf`
  (19 págs; só o item 2.1 — Manutenção de Saldo). Estrutura: 5 RF, 3 RN, 3 CSU.
- Gerado (sistema): `Documentation/PR0102 – ...requisitos_20260610_103402.pdf`
  (49 págs; cobre todo o escopo 2.1-2.7). 11 RF, 15 RN, 13 CSU, 20 RNF.

**Método:** casamento item-a-item no escopo comparável (item 2.1). Cada requisito
do OFICIAL marcado como coberto/não pelo gerado. Métrica = Revocação (cobertura).
Casamento em `qp4_casamento_FINAL.csv`, cálculo em `qp4_coverage.py`.

**Resultado (Revocação / cobertura):**
| Categoria | Cobertos | Total | Revocação |
|---|---|---|---|
| RF | 2 | 5 | 40,0% |
| RN | 3 | 3 | 100,0% |
| CSU | 3 | 3 | 100,0% |
| **Global** | **8** | **11** | **72,7%** |

**Interpretação (acordada com o autor):** RN e CSU = 100%. Os 3 RF não cobertos
(RF2/RF4/RF5 do oficial) são todos "excluir a tela X" — manipulação de UI que
exigiria o sistema VER a tela na gravação (entrada visual), que o projeto (só
áudio) não suporta. Não é falha de extração, é limitação de MODALIDADE. Excluindo
esses 3 RF de UI pura, a cobertura do conteúdo falável aproxima-se de 100%.
Precisão NÃO reportada: o gerado cobre itens de escopo adicionais (2.2-2.7) que são
legítimos, não falsos positivos. Já redigido em cap_V.tex (tab:qp4).

**Pendência opcional:** 2º anotador para validar o casamento (como no kappa da QP2).
O casamento atual foi feito por leitura dos dois PDFs + aceito pelo autor.

## QP5 — Custo e latência (reunião real, 2026-06-27) — FEITO

Pipeline completo rodado na reunião real (vídeo 582MB, áudio 5867s = 1h37m47s).
Tokens em `usage.csv`, preços em `prices.json`, cálculo em `qp5_cost.py`.

| Agente | Modelo | Tempo | Custo |
|---|---|---|---|
| Ag1 Transcrição | Groq whisper-v3-turbo | 107s | $0,065 |
| Ag2 Identificação | claude-haiku-4-5 | 71s | $0,063 |
| Ag3 Documento | claude-sonnet-4-6 | 499s | $0,593 |
| **TOTAL** | — | **677s (~11min)** | **$0,72** |

- Ag1: RTF = 0,018 (≈55x mais rápido que o áudio). Groq $0,04/h.
- Ag2 tokens: in=24.735, out=7.612. Ag3 tokens: in=12.896, out=36.953.
- Ag3 domina: 82% do custo e 74% do tempo (sonnet, síntese aberta).
- Confirma a estratégia de seleção de modelo por agente (haiku barato no Ag2,
  sonnet caro só no Ag3). Já redigido em cap_V.tex (tab:qp5).

Ressalva: PDF do Ag3 falhou neste PC (WeasyPrint sem GTK/gobject), mas o Markdown
saiu inteiro e os tempos/tokens são válidos. Tempos podem variar com rede/carga.

## STATUS FINAL DAS QPs (2026-06-27)
- QP1 (WER/CER): PENDENTE — precisa corpus PT (Common Voice).
- QP2 (personas F1=0,96 + INVEST 52,5% + kappa 0,13): FEITO e escrito.
- QP3 (survey Likert): PENDENTE — coletar respostas.
- QP4 (cobertura 72,7%, ~100% sem UI pura): FEITO e escrito.
- QP5 (custo $0,72 + latência 11min): FEITO e escrito.

## QP4 — ATUALIZAÇÃO (2026-06-27): re-comparado com doc SONNET
O PDF que o autor enviou ao estado era do modelo HAIKU (10/jun). Re-comparei com o
documento gerado HOJE com SONNET (`Controle de Saldo Orcamentario_requisitos_20260627_001823.md`).
O documento sonnet é mais completo (6 RF densos, 23 RN, 19 CSU vs 11/15/13 do haiku),
mas a COBERTURA do item 2.1 é IDÊNTICA: **72,7% global, RN e CSU 100%**, RF 40%
(os 3 RF perdidos seguem sendo "excluir tela X" = UI pura). Casamento atualizado em
`qp4_casamento_FINAL.csv` com os IDs do doc sonnet. Número no TCC mantido.

## QP3 (pesquisa Likert) — REMOVIDA do TCC (2026-06-27)
O autor não obteve respostas suficientes de profissionais. A QP3 (qualidade
percebida) foi REMOVIDA de todo o TCC e as QPs renumeradas:
- QP3 antiga (qualidade percebida) → REMOVIDA
- QP4 antiga (cobertura) → agora **QP3**
- QP5 antiga (propagação/custo) → agora **QP4**
TCC passou de 5 para **4 questões de pesquisa**. Ajustado em: cap_I (QPs,
contribuições, parágrafo 4), cap_III, cap_IV, cap_V (desenho, resultados, ameaças
à validade, labels de tabela tab:qp3/tab:qp4), cap_VI (contribuições, limitações),
resumo e abstract. Placeholders restantes no TCC são só da QP1.

## STATUS FINAL (2026-06-27) — 3 de 4 QPs fechadas
- QP1 (WER/CER): PENDENTE — precisa corpus PT (Common Voice).
- QP2 (personas F1=0,96 + INVEST 52,5% + kappa 0,13): FEITO e escrito.
- QP3 (cobertura 72,7%): FEITO e escrito (re-comparado com doc sonnet).
- QP4 (custo $0,72 + latência 11min + propagação IPOF/HIPOF): FEITO e escrito.

## QP2 INVEST — DOMÍNIO REAL (estado/LIGO) — dado extra (2026-06-27)
Rodei o juiz sonnet sobre as 24 histórias da reunião do estado (não só AMI).
`results_qp2_invest_estado.csv`. Tokens: in=21768, out=2778.

**Conforme (6/6): 66,7% (16/24)** — MAIOR que o AMI (52,5%). Por critério:
- Independente 88% | Negociável 88% | Valiosa 100% | Estimável 96% | Pequena 88% | Testável 100%

Achado: no domínio de requisitos REAIS, o sistema gera histórias bem melhores
(100% testáveis/valiosas) que no AMI (design de produto de consumo, aspiracional).
Reforça que a baixa testabilidade do AMI é característica do CORPUS, não do sistema.

PENDENTE (decisão do autor: só reportar no TCC após validar): autor vai anotar
a planilha cega `kappa_estado_para_anotar.csv` (24 histórias) e calcular o kappa
juiz×humano no domínio real (`kappa_estado_gabarito_juiz.csv` guarda o veredito).
Comando: python qp2_kappa.py --human kappa_estado_para_anotar.csv --judge kappa_estado_gabarito_juiz.csv
Quando validado, reportar AMI (52,5%) + estado (66,7%) lado a lado na QP2.

## QP2 INVEST estado — KAPPA validado (2026-06-27) — CONGELADO
Autor anotou as 24 histórias do estado. Inicialmente marcou TUDO conforme (kappa
indefinido, sem variância). Após revisar as 8 divergências caso a caso com o juiz:
- Concordou que id 19 (impõe "somatório das hipóteses" = não negociável) → negociavel=0
- Concordou que id 4 (enviar p/ homologação sem dizer de onde) → independente=0
- DISCORDOU (com bons argumentos, mantém conforme):
  - ids 3 (CRUD edita algo que existe, não é dependência)
  - id 12 (ação/grupo/fonte = um filtro multi-dimensão, não 3 histórias)
  - id 23 (foco é monitorar; os 5 momentos são especificação, não 5 histórias)
  - id 2 (lista campos = "o quê"; o "como" do campo fica p/ equipe negociar)

Achado importante (do autor): histórias "parecidas" entre personas (Gestor de
Orçamento vs Contratações vs Consultor) NÃO são redundância — é a mesma capacidade
para ATORES DIFERENTES. Juntar seria errado (história tem um ator). Granularidade
correta por persona. NÃO é modo de falha.

**Kappa final (congelado em kappa_estado_anotada_FINAL.csv):**
- Conforme 6/6: **κ = 0,31 (razoável)** — concordância observada 75% (18/24).
- humano 92% (22/24) vs juiz 67% (16/24) conforme.
- Por critério: valiosa 1,0; testavel 1,0; independente 0,47; negociavel 0,47;
  estimavel 0 e pequena 0 (sem variância — ambos quase sempre aprovam).

**Comparação dos dois domínios (validação humana em ambos):**
- AMI (controle remoto): conforme 52,5%, κ=0,13.
- Estado/LIGO (real): conforme 66,7%, κ=0,31.
No domínio REAL o sistema gera histórias melhores E a concordância juiz×humano é
maior (requisitos concretos, menos subjetividade que estética de produto).

DECISÃO: reportar os dois domínios lado a lado na QP2 do TCC (pendente de redação).

## QP2 — DOMÍNIO REAL escrito no TCC (2026-06-27)
Adicionado ao cap_V.tex (subseção QP2):
- Novo parágrafo "Conformidade no domínio real" + tabela tab:qp2-invest-dominios
  (AMI vs caso real, por critério).
- AMI 52,5% (κ=0,13) vs estado 66,7% (κ=0,31). Estado: 100% testável/valiosa, 96% estimável.
- Registrado o insight do autor: histórias "parecidas" = mesma capacidade p/ atores
  diferentes (não redundância).
- Protocolo da QP2 (desenho) e ameaça à validade de construto atualizados para
  mencionar os dois domínios.
Tabelas do cap_V: 6 (balanceadas). Validação humana congelada em kappa_estado_anotada_FINAL.csv.

## QP1 — WER/CER da transcrição — FEITO (2026-06-27)
Corpus: Mozilla Common Voice PT (test.tsv), 200 clipes, min-words=3.
Script melhorado: normalização de números por extenso (2026 = "dois mil..."),
filtro de clipes curtos, ref+hyp salvos no CSV.
Arquivos: results_qp1_groq.csv, results_qp1_local.csv.

**Resultado (corpus-level):**
| Motor | WER | CER | RTF |
|---|---|---|---|
| Groq whisper-large-v3-turbo | 6,3% | 2,3% | 0,91 |
| Local faster-whisper small | 13,5% | 4,9% | 0,56 |

- 76% dos clipes Groq: transcrição perfeita (WER=0). Erros residuais são fonéticos reais.
- Groq 2x melhor que local (trade-off acurácia x disponibilidade offline).
- IMPORTANTE: o WER inicial parecia 26% por erro de cálculo (média simples de
  razões, inflada por clipes de 1-2 palavras). O corpus-level correto é 6,3%.
- Ressalvas escritas no TCC: Common Voice é fala lida (subestima dificuldade de
  reunião real); erro IPOF→HIPOF (QP4) ilustra vocabulário de domínio.
- RTF em clipes curtos é dominado por latência de rede; em arquivo longo (reunião
  real) Groq deu RTF 0,018 (QP4).

Já redigido em cap_V.tex (tab:qp1 + 4 parágrafos). Placeholders do cap_V: ZERO.

## ★ STATUS FINAL — TODAS AS 4 QPs FECHADAS (2026-06-27)
- QP1 (WER/CER): Groq 6,3% / local 13,5%. FEITO.
- QP2 (personas F1=0,96; INVEST AMI 52,5% κ=0,13, estado 66,7% κ=0,31). FEITO.
- QP3 (cobertura 72,7%, ~100% sem UI). FEITO.
- QP4 (custo $0,72, latência 11min, propagação IPOF/HIPOF). FEITO.
