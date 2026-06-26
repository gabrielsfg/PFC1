# Análise comparativa — Documento gerado vs. Documento modelo (PR0102)

> Comparação entre o **documento de requisitos gerado pelo pipeline** (a partir do áudio da reunião
> *"Detalhamento de escopo e levantamento — Alteração no controle de saldo orçamentário"*) e o
> **documento oficial enviado pela SGG-GO** (`PR0102 – Secretaria da Economia – Evolução IPOF-LOA-Empenho –
> Alteração do Saldo Orçamentário`, sistema IPOF/MGS 2.0.1).
>
> Duplo objetivo: (1) servir de base para a **escrita do TCC** (análise crítica de precisão/recall);
> (2) orientar a **melhoria dos prompts** para aproximar a saída do documento-modelo.

---

## 1. Contexto essencial (não comparar maçã com laranja)

| | Documento modelo (PR0102) | Documento gerado |
|---|---|---|
| Origem | Escrito por analista humano (André Dias Ramos) | Gerado por IA a partir de 1 transcrição |
| Insumos | Sistema real (SIAFIC/SIOFI) + **protótipos no Figma** + várias reuniões | Apenas o áudio de **uma** reunião de levantamento |
| Estágio | Documento **final e polido** | **Elicitação crua** (estágio anterior) |
| Modelo LLM | — | `claude-haiku-4-5` (modelo econômico) |

**Implicação:** parte das diferenças é estrutural e esperada (o áudio não tem telas/protótipos).
A análise abaixo separa o que é *limitação justa* do que é *falha corrigível via prompt*.

---

## 2. Números (volume)

| Seção | PR0102 (modelo) | Gerado | Observação |
|---|---|---|---|
| Requisitos Funcionais (RF) | 5 | 16 | super-geração |
| Regras de Negócio (RN) | 3 | 27 (9 grupos × 3) | super-geração |
| Casos de Uso (CSU/UC) | 3 | 26 | super-geração |
| Requisitos Não-Funcionais (RNF) | 0 | 21 | modelo não usa RNF |
| Personas/atores | "Usuário do sistema" (1 ator) | 10 personas | conceito divergente |

---

## 3. O que a IA ACERTOU (forte)

- **Domínio/tema: excelente.** Capturou com precisão o assunto: controle de **saldo orçamentário** no
  **IPOF**, com **granularidade por ação orçamentária + grupo de despesa + fonte de recurso**; menções a
  **DAOF**, **POF**, **exercício futuro**, **"exibir saldo zerado"**, **nova tela de consulta para os órgãos**.
- **RFs centrais convergem** com o modelo:
  - Granularidade expandida de controle (modelo RF1 / gerado RF1)
  - Nova tela/consulta de saldo para órgãos (modelo menu "Consultar saldo orçamentário" / gerado RF8)
  - Validação de cobertura orçamentária (gerado RF2–RF6)
  - Tratamento de exercício futuro sem programa de trabalho (gerado RF7)
  - Alteração de serviços POF / novo serviço de saldo (gerado RF9, RF10)
- **Estrutura do formato empresa** fiel: Funcionalidade → RF (Detalhamento/Comentários) → RN em tabela →
  Casos de Uso → RNF.

➡️ **Recall do domínio alto:** a IA "ouviu" a reunião e extraiu corretamente o núcleo funcional, incluindo
itens que estão no documento oficial.

---

## 4. Onde DIVERGIU (e a causa raiz no prompt)

### 4.1 "Persona" = participante da reunião, não usuário do sistema  ⟵ divergência mais importante
- **Gerado:** 10 personas = a **equipe do projeto** (Bruno/analista de negócio, André/TI, Lívia/PM,
  Zé Lucas/dev sênior, Débora/prototipadora UX, etc.).
