# Dados a coletar para o artigo

Rodar o pipeline na reunião do SGG-GO e anotar os valores abaixo.
Todos os itens vão para a Section 3.4 (Case Study) do main.tex.

## Coletar rodando o pipeline

- [ ] Tempo total do pipeline do início ao fim (do áudio ao PDF)
- [ ] Número de chunks em que o áudio foi dividido (está nos logs do Agent 1)
- [ ] Número de palavras da transcrição gerada — rodar `wc -w` no .txt de saída
- [ ] Número de personas identificadas pelo Agent 2 (contar no JSON)
- [ ] Número de user stories geradas pelo Agent 2 (contar no JSON)
- [ ] Número de requisitos funcionais no documento final (contar no PDF/MD)
- [ ] Número de páginas do documento final
- [ ] Custo total de API — ver na dashboard da Anthropic (tokens Haiku + Sonnet)

## Para a Section 4 (Evaluation) — deixar para depois

- [ ] WER/CER do Agent 1: precisa transcrever manualmente um trecho da reunião como gold standard
- [ ] Precisão/Recall/F1 do Agent 2: precisa anotar manualmente quais personas e stories estão corretas
- [ ] Survey de satisfação com a equipe do SGG-GO (RQ3)
- [ ] Comparação sistemática do documento gerado vs. documento oficial do SGG-GO (RQ4)
- [ ] Quantificar propagação de erros — expandir o exemplo HIPOF/IPOF com mais casos (RQ5)
