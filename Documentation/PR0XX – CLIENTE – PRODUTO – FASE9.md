# PR0XX – CLIENTE – PRODUTO – FASE99

## Documento de Requisitos

**Versão:** 20`<XX>`

---

> **:information_source: Nota sobre este template:** O texto entre `< >` em itálico é fornecido para orientar o autor e deve ser removido antes de publicar o documento. Substitua os placeholders pelo conteúdo real da funcionalidade.

---

## Controle de Versão do Documento

> **:information_source: Instrução:** Neste item devem ser documentadas todas as revisões e alterações. O campo "Versão" deve ser alterado somente após aprovação formal do documento.

| Data | Versão | Descrição | Autor(es) |
|------|--------|-----------|-----------|
| dd/mm/aaaa | 1.0.0 |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

---

## Funcionalidade: `<Nome da Funcionalidade>`

> **:information_source: Instrução:** Coloque nesta seção a descrição da funcionalidade. Exemplo: _"Essa funcionalidade tem por objetivo..."_
>
> Este modelo descritivo também servirá para a modelagem de dados.

`<Descrição da funcionalidade>`

---

### Requisitos Funcionais

> **:information_source: Instrução:** Descrição dos requisitos funcionais que compõem a funcionalidade. Os requisitos funcionais são agrupados por funcionalidade.
>
> Descreva o requisito funcional de forma macro, relatando a funcionalidade específica. O analista de requisitos verifica quais informações são necessárias para descrever a funcionalidade de forma clara e resumida.
>
> Fica a critério do analista usar a formatação com os subtítulos **Detalhamento** e **Comentários**.
>
> Caso o analista de requisitos em conjunto com o UX já tenha um esboço da tela, é permitido incluir imagem ou link.
>
> **Exemplo:**
>
> - **RF1 – Consultar IPOF**
>   - **Detalhamento:** Esta funcionalidade permite consultar uma IPOF, listando por determinados filtros e exibindo as informações.
>   - **Comentários:** Deve haver validação de quem pode acessar as informações. Através da lista deve ser possível acessar a consulta detalhada, padrão SGG-GO.

---

#### RF`<N>` – `<NOME_REQUISITO>`

**Tela:** `<link e/ou imagem da tela>`

**Detalhamento:**

`<Descrição detalhada do requisito funcional>`

**Comentários:**

`<Observações, restrições ou comentários relevantes>`

---

#### RF`<N>` – `<NOME_REQUISITO>`

**Tela:** `<link ou imagem da tela>`

**Detalhamento:**

`<Descrição detalhada do requisito funcional>`

**Comentários:**

`<Observações, restrições ou comentários relevantes>`

---

#### RF`<N>` – `<NOME_REQUISITO>`

**Tela:** `<link ou imagem da tela>`

**Detalhamento:**

`<Descrição detalhada do requisito funcional>`

**Comentários:**

`<Observações, restrições ou comentários relevantes>`

---

### Regras de Negócio

> **:information_source: Instrução:** Para atender a funcionalidade, detalhe nesta seção as regras de negócio. As regras devem ser descritas da forma mais clara possível, apresentando todas as informações necessárias.
>
> Pode ser útil organizar as Regras de Negócio em grupos para melhorar a leitura. Além das regras de negócio, pode-se listar e detalhar regras para a implementação de interface (regras de interface).
>
> **Exemplos de regras de interface:**
>
> - É permitida a seleção de vários itens para pesquisa;
> - Quando o cursor está posicionado sobre o campo, é exibida a mensagem de ajuda `<informar a mensagem>`;
> - Quando o cursor está posicionado sobre a opção/botão, é exibida mensagem de ajuda `<informar a mensagem>`;
> - Campo sem possibilidade de edição;
> - É permitida a seleção de apenas um único item para a pesquisa;
> - A lista é ordenada de forma ascendente pelo campo `<nome do campo>`.
>
> **Observação:** Regras de interface que não foram definidas pelo cliente devem seguir o descrito no Design System: _03 - GESI..._

---

