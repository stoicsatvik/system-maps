# Foundry State

## Objective
Build a generic toolkit for mapping complex systems as typed graphs of actors, resources, flows, dependencies, feedback loops, and control points.

## Public boundary
Visualization and generic graph-analysis primitives only. Do not publish proprietary power-ranking heuristics, private market intelligence, or confidential ecosystem data.

## V0 milestone
- Typed node/edge schema for actors, resources, flows, dependencies, and feedback
- Import/export via JSON
- Detect cycles, central dependencies, and single points of failure
- Generate an interpretable system summary
- Deterministic examples and tests

## Acceptance
A stranger can describe a small ecosystem in JSON and obtain a reproducible map plus basic structural-risk analysis without depending on a hosted service.

## Next move
Implement the schema/parser and cycle/dependency analysis before graphical rendering.

Status: ACTIVE / NOT YET PROVEN
