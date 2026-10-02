from pyomo.environ import ConcreteModel, Set

from temoa.components.geography import create_regional_indices


def test_create_regional_indices_uses_only_observed_linked_regions() -> None:
    model = ConcreteModel()
    model.regions = Set(initialize=['A', 'B', 'C'])
    model.regional_global_indices = Set(
        initialize=['A', 'B', 'C', 'A-B', 'A+C', 'global']
    )

    assert create_regional_indices(model) == ['A', 'A-B', 'B', 'C']


def test_create_regional_indices_does_not_build_cartesian_product() -> None:
    regions = [f'R{i}' for i in range(1_000)]
    model = ConcreteModel()
    model.regions = Set(initialize=regions)
    model.regional_global_indices = Set(initialize=[*regions, 'R1-R2'])

    result = create_regional_indices(model)

    assert len(result) == len(regions) + 1
    assert 'R1-R2' in result
    assert 'R2-R1' not in result
