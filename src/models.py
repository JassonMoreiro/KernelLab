from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Process:
    pid: str
    name: str
    arrival: int
    burst: int
    priority: int
    memory_mb: int
    devices: tuple[str, ...]

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "Process":
        required = ("pid", "name", "arrival", "burst", "priority", "memory_mb", "devices")
        missing = [key for key in required if key not in row]
        if missing:
            raise ValueError(f"Processo sem campos obrigatórios: {', '.join(missing)}")
        values = {key: row[key] for key in required}
        for key in ("arrival", "burst", "priority", "memory_mb"):
            if isinstance(values[key], bool) or not isinstance(values[key], int):
                raise ValueError(f"{row.get('pid', '?')}: {key} deve ser inteiro")
        if values["arrival"] < 0 or values["burst"] <= 0 or values["memory_mb"] < 0:
            raise ValueError(f"{row['pid']}: chegada/memória devem ser não negativas e burst positivo")
        devices = values["devices"]
        if isinstance(devices, str):
            devices = [devices]
        if not isinstance(devices, list) or any(not isinstance(d, str) for d in devices):
            raise ValueError(f"{row['pid']}: devices deve ser uma lista de nomes")
        return cls(values["pid"], values["name"], values["arrival"], values["burst"],
                   values["priority"], values["memory_mb"], tuple(devices))


@dataclass(frozen=True)
class Segment:
    pid: str
    start: int
    end: int

