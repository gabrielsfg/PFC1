# Comparação v2 (pós-melhorias) — Documento gerado vs. Documento modelo (PR0102)

> Segunda rodada de comparação, **após** implementar as melhorias de prompt P1–P4/P6
> (ver `comparacao_PR0102.md` para a 1ª análise e as recomendações).
>
> - **Gerado:** `..._personas_20260608_133044_requisitos_20260608_133354.md`
> - **Modelo:** `20260507-PR102-ECONOMIA-EVOLUÇÃO IPOF-LOA-EMPENHO-ALTERAÇÃO DO SALDO ORÇAMENTÁRIO 2.pdf`
> - **Modelo LLM:** identificação = `claude-sonnet-4-6`; documento (agente-srs) = `claude-haiku-4-5`

---

## Veredito

Convergência **alta** nos pontos centrais discutidos na reunião e presentes no exemplo deles.
Em relação à v1, houve salto de qualidade: **atores do sistema corretos**, **zero ruído de gestão
de projeto nos requisitos** e RF/CSU focados em comportamento do software.

---

## 1. Evolução em relação à v1 (antes × depois das melhorias)

| Aspecto | v1 (antes) | v2 (depois) |
|---|---|---|
| Personas/atores | 10 participantes da reunião (Bruno, André...) | **4 atores do sistema** (Gestor de Orçamento JASO, Usuário do Órgão, Admin/TI, Gestor da LOA) |
| Ruído de gestão de projeto | RF11–RF16 e várias RN eram EAP/prazos/mapeamento | **0 nos requisitos**; movido para Anexo "Gestão e Decisões do Projeto" |
| Numeração RN | RN01 repetido por grupo | **RN1…RN20 contínuo** |
| Casos de uso | "UC" | **"CSU1…CSU16"** |
| Foco dos RF | misturava produto e processo | **100% comportamento do software** |

---

## 2. Estrutura do documento gerado (v2)

- **Funcionalidade:** "Controle Granular de Saldo Orçamentário" (substituir controle macro por chave
  composta: exercício, unidade, ação orçamentária, grupo de despesa, fonte de recurso).
- **16 RF**, **20 RN** (contínuo), **16 CSU**, **26 RNF**, + **Anexo de Gestão de Projeto**.
- **4 atores do sistema** (todos perfis de uso, não participantes da reunião).

---

## 3. Pontos que os DOIS documentos identificaram (convergência)

| Ponto discutido na reunião | Modelo deles (PR0102) | Gerado (v2) |
|---|---|---|
| Granularidade multidimensional (exercício, unidade, **ação orçamentária, grupo de despesa, fonte de recurso**) | RF1/RF3 (filtros e colunas) | RF1 + RN1 |
| Inclusão/cadastro de saldo | RF3 "Inclusão parâmetros" | RF1 / CSU1 |
| Edição/alteração de saldo | RF1 popup "Editar saldo orçamentário" | RF2 / CSU3 |
| Consulta de saldo | RF1 "Manutenção/Consultar" | RF5 / CSU6 |
| Multiseleção de ação/grupo/fonte | RF3 (multiseleção) | RF1 inclusão em massa / CSU2 |
| Incluir com valor zerado / sem dotação (flag Sim/Não) | RF3 "Incluir parâmetros com valor zerado?" | RF3 "Validação e alerta de saldo sem dotação" |

➡️ **Destaque:** a **flag Sim/Não para saldo sem dotação/zerado** é um detalhe muito específico que os dois
capturaram — forte evidência de que a IA "ouviu" a reunião com precisão.

---

## 4. O gerado cobriu MAIS escopo (e isso é correto)

O PDF deles documenta **apenas o item 2.1** do projeto (a tela de Manutenção de Saldo). A reunião — e o
documento gerado — cobriram **todo o escopo** (itens 2.1 a 2.7, conforme registrado no próprio Anexo de Gestão
de Projeto do gerado: "2.1 primeiro, 2.7 em execução, depois 2.4, 2.5, 2.3, 2.2, 2.6"). Por isso o gerado tem,
além do núcleo, pontos que o PDF não cobre (porque são outros itens de escopo, documentados à parte):