#### `<CONTEXTO_REGRA_NEGÓCIO>`

| ID | Regra de Negócio | Detalhamento |
|----|------------------|--------------|
| RN01 | `<Nome da Regra>` | `<Descrição>` |
| RN02 | `<Nome da Regra>` | `<Descrição>` |
| RN03 | `<Nome da Regra>` | `<Descrição>` |

---

#### `<CONTEXTO_REGRA_NEGÓCIO>`

| ID | Regra de Negócio | Detalhamento |
|----|------------------|--------------|
| RN01 | `<Nome da Regra>` | `<Descrição>` |
| RN02 | `<Nome da Regra>` | `<Descrição>` |

---

#### `<CONTEXTO_REGRA_NEGÓCIO>`

| ID | Regra de Negócio | Detalhamento |
|----|------------------|--------------|
| RN01 | `<Nome da Regra>` | `<Descrição>` |
| RN02 | `<Nome da Regra>` | `<Descrição>` |

---

### Casos de Uso

> **:information_source: Instrução:** Caso a funcionalidade mapeada seja composta de outras funcionalidades, o analista tem liberdade para criar vários casos de uso. A técnica de casos de uso com inclusão e extensão pode ser utilizada.
>
> - **Fluxo Principal – FP `<Título>`:** Mostra a interação entre ator e sistema, apresentando o fluxo principal de execução da funcionalidade.
> - **FA`<número>` – `<Título>`:** Mostra situações de desvio do caminho definido pelo fluxo principal. Cada fluxo alternativo retorna ao fluxo principal ou encerra o caso de uso.
> - **FE`<número>`:** Mostra o fluxo de exceção caso ocorra alguma atividade não prevista. Geralmente são erros ou situações de exceção do sistema.
>
> **Nota:** Na descrição do fluxo de eventos devem constar todas as especificações das regras de negócio executadas.
>
> **Nota:** A numeração dos casos de uso segue o padrão de identificação dos casos de uso, e a numeração dos fluxos alternativos e de exceção é reiniciada a cada caso de uso.

---

#### UC`<N>` – `<NOME_CASO_DE_USO>`

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | `<Descreva o objetivo do caso de uso>` |
| **Ator** | `<Nome do ator principal>` |
| **Pré-condições** | `<Condições necessárias para iniciar o caso de uso>` |
| **Pós-condições** | `<Estado do sistema após a execução bem-sucedida>` |

**Fluxo Principal – FP `<Título do Fluxo>`**

1. Passo 1
2. Passo 2
3. ...
4. Fim do caso de uso.

**Fluxo Alternativo – FA001 `<Título do Fluxo>`**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

**Fluxo Alternativo – FA002**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

**Fluxo Exceção – FE001**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

**Fluxo Exceção – FE002**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

---

#### UC`<N>` – `<NOME_CASO_DE_USO>`

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | `<Descreva o objetivo do caso de uso>` |
| **Ator** | `<Nome do ator principal>` |
| **Pré-condições** | `<Condições necessárias para iniciar o caso de uso>` |
| **Pós-condições** | `<Estado do sistema após a execução bem-sucedida>` |

**Fluxo Principal – FP `<Título do Fluxo>`**

1. Passo 1
2. Passo 2
3. ...
4. Fim do caso de uso.

**Fluxo Alternativo – FA001 `<Título do Fluxo>`**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

**Fluxo Alternativo – FA002**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

**Fluxo Exceção – FE001**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

**Fluxo Exceção – FE002**

Se no passo `<número do passo>` do `<nome do fluxo>`, o ator `<informar a condição para o desvio>` então:

1. Passo 1
2. Passo 2
3. ...

---

### Requisitos Não-Funcionais

#### RNF`<N>` – `<NOME_REQUISITO_NÃO-FUNCIONAL>`

| Campo | Descrição |
|-------|-----------|
| **Categoria** | `<Desempenho / Segurança / Usabilidade / Disponibilidade / etc.>` |
| **Descrição** | `<Descrição do requisito não-funcional>` |
| **Critério de Aceitação** | `<Como será validado>` |

---