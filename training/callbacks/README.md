# Callback extension point

Future RLlib callbacks should live here. Keep them focused on metrics that are
already exposed through the environment `info` dictionary, such as velocity,
direction similarity, control cost, orientation cost, and health state.

Callbacks should not change rewards or environment dynamics.
