import unittest

from system_maps import cycles, dependency_counts, from_json, single_points_of_failure, summary, to_json

FIXTURE = '''{
  "nodes": [
    {"id":"supplier","type":"actor","label":"Supplier"},
    {"id":"plant","type":"actor","label":"Plant"},
    {"id":"grid","type":"resource","label":"Grid"},
    {"id":"market","type":"actor","label":"Market"}
  ],
  "edges": [
    {"source":"supplier","target":"plant","type":"flow"},
    {"source":"plant","target":"market","type":"flow"},
    {"source":"market","target":"supplier","type":"feedback"},
    {"source":"plant","target":"grid","type":"dependency"},
    {"source":"market","target":"grid","type":"dependency"}
  ]
}'''

class GraphContracts(unittest.TestCase):
    def test_json_round_trip_is_canonical(self):
        system = from_json(FIXTURE)
        encoded = to_json(system)
        self.assertEqual(encoded, to_json(from_json(encoded)))

    def test_cycle_detection_is_deterministic(self):
        system = from_json(FIXTURE)
        self.assertEqual(cycles(system), (("market", "supplier", "plant"),))
        self.assertEqual(cycles(system), cycles(system))

    def test_dependency_ranking_and_spof(self):
        system = from_json(FIXTURE)
        self.assertEqual(dependency_counts(system)[0], ("grid", 2))
        self.assertEqual(single_points_of_failure(system), ("grid",))

    def test_summary_is_interpretable_and_repeatable(self):
        system = from_json(FIXTURE)
        expected = "4 nodes, 5 edges; top dependency target=grid (2 incoming); cycles=1; single_points_of_failure=grid"
        self.assertEqual(summary(system), expected)
        self.assertEqual(summary(system), summary(system))

    def test_invalid_graph_fails_closed(self):
        cases = [
            '{}',
            '{"nodes":[],"edges":[]}',
            '{"nodes":[{"id":"a","type":"secret"}],"edges":[]}',
            '{"nodes":[{"id":"a","type":"actor"}],"edges":[{"source":"a","target":"missing","type":"flow"}]}',
            '{"nodes":[{"id":"a","type":"actor"},{"id":"a","type":"actor"}],"edges":[]}',
            '{"nodes":[{"id":"a","type":"actor"}],"edges":[],"x":NaN}'
        ]
        for text in cases:
            with self.assertRaises((ValueError, TypeError)):
                from_json(text)

if __name__ == "__main__":
    unittest.main()
