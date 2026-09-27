
import argparse
import json
from pathlib import Path
from models import Process
from schedulers import simulate_all
from memory import compare_pages
from devices import DeviceController
from metrics import recommendation, fairness_spread


ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    processes = [Process.from_dict(row) for row in data["processes"]]
    if len({p.pid for p in processes}) != len(processes):
        raise ValueError("Os identificadores dos processos devem ser únicos")
    return data, processes


def gantt(result):
    return " | ".join(f"{s.pid} [{s.start}-{s.end}]" for s in result["segments"])


def run(config_path: Path):
    data, processes = load_config(config_path)
    sched = simulate_all(processes, int(data.get("quantum", 3)))
    print("KERNELLAB — ESCALONAMENTO DA CPU")
    print(f"{'Política':<22} {'Espera média':>13} {'Retorno médio':>14} {'Resposta média':>15} {'Trocas':>8} {'Justiça (amplitude)':>21}")
    for r in sched:
        a = r["averages"]
        print(f"{r['policy']:<22} {a['waiting']:>13.2f} {a['turnaround']:>14.2f} {a['response']:>15.2f} {r['context_switches']:>8} {fairness_spread(r):>21.2f}")
        print("  Gantt:", gantt(r))
        print("  Métricas por processo:", json.dumps(r["metrics"], ensure_ascii=False))
        print("  Espera excessiva (limiar didático):", ", ".join(r["excessive_wait"]) or "nenhuma")
    print("\nMEMÓRIA —", data.get("frame_count", 4), "frames")
    page_results = compare_pages(data.get("page_references", []), int(data.get("frame_count", 4)))
    for r in page_results:
        print(f"{r['algorithm']}: hits={r['hits']} faults={r['faults']} taxa={r['fault_rate']:.1%}")
        print("  ref | frames | resultado")
        for step in r["history"]:
            print(f"  {step['reference']:>3} | {str(step['frames']):<22} | {'hit' if step['hit'] else 'fault'}")
    print("\nDISPOSITIVOS — matriz de permissões (ler/gravar/executar/utilizar/exclusivo)")
    controller = DeviceController(processes)
    for pid, devices in controller.access_matrix().items():
        allowed = [d for d, rights in devices.items() if rights["utilizar"]]
        print(f"  {pid}: {', '.join(allowed) or 'sem dispositivos autorizados'}")
    target = data.get("contention_device", "disco")
    contenders = data.get("contention_processes", [p.pid for p in processes])
    print(f"Fila concorrente ({target}):", json.dumps(controller.simulate_contention(target, contenders), ensure_ascii=False))
    print("\n", recommendation(sched))


def main():
    parser = argparse.ArgumentParser(description="Simulador educacional de escalonamento, memória e dispositivos")
    parser.add_argument("--config", type=Path, default=ROOT / "data" / "processes.json", help="Arquivo JSON de configuração")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
