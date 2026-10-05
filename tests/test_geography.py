import sqlite3
from collections import defaultdict
from typing import TYPE_CHECKING, cast

from pyomo.environ import ConcreteModel, Set

from temoa.core.model import TemoaModel
from temoa.data_io.component_manifest import build_manifest
from temoa.data_io.hybrid_loader import HybridLoader
from temoa.model_checking.commodity_network_manager import CommodityNetworkManager
from temoa.model_checking.element_checker import ViableSet
from temoa.model_checking.network_model_data import EdgeTuple, NetworkModelData
from temoa.model_checking.validators import regional_index_check

if TYPE_CHECKING:
    from temoa.types import Commodity, Period, Region, Technology, Vintage


def test_regional_index_check_accepts_only_single_or_linked_regions() -> None:
    model = ConcreteModel()
    model.regions = Set(initialize=['A', 'B', 'C'])

    assert regional_index_check(cast('TemoaModel', model), cast('Region', 'A'))
    assert regional_index_check(cast('TemoaModel', model), cast('Region', 'A-B'))
    assert not regional_index_check(cast('TemoaModel', model), cast('Region', 'A+B'))
    assert not regional_index_check(cast('TemoaModel', model), cast('Region', 'A-B+A+B-A+B'))
    assert not regional_index_check(cast('TemoaModel', model), cast('Region', 'A-D'))


def test_regional_indices_are_distinct_efficiency_regions_filtered_by_viability() -> None:
    model = TemoaModel()
    item = next(item for item in build_manifest(model) if item.component is model.regional_indices)
    connection = sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE efficiency (region TEXT)')
    connection.executemany(
        'INSERT INTO efficiency VALUES (?)',
        [('A',), ('A',), ('A-B',), ('unused',)],
    )

    loader = HybridLoader.__new__(HybridLoader)
    loader.con = connection
    loader.viable_regions = ViableSet(elements={'A', 'A-B'})

    raw_data = loader._fetch_data(connection.cursor(), item, None)
    filtered_data = loader._filter_data(raw_data, item, use_raw_data=False)

    assert item.distinct
    assert item.table == 'efficiency'
    assert set(raw_data) == {('A',), ('A-B',), ('unused',)}
    assert set(filtered_data) == {('A',), ('A-B',)}


def test_network_filters_expose_viable_process_regions() -> None:
    network_data = NetworkModelData()
    network_data.available_techs[cast('tuple[Region, Period]', ('A', 2020))].add(
        EdgeTuple(
            cast('Region', 'A'),
            cast('Commodity', 'source'),
            cast('Technology', 'supply'),
            cast('Vintage', 2020),
            cast('Commodity', 'demand'),
        )
    )
    network_data.available_techs[cast('tuple[Region, Period]', ('A-B', 2020))].add(
        EdgeTuple(
            cast('Region', 'A-B'),
            cast('Commodity', 'power'),
            cast('Technology', 'exchange'),
            cast('Vintage', 2020),
            cast('Commodity', 'power'),
        )
    )
    manager = CommodityNetworkManager(periods=[2020], network_data=network_data)
    manager.analyzed = True
    manager.filtered_data = network_data

    filters = manager.build_filters(defaultdict(set))

    assert filters['r'].members == {'A', 'A-B'}
