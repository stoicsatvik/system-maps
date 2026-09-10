import unittest

from system_maps import cycles, dependency_concentrations, dependency_counts, from_json, single_points_of_failure, summary, to_json

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

    def test_dependency_concentration_is_not_automatically_spof(self):
        system = from_json(FIXTURE)
        self.assertEqual(dependency_counts(system)[0], ("grid", 2))
        self.assertEqual(dependency_concentrations(system), ("grid",))
        self.assertEqual(single_points_of_failure(system), ())

    def test_removal_based_spof_detects_bridge_dependency(self):
        system = from_json('''{
          "nodes":[
            {"id":"service","type":"actor"},
            {"id":"gateway","type":"actor"},
            {"id":"database","type":"resource"},
            {"id":"backup","type":"resource"}
          ],
          "edges":[
            {"source":"service","target":"gateway","type":"dependency"},
            {"source":"gateway","target":"database","type":"dependency"},
            {"source":"backup","target":"gateway","type":"dependency"}
          ]
        }''')
        self.assertEqual(single_points_of_failure(system), ("gateway",))

    def test_alternate_dependency_path_prevents_false_positive(self):
        system = from_json('''{
          "nodes":[
            {"id":"a","type":"actor"},
            {"id":"b","type":"actor"},
            {"id":"hub","type":"resource"},
            {"id":"alt","type":"resource"},
            {"id":"sink","type":"resource"}
          ],
          "edges":[
            {"source":"a","target":"hub","type":"dependency"},
            {"source":"b","target":"hub","type":"dependency"},
            {"source":"hub","target":"sink","type":"dependency"},
            {"source":"a","target":"alt","type":"dependency"},
            {"source":"alt","target":"sink","type":"dependency"},
            {"source":"b","target":"alt","type":"dependency"}
          ]
        }''')
        self.assertEqual(dependency_concentrations(system), ("alt", "hub", "sink"))
        self.assertEqual(single_points_of_failure(system), ())

    def test_summary_is_interpretable_and_repeatable(self):
        system = from_json(FIXTURE)
        expected = "4 nodes, 5 edges; top dependency target=grid (2 incoming); cycles=1; dependency_concentrations=grid; single_points_of_failure=none"
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
