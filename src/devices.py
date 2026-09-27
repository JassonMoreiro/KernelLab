from collections import deque
from threading import Lock

DEVICES = ("disco", "rede", "audio", "logs")


class DeviceController:
    def __init__(self, processes):
        self.allowed = {p.pid: set(p.devices) for p in processes}
        self.permissions = {}
        for pid, devices in self.allowed.items():
            self.permissions[pid] = {d: {"ler": d in devices, "gravar": d in devices,
                "executar": False, "utilizar": d in devices, "exclusivo": d in devices}
                for d in DEVICES}
        self._locks = {d: Lock() for d in DEVICES}
        self._queues = {d: deque() for d in DEVICES}

    def access_matrix(self):
        return self.permissions

    def request(self, pid: str, device: str, action: str = "utilizar") -> dict:
        if device not in DEVICES:
            raise ValueError(f"Dispositivo desconhecido: {device}")
        if pid not in self.permissions or not self.permissions[pid][device].get(action, False):
            return {"pid": pid, "device": device, "action": action, "status": "negado"}
        queue = self._queues[device]
        queue.append(pid)
        # The lock models mutual exclusion. Requests are processed in FIFO order.
        with self._locks[device]:
            owner = queue.popleft()
            return {"pid": owner, "device": device, "action": action, "status": "concedido"}

    def simulate_contention(self, device: str, pids: list[str]) -> list[dict]:
        if device not in DEVICES:
            raise ValueError(f"Dispositivo desconhecido: {device}")
        # Enqueue in arrival order before serving, making queue behavior observable.
        self._queues[device].extend(pids)
        result = []
        while self._queues[device]:
            pid = self._queues[device][0]
            if pid not in self.permissions or not self.permissions[pid][device]["utilizar"]:
                self._queues[device].popleft()
                result.append({"pid": pid, "device": device, "status": "negado"})
                continue
            with self._locks[device]:
                self._queues[device].popleft()
                result.append({"pid": pid, "device": device, "status": "concedido"})
        return result
