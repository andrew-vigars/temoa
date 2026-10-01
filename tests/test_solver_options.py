from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pyomo.environ import Binary, ConcreteModel, Var

from temoa._internal import run_actions
from temoa.core.config import TemoaConfig


def test_config_selects_options_for_active_solver() -> None:
    database = Path(__file__).parent / 'testing_outputs' / 'utopia.sqlite'

    config = TemoaConfig(
        scenario='solver_options',
        scenario_mode='perfect_foresight',
        input_database=database,
        output_database=database,
        output_path=database.parent,
        solver_name='gurobi',
        solver_options={
            'gurobi': {'Method': 2, 'mip': {'MIPGap': 1.0e-4}},
            'appsi_highs': {'time_limit': 60},
        },
    )

    assert config.solver_options == {'Method': 2}
    assert config.mip_solver_options == {'MIPGap': 1.0e-4}


def test_configured_options_override_gurobi_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOptimizer:
        def __init__(self) -> None:
            self.options: dict[str, object] = {}

        def solve(self, instance: ConcreteModel, **kwargs: Any) -> SimpleNamespace:  # noqa: ARG002
            return SimpleNamespace(solver=SimpleNamespace())

    optimizer = FakeOptimizer()
    monkeypatch.setattr(run_actions, 'SolverFactory', lambda _name: optimizer)
    monkeypatch.setattr(run_actions, 'check_optimal_termination', lambda _result: True)

    run_actions.solve_instance(
        instance=ConcreteModel(),
        solver_name='gurobi',
        silent=True,
        solver_options={'Method': 1, 'MIPGap': 1.0e-4},
    )

    assert optimizer.options['Method'] == 1
    assert optimizer.options['MIPGap'] == 1.0e-4
    assert optimizer.options['Crossover'] == 0


def test_gurobi_uses_mip_profile_when_model_has_integer_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeOptimizer:
        def __init__(self) -> None:
            self.options: dict[str, object] = {}

        def solve(self, instance: ConcreteModel, **kwargs: Any) -> SimpleNamespace:  # noqa: ARG002
            return SimpleNamespace(solver=SimpleNamespace())

    optimizer = FakeOptimizer()
    monkeypatch.setattr(run_actions, 'SolverFactory', lambda _name: optimizer)
    monkeypatch.setattr(run_actions, 'check_optimal_termination', lambda _result: True)

    instance = ConcreteModel()
    instance.commitment = Var(domain=Binary)
    run_actions.solve_instance(instance=instance, solver_name='gurobi', silent=True)

    assert optimizer.options == {
        'Method': -1,
        'Crossover': -1,
        'MIPGap': 1.0e-4,
    }
