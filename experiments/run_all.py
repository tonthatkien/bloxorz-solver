"""Chạy mọi solver trên mọi màn trong levels/, ghi CSV vào experiments/results/. TODO [F7-F8].

Gợi ý khung:
    for path in sorted(glob("levels/*.json")):
        game = Game(load_level(path))
        for name, solver in SOLVERS.items():
            res = run_measured(solver.solve, game)
            # ghi: level, solver, solved, length, cost, expanded_nodes, time_sec, peak_memory_kb, note
"""
