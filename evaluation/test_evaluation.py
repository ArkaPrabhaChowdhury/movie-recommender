import json
import unittest
from pathlib import Path

from run_evaluation import expand_dataset, ndcg_at_k, precision_at_k


class EvaluationSmokeTest(unittest.TestCase):
    def test_case_matrix_has_at_least_thirty_cases(self):
        templates = json.loads((Path(__file__).parent / "dataset.json").read_text(encoding="utf-8"))
        self.assertEqual(len(expand_dataset(templates)), 36)

    def test_ranking_metrics_are_bounded(self):
        self.assertEqual(precision_at_k([1, 2, 3], {1, 3}, 3), 2 / 3)
        self.assertGreaterEqual(ndcg_at_k([1, 2, 3], {1, 3}, 3), 0)
        self.assertLessEqual(ndcg_at_k([1, 2, 3], {1, 3}, 3), 1)


if __name__ == "__main__":
    unittest.main()
