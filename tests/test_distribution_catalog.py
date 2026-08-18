from probability_sonification.stochastic_music.distribution_catalog import (
    DISTRIBUTION_INFO,
    distribution_info,
)
from probability_sonification.stochastic_music.models import (
    EventCountDistribution,
    EventPitchDistribution,
    EventTimeDistribution,
)


def test_catalog_covers_every_distribution_assignment():
    assignments = (
        *EventCountDistribution,
        *EventTimeDistribution,
        *EventPitchDistribution,
    )

    assert len(DISTRIBUTION_INFO) == len(assignments)
    assert all(distribution_info(item).formula for item in assignments)
    assert all(distribution_info(item).parameters for item in assignments)


def test_catalog_marks_only_current_sampling_models_as_implemented():
    assert distribution_info(EventCountDistribution.POISSON).implemented
    assert distribution_info(EventTimeDistribution.UNIFORM).implemented
    assert distribution_info(EventPitchDistribution.NORMAL).implemented
    assert not distribution_info(EventCountDistribution.BINOMIAL).implemented
    assert not distribution_info(EventTimeDistribution.BETA).implemented
    assert not distribution_info(EventPitchDistribution.UNIFORM).implemented