- **Modelo:** o **único ator** de todos os casos de uso é *"Usuário do sistema"* (operador de orçamento no órgão).
- **Causa raiz** — `agente-identificacao/config/prompts.py`:
  - `SYSTEM_MESSAGE`: *"identificação de personas... quem são os participantes (personas)"*
  - `PERSONA_IDENTIFICATION_PROMPT`: *"identifique todas as personas (participantes) envolvidos na conversa"*
  - → O prompt pede **participantes da conversa**, então a IA devolve os interlocutores — não os **atores do
    sistema** que o software vai atender.

### 4.2 Super-geração + mistura de requisito de produto com discussão de gestão de projeto
- RF11–RF16 e ~metade das RN são **processo de projeto**, não requisito de software:
  "Priorizar itens do escopo", "Criar EAP", "Negociar prazos", "Agendar reunião de validação de protótipos",
  "Compartilhar conhecimento de arquitetura", "Mapear métodos do código".
- O analista humano **filtrou** isso; a IA tratou tudo como requisito.
- **Causa raiz:** `USER_STORIES_PROMPT` cria histórias para **cada persona** (inclusive PM, dev sênior,
  prototipadora), e `EMPRESA_FUNCTIONAL_REQUIREMENTS_PROMPT` converte **todas** as histórias em RF, sem
  distinguir "comportamento do sistema" de "atividade do projeto/equipe".

### 4.3 Falta de concretude de UI (limitação justa)
- Modelo: especifica tela, menu (`>> Planejamento e Execução Orçamentária >> IPOF >> Manutenção de Saldo
  Orçamentário`), filtros campo a campo, colunas da grade, botões, paginação, pop-up "Editar saldo orçamentário".
- Gerado: fica conceitual ("o sistema deve validar...").
- **Justo:** essa concretude vem de prints/protótipos ausentes no áudio. Não é falha de prompt — é limitação
  de insumo. (Mitigável no futuro permitindo anexar prints/protótipos como entrada multimodal.)

### 4.4 Detalhes de forma
- Modelo numera **RN1, RN2, RN3** de forma contínua; gerado **reinicia RN01 por grupo** → IDs repetidos
  (vários "RN01"). Ajuste de numeração global recomendado.
- Modelo usa **CSU**; gerado usa **UC**. Trivial, mas para ficar idêntico ao modelo pode-se renomear.
- Modelo nomeia RF por **ação na tela** ("Consultar parâmetros..."); gerado nomeia por **capacidade**
  ("Validação de saldo em envio de IPOF").

---

## 5. Recomendações de melhoria de prompt (acionável)

### P1 — Separar "ator do sistema" de "participante da reunião"  (resolve 4.1)
No `agente-identificacao`, **distinguir dois conceitos** no output:
- `participantes_reuniao`: quem falou (atual comportamento — útil como metadado/rastreabilidade).
- `personas_sistema` / `atores`: os **usuários/atores do software** inferidos do que está sendo construído
  (no caso, "Usuário do sistema / Operador de orçamento do órgão", "Equipe central de orçamento").

Sugestão de texto a adicionar ao `PERSONA_IDENTIFICATION_PROMPT`:
> "Distinga DOIS grupos: (a) **participantes da reunião** (interlocutores), e (b) **atores do sistema** —
> os perfis de usuário que efetivamente USARÃO o software discutido (ex.: operador, gestor, consultor),
> inferidos a partir das funcionalidades descritas, mesmo que não estejam presentes na conversa.
> Os casos de uso e requisitos devem ser escritos do ponto de vista dos **atores do sistema**, não dos participantes."

➡️ Os casos de uso do `agente-srs` devem então usar **atores do sistema** como `actor`, não o nome do participante.

### P2 — Filtrar requisito de produto vs. discussão de projeto  (resolve 4.2)
Adicionar regra explícita ao `EMPRESA_FUNCTIONAL_REQUIREMENTS_PROMPT` (e ao de histórias):
> "Inclua APENAS requisitos de **comportamento do software** (o que o sistema deve fazer).
> EXCLUA discussões de gestão de projeto e atividades de equipe: priorização de escopo, EAP, cronograma,
> negociação de prazos, alocação de pessoas, reuniões de validação, mapeamento de código, transferência de
> conhecimento. Se um item descreve uma atividade humana de processo (não um comportamento do sistema), não o
> liste como requisito funcional."

