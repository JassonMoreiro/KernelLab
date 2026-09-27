import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from models import Process
from schedulers import fcfs, sjf, round_robin, priority, simulate_all
from memory import simulate_pages
from devices import DeviceController
from main import load_config, ROOT
from metrics import recommendation


class KernelLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.ps = load_config(ROOT / "data" / "processes.json")

    def test_scheduler_finishes_all_processes(self):
        for result in (fcfs(self.ps), sjf(self.ps), round_robin(self.ps, 3), priority(self.ps)):
            self.assertEqual(set(result["metrics"]), {p.pid for p in self.ps})
            self.assertTrue(all(v["turnaround"] >= p.burst for p in self.ps for v in [result["metrics"][p.pid]]))

    def test_rr_quantum_validation(self):
        with self.assertRaises(ValueError):
            round_robin(self.ps, 0)

    def test_page_algorithms_consistent(self):
        refs = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5, 2, 1, 5, 3, 2]
        results = [simulate_pages(refs, 4, a) for a in ("FIFO", "LRU", "OPTIMAL")]
        self.assertTrue(all(r["hits"] + r["faults"] == len(refs) for r in results))
        self.assertLessEqual(results[2]["faults"], results[0]["faults"])

    def test_access_control_and_queue(self):
        c = DeviceController(self.ps)
        self.assertEqual(c.request("P4", "audio")["status"], "concedido")
        self.assertEqual(c.request("P5", "audio")["status"], "negado")
        self.assertEqual([x["pid"] for x in c.simulate_contention("disco", ["P3", "P5", "P6"])], ["P3", "P5", "P6"])

    def test_recommendation_reports_measured_tie(self):
        result = recommendation(simulate_all(self.ps, 3))
        self.assertIn("empata na menor resposta para P4 (5 unidades)", result)
        self.assertIn("não uma vantagem de latência", result)


if __name__ == "__main__":
    unittest.main()
