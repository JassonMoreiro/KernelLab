"""Analysis helpers for generated scheduling results."""


def recommendation(results: list[dict]) -> str:
    alarm = "P4"
    responses = {r["policy"]: r["metrics"][alarm]["response"]
                 for r in results if alarm in r["metrics"]}
    if not responses:
        return ("Recomendação indisponível: inclua o processo-alvo P4 para comparar "
                "a latência do alarme.")
    best_response = min(responses.values())
    best_policies = [policy for policy, response in responses.items()
                     if response == best_response]
    priority_response = responses.get("Prioridade")
    if priority_response is None:
        comparison = (f"não pode ser comparada porque não há resultado da política de Prioridade; "
                      f"{', '.join(best_policies)} obtém a menor resposta ({best_response} unidades)")
    elif priority_response == best_response:
        peers = [policy for policy in best_policies if policy != "Prioridade"]
        comparison = (f"empata na menor resposta para P4 ({best_response} unidades) "
                      f"com {', '.join(peers) or 'as demais políticas'}")
    else:
        comparison = (f"responde em {priority_response} unidades para P4; "
                      f"{', '.join(best_policies)} obtém a menor resposta "
                      f"({best_response} unidades)")
    return (f"Recomendação: a política de Prioridade não preemptiva {comparison}. "
            "A escolha por prioridade expressa melhor a criticidade clínica, não uma "
            "vantagem de latência neste conjunto. Monitore starvation e, em produção, "
            "avalie prioridade preemptiva com envelhecimento e validação de deadlines. "
            "O simulador não modela I/O bloqueante, deadlines nem múltiplas CPUs.")


def fairness_spread(result: dict) -> float:
    waits = [m["waiting"] for m in result["metrics"].values()]
    return max(waits) - min(waits) if waits else 0.0
