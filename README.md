# KernelLab

Simulador didático de escalonamento de CPU, substituição de páginas e acesso a dispositivos para o cenário MedControl. A aplicação compara quatro políticas de CPU, três algoritmos de páginas e uma matriz de permissões, com métricas reproduzíveis e testes automatizados.

## Requisitos

- Python 3.10 ou superior
- `pip`
- Windows, macOS ou Linux

## Instalação reproduzível

Clone o repositório e entre na pasta do projeto. Crie um ambiente virtual e instale a dependência usada apenas para gerar o PDF do relatório.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Executar

Windows:

```powershell
.\.venv\Scripts\python.exe src/main.py
```

macOS/Linux:

```bash
.venv/bin/python src/main.py
```

Para usar outra carga de trabalho, passe um arquivo JSON com a mesma estrutura de `data/processes.json`:

```powershell
.\.venv\Scripts\python.exe src/main.py --config caminho\para\processos.json
```

```bash
.venv/bin/python src/main.py --config caminho/para/processos.json
```

A execução imprime os diagramas de Gantt e métricas de cada política, a evolução dos frames por referência, page hits/faults, a matriz de acesso e a fila de contenção configurada.

## Testes

Execute na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Os testes cobrem a conclusão dos processos, o quantum do Round Robin, os algoritmos de substituição, permissões/fila e a recomendação do cenário. Não é preciso instalar dependências de teste.

## Relatório e pitch

O relatório técnico completo está em [docs/relatorio_tecnico.md](docs/relatorio_tecnico.md). Para regenerar o PDF após instalar `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe scripts/generate_report.py
```

```bash
.venv/bin/python scripts/generate_report.py
```

O arquivo gerado é `docs/relatorio_tecnico.pdf`. O roteiro de gravação com demonstração executável está em [docs/roteiro_video.md](docs/roteiro_video.md); o vídeo precisa ser gravado pela equipe e não é gerado pelo simulador.

## Estrutura

```text
data/processes.json          Carga de trabalho MedControl
src/models.py                Modelo e validação de processos
src/schedulers.py            FCFS, SJF, Round Robin, Prioridade e métricas
src/memory.py                FIFO, LRU e Optimal
src/devices.py               Matriz de permissões e contenção de dispositivos
src/metrics.py               Justiça e recomendação
src/main.py                  Interface de linha de comando
tests/test_algorithms.py     Testes automatizados
```

## Modelo e interpretação

O cenário representa monitoramento cardíaco (P1), telemetria (P2), relatórios (P3), alarme crítico (P4), backup (P5) e atualização (P6). Números de prioridade menores significam maior prioridade. Os parâmetros, incluindo quantum, frames e referências a páginas, estão em `data/processes.json`.

Os quatro escalonadores são de CPU única e não preemptivos, exceto Round Robin, que preempta ao fim do quantum. SJF significa Shortest Job First não preemptivo; Prioridade também é não preemptiva. A métrica de espera excessiva usa o limiar didático `max(10, 2 × burst)`. A amplitude de justiça é `maior espera − menor espera`; não representa uma medida universal de justiça.

FIFO, LRU e Optimal recebem a mesma sequência de referências e quantidade fixa de frames. Optimal usa referências futuras e serve somente como limite teórico. A memória do programa é uma abstração de paginação: não simula endereços virtuais, tabelas de páginas, TLB, disco de swap ou custo temporal de page fault.

O controle de dispositivos autoriza operações por processo a partir da lista `devices` e serializa solicitações em uma fila por dispositivo. A fila de contenção é uma simulação determinística em ordem FIFO; embora `request` use `Lock`, a demonstração não inicia threads concorrentes nem modela tempos de serviço. A matriz é uma allowlist simplificada, não substitui autenticação, auditoria ou controles de segurança de um sistema real.

## Resultado de referência

Com a carga fornecida e quantum 3, os tempos médios são:

| Política | Espera | Retorno | Resposta | Resposta P4 | Trocas |
| --- | ---: | ---: | ---: | ---: | ---: |
| FCFS | 13,67 | 20,50 | 13,67 | 18 | 5 |
| SJF | 10,67 | 17,50 | 10,67 | 5 | 5 |
| Round Robin | 18,00 | 24,83 | 5,33 | 6 | 13 |
| Prioridade | 10,67 | 17,50 | 10,67 | 5 | 5 |

Para quatro frames e 17 referências, FIFO resulta em 5 hits/12 faults, LRU em 7/10 e Optimal em 10/7. Esses números são um exemplo reproduzível da carga versionada, não uma conclusão universal sobre as políticas.

## Recomendação técnica

Limitações principais: uma CPU, processos CPU-bound, sem bloqueio por E/S nem custo de troca de contexto, prioridade estática não preemptiva, memória sem tradução de endereços ou tempo de falta de página e concorrência de dispositivos determinística. O projeto é apropriado para comparar conceitos, não para demonstrar garantias de tempo real ou segurança clínica.

