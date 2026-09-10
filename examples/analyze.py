from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from system_maps import cycles, dependency_counts, from_json, single_points_of_failure, summary, to_json

fixture = Path(__file__).with_name("ecosystem.json")
system = from_json(fixture.read_text(encoding="utf-8"))

print(to_json(system), end="")
print(summary(system))
print("dependency_ranking=" + ",".join(f"{node}:{count}" for node, count in dependency_counts(system)))
print("cycles=" + repr(cycles(system)))
print("single_points_of_failure=" + (",".join(single_points_of_failure(system)) or "none"))
