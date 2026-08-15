import numpy as np
import pytest

from probability_sonification.distributions import sample_distribution


def test_sampling_is_reproducible():
    first = sample_distribution("Poisson", {"lam": 2.0}, 32, 42)
    second = sample_distribution("Poisson", {"lam": 2.0}, 32, 42)
    np.testing.assert_array_equal(first, second)


def test_invalid_normal_scale_is_rejected():
    with pytest.raises(ValueError, match="at least 0.01"):
        sample_distribution("Normal", {"loc": 0.0, "scale": 0.0}, 32, 42)


def test_uniform_samples_stay_within_bounds():
    samples = sample_distribution("Uniform", {"low": -2.0, "high": 3.0}, 100, 42)
    assert np.all(samples >= -2.0)
    assert np.all(samples < 3.0)


def test_invalid_uniform_bounds_are_rejected():
    with pytest.raises(ValueError, match="greater than lower bound"):
        sample_distribution("Uniform", {"low": 1.0, "high": 1.0}, 32, 42)


def test_bernoulli_support_is_zero_and_one():
    samples = sample_distribution("Bernoulli", {"p": 0.5}, 100, 42)
    assert set(samples).issubset({0, 1})


def test_rademacher_support_is_negative_and_positive_one():
    samples = sample_distribution("Rademacher", {}, 100, 42)
    assert set(samples) == {-1, 1}
