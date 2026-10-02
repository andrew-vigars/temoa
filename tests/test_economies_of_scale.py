from types import SimpleNamespace
from unittest.mock import patch

from temoa.extensions.economies_of_scale.components.cost_invest_eos import (
    initialize_cost_invest_eos,
)


class _EmptyParam:
    @staticmethod
    def sparse_keys() -> list[tuple[object, ...]]:
        return []


def test_initialize_cost_invest_eos_caches_previous_period_by_cluster() -> None:
    model = SimpleNamespace(
        cost_invest_eos=_EmptyParam(),
        cost_invest_eos_segments={},
        cost_invest_eos_period_rpt={
            ('R1', 2050, 'tech'),
            ('R2', 2030, 'tech'),
            ('R1', 2030, 'tech'),
            ('R1', 2040, 'tech'),
        },
        cost_invest_eos_previous_period={},
        cost_invest_eos_reference_process={},
        lifetime_process=object(),
        loan_lifetime_process=object(),
        loan_rate=object(),
    )

    with patch(
        'temoa.extensions.economies_of_scale.components.cost_invest_eos.'
        'capacity.gather_group_built_processes',
        return_value=[],
    ):
        initialize_cost_invest_eos(model)

    assert model.cost_invest_eos_previous_period == {
        ('R1', 2030, 'tech'): None,
        ('R1', 2040, 'tech'): 2030,
        ('R1', 2050, 'tech'): 2040,
        ('R2', 2030, 'tech'): None,
    }
