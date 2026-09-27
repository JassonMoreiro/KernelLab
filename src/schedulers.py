from collections import deque
from typing import Iterable
from models import Process, Segment


def _append(segments: list[Segment], pid: str, start: int, end: int) -> None:
    if end <= start:
        return
    if segments and segments[-1].pid == pid and segments[-1].end == start:
        last = segments[-1]
        segments[-1] = Segment(pid, last.start, end)
    else:
        segments.append(Segment(pid, start, end))


def _result(processes: list[Process], segments: list[Segment], policy: str) -> dict:
    by_id = {p.pid: p for p in processes}
    first, finish = {}, {}
    for s in segments:
        if s.pid != "IDLE":
            first.setdefault(s.pid, s.start)
            finish[s.pid] = s.end
    rows = {}
    for p in processes:
        end = finish[p.pid]
        response = first[p.pid] - p.arrival
        turnaround = end - p.arrival
        rows[p.pid] = {"waiting": turnaround - p.burst, "turnaround": turnaround,
                       "response": response, "completion": end}
    n = len(processes) or 1
    averages = {key: sum(row[key] for row in rows.values()) / n
                for key in ("waiting", "turnaround", "response")}
    switches = sum(1 for a, b in zip(segments, segments[1:]) if a.pid != b.pid and a.pid != "IDLE" and b.pid != "IDLE")
    execution_order = [s.pid for s in segments if s.pid != "IDLE"]
    # Response-delay flag is deliberately explicit and configurable for analysis.
    excessive = [pid for pid, row in rows.items() if row["waiting"] >= max(10, 2 * by_id[pid].burst)]
    return {"policy": policy, "segments": segments, "metrics": rows, "averages": averages,
            "context_switches": switches, "execution_order": execution_order,
            "excessive_wait": excessive}


def _nonpreemptive(processes: Iterable[Process], policy: str) -> dict:
    ps = list(processes)
    remaining = {p.pid: p for p in ps}
    ready, now, seg = [], 0, []
    while remaining:
        ready.extend(p for p in list(remaining.values()) if p.arrival <= now and p not in ready)
        if not ready:
            next_time = min(p.arrival for p in remaining.values())
            _append(seg, "IDLE", now, next_time)
            now = next_time
            continue
        if policy == "FCFS":
            p = min(ready, key=lambda x: (x.arrival, ps.index(x)))
        elif policy == "SJF":
            p = min(ready, key=lambda x: (x.burst, x.arrival, ps.index(x)))
        else:
            p = min(ready, key=lambda x: (x.priority, x.arrival, ps.index(x)))
        ready.remove(p)
        _append(seg, p.pid, now, now + p.burst)
        now += p.burst
        del remaining[p.pid]
    return _result(ps, seg, policy)


def fcfs(processes: Iterable[Process]) -> dict:
    return _nonpreemptive(processes, "FCFS")


def sjf(processes: Iterable[Process]) -> dict:
    return _nonpreemptive(processes, "SJF")


def priority(processes: Iterable[Process]) -> dict:
    return _nonpreemptive(processes, "Prioridade")


def round_robin(processes: Iterable[Process], quantum: int = 3) -> dict:
    if quantum <= 0:
        raise ValueError("O quantum deve ser maior que zero")
    ps = list(processes)
    pending = sorted(ps, key=lambda p: (p.arrival, ps.index(p)))
    rem = {p.pid: p.burst for p in ps}
    q, now, i, seg = deque(), 0, 0, []
    while q or i < len(pending):
        if not q and i < len(pending) and now < pending[i].arrival:
            _append(seg, "IDLE", now, pending[i].arrival)
            now = pending[i].arrival
        while i < len(pending) and pending[i].arrival <= now:
            q.append(pending[i]); i += 1
        p = q.popleft()
        run = min(quantum, rem[p.pid])
        _append(seg, p.pid, now, now + run)
        now += run
        rem[p.pid] -= run
        while i < len(pending) and pending[i].arrival <= now:
            q.append(pending[i]); i += 1
        if rem[p.pid] > 0:
            q.append(p)
    return _result(ps, seg, f"Round Robin (q={quantum})")


def simulate_all(processes: Iterable[Process], quantum: int = 3) -> list[dict]:
    ps = list(processes)
    return [fcfs(ps), sjf(ps), round_robin(ps, quantum), priority(ps)]