➡️ Opcional: capturar esses itens de processo numa seção à parte ("Decisões e ações do projeto"), fora dos RF.

### P3 — Reduzir super-geração / consolidar  (resolve volume)
- Pedir **consolidação**: "Agrupe requisitos redundantes; priorize de 5 a 10 RF macro que cubram o núcleo
  funcional, evitando fragmentar uma mesma capacidade em vários RF."
- O modelo PR0102 tem 5 RF densos; mirar densidade > quantidade.

### P4 — Numeração e nomenclatura fiéis ao modelo  (resolve 4.4)
- **RN global e contínua** (RN1, RN2, ...) em vez de reiniciar por grupo. Ajustar `BUSINESS_RULES_PROMPT`
  e/ou pós-processar no `feature_generator.py`.
- Considerar renomear "UC" → "CSU" no template empresa para igualar o modelo.
- Nome de RF orientado à **tela/ação** quando o contexto permitir.

### P5 — Aproximar a estrutura interna de cada RF do modelo
O modelo detalha cada RF com subseções padronizadas: **MENU DE ACESSO**, **TÍTULO DA TELA**, **FILTROS**,
**CAMPOS DA GRADE**, **BOTÕES DE AÇÃO**, **ORDENAÇÃO**, **PAGINAÇÃO**. Quando houver protótipo/print no futuro,
pedir ao LLM que organize o Detalhamento nessas subseções. Sem protótipo, manter Detalhamento livre (atual).

### P6 — RNF (decisão de escopo)
O modelo PR0102 **não tem** RNF. Para comparação fiel, avaliar **tornar a seção RNF opcional** no formato
empresa (flag), ou mantê-la como valor agregado do pipeline (decisão do TCC: documentar a escolha).

---

## 6. Síntese para o TCC

- **Ponto forte mensurável (recall de domínio):** a IA extraiu corretamente o tema e os requisitos funcionais
  centrais a partir de áudio puro, convergindo com o documento oficial em vários itens.
- **Pontos fracos mensuráveis (precisão/escopo):**
  1. confusão **persona-participante × ator-do-sistema**;
  2. **ruído de gestão de projeto** misturado aos requisitos (super-geração);
  3. ausência de concretude de UI (limitação de insumo, não de modelo).
- **Contribuição proposta no PFC2:** introduzir no pipeline um **passo de classificação/filtragem** que
  (a) separe ator-do-sistema de participante e (b) distinga requisito-de-produto de discussão-de-processo —
  além de **consolidação** para reduzir super-geração. Métricas: Precisão/Recall/F1 dos RF/RN/UC gerados
  contra o documento oficial PR0102 como *ground truth*.

---

## 7. Tabela de rastreabilidade (convergência item a item)

| Tema | PR0102 (modelo) | Gerado | Convergiu? |
|---|---|---|---|
| Granularidade (ação/grupo/fonte) | RF1 (filtros e colunas) | RF1 | ✅ |
| Exibir saldo zerado | RF1 | UC004 (passo) | ✅ parcial |
| Nova consulta de saldo p/ órgãos | menu "Consultar saldo" | RF8 | ✅ |
| Validação de cobertura | implícito nas regras | RF2–RF6 | ✅ (gerado mais explícito) |
| Exercício futuro s/ prog. trabalho | — (não detalhado) | RF7, RF13 | ➕ gerado capturou da fala |
| Serviços POF / saldo | — | RF9, RF10 | ➕ gerado capturou da fala |
| Especificação de tela/menu/grade | RF1–RF5 (muito detalhado) | — | ❌ falta concretude UI |
| Ator dos casos de uso | "Usuário do sistema" | participantes (Bruno, etc.) | ❌ conceito trocado |
| Gestão de projeto (EAP, prazos) | não consta | RF11–RF16, várias RN | ❌ ruído (deveria filtrar) |
