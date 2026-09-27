def simulate_pages(references: list[int], frame_count: int, algorithm: str) -> dict:
    if frame_count <= 0:
        raise ValueError("A quantidade de frames deve ser positiva")
    algo = algorithm.upper()
    if algo not in {"FIFO", "LRU", "OPTIMAL"}:
        raise ValueError("Algoritmo deve ser FIFO, LRU ou Optimal")
    frames: list[int | None] = [None] * frame_count
    fifo_order: list[int] = []
    last_used: dict[int, int] = {}
    hits = faults = 0
    history = []
    for i, page in enumerate(references):
        hit = page in frames
        if hit:
            hits += 1
        else:
            faults += 1
            if None in frames:
                slot = frames.index(None)
            elif algo == "FIFO":
                victim = fifo_order.pop(0); slot = frames.index(victim)
            elif algo == "LRU":
                victim = min(frames, key=lambda x: last_used[x]); slot = frames.index(victim)
            else:
                future = references[i + 1:]
                distances = {p: (future.index(p) if p in future else float("inf")) for p in frames}
                victim = max(frames, key=lambda x: distances[x]); slot = frames.index(victim)
            evicted = frames[slot]
            frames[slot] = page
            if algo == "FIFO":
                if evicted is not None and evicted in fifo_order:
                    fifo_order.remove(evicted)
                fifo_order.append(page)
        if algo == "FIFO" and hit is False and page not in fifo_order:
            fifo_order.append(page)
        last_used[page] = i
        history.append({"reference": page, "frames": list(frames), "hit": hit})
    total = len(references)
    return {"algorithm": "Optimal" if algo == "OPTIMAL" else algo, "history": history,
            "hits": hits, "faults": faults, "fault_rate": faults / total if total else 0.0}


def compare_pages(references: list[int], frame_count: int) -> list[dict]:
    return [simulate_pages(references, frame_count, a) for a in ("FIFO", "LRU", "OPTIMAL")]