- **Validação de saldo nos pontos de consumo:** envio, alteração, homologação, autorização de IPOF e
  contratações (RF7–RF11, CSU7–CSU12).
- **Exercícios futuros sem programa de trabalho** (RF13, CSU13).
- **Limites e monitoramento da LOA** (RF14–RF16, CSU14–CSU16).
- **Componente centralizado de cálculo/validação de saldo** (RF12 — derivado da fala sobre mapear os pontos
  de checagem de saldo no código).

---

## 5. O que o modelo deles tem e o gerado NÃO tem (limitação justa)

Tudo relativo à **concretude de UI**, que vem dos protótipos (ausentes no áudio):

- Caminho de menu (`>> Planejamento e Execução Orçamentária >> IPOF >> Manutenção de Saldo Orçamentário`).
- Título de tela, renomear telas e **excluir** telas específicas (RF2/RF4/RF5 deles são "Excluir a tela X").
- Filtros campo a campo, colunas da grade, paginação (5,10,25,50,100,200), ordenação, botões.
- Integração com o **SIOFI** (busca de orçamento) e o detalhamento da classificação orçamentária.

➡️ Não é falha de prompt — é limitação de insumo (sem prints/protótipos). Mitigável no futuro com entrada
multimodal (anexar telas/protótipos).

---

## 6. Ponto de atenção — fidelidade terminológica (erro de transcrição)

O gerado escreve **"HIPOF"** em vários lugares; o sistema real é **"IPOF"** (Instrumento de Planejamento,
Orçamento e Finanças). É um **erro de transcrição** do Agente 1 (Whisper ouviu "IPOF" como "HIPOF") que se
propagou para o documento. Excelente exemplo para a seção de limitações do TCC: **a precisão do Agente 1
(WER/CER) impacta diretamente a qualidade dos agentes seguintes**.

---

## 7. Resumo

| Critério | Avaliação |
|---|---|
| Recall dos pontos centrais | **Alto** — granularidade, CRUD de saldo, multiseleção, flag valor zerado/sem dotação |
| Cobertura de escopo | Mais ampla que o PDF (que é só 1 item); coerente com a reunião completa |
| Atores corretos (P1) | ✅ atores do sistema, não participantes |
| Sem ruído de gestão nos requisitos (P2) | ✅ movido para o anexo |
| Numeração/forma (P4) | ✅ RN contínuo, CSU |
| Concretude de UI | ❌ ausente (limitação de insumo — sem protótipo) |
| Fidelidade terminológica | ⚠️ "HIPOF" × "IPOF" (erro de transcrição do Agente 1) |

**Conclusão:** no núcleo funcional, os dois documentos identificaram os **mesmos pontos desejados e falados na
reunião**. As diferenças principais são: (a) o gerado tem escopo mais amplo (cobre toda a reunião, não só 1
item), e (b) o modelo deles tem detalhamento de tela (vindo de protótipos). As melhorias P1–P4 eliminaram os
problemas estruturais da v1 (persona-participante e ruído de gestão de projeto).

---

## 8. Próximos passos sugeridos (para o PFC2)

1. **P5 (estrutura interna de RF):** quando houver protótipo/print, organizar o Detalhamento nas subseções do
   modelo (MENU DE ACESSO, TÍTULO DA TELA, FILTROS, CAMPOS DA GRADE, BOTÕES, ORDENAÇÃO, PAGINAÇÃO).
2. **Glossário/normalização de termos:** corrigir "HIPOF" → "IPOF" (dicionário de termos do domínio aplicado
   pós-transcrição) e medir WER/CER do Agente 1.
3. **Métrica quantitativa:** calcular Precisão/Recall/F1 dos RF/RN/CSU do núcleo (item 2.1) usando o PR0102
   como *ground truth*, separando o escopo comparável (2.1) do escopo adicional (2.2–2.7).
