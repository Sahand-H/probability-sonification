from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class ParameterDefinition:
    label: str
    default: float | int
    minimum: float | int | None = None
    maximum: float | int | None = None
    integer: bool = False
    strictly_positive: bool = False
    step: float | int = 0.1


@dataclass(frozen=True)
class DistributionDefinition:
    parameters: dict[str, ParameterDefinition]
    sampler: Callable[..., np.ndarray]
    discrete: bool


DISTRIBUTIONS: dict[str, DistributionDefinition] = {
    "Poisson": DistributionDefinition(
        parameters={
            "lam": ParameterDefinition("Mean (μ)", 2.0, minimum=0.0),
        },
        sampler=lambda rng, size, **p: rng.poisson(size=size, **p),
        discrete=True,
    ),
    "Normal": DistributionDefinition(
        parameters={
            "loc": ParameterDefinition("Mean (μ)", 2.0),
            "scale": ParameterDefinition(
                "Std. deviation (σ)", 1.0, minimum=0.01, strictly_positive=True
            ),
        },
        sampler=lambda rng, size, **p: rng.normal(size=size, **p),
        discrete=False,
    ),
    "Binomial": DistributionDefinition(
        parameters={
            "n": ParameterDefinition(
                "Trials (n)", 10, minimum=0, maximum=1000, integer=True, step=1
            ),
            "p": ParameterDefinition(
                "Probability (p)", 0.5, minimum=0.0, maximum=1.0, step=0.05
            ),
        },
        sampler=lambda rng, size, **p: rng.binomial(size=size, **p),
        discrete=True,
    ),
    "Exponential": DistributionDefinition(
        parameters={
            "scale": ParameterDefinition(
                "Scale", 1.0, minimum=0.01, strictly_positive=True
            ),
        },
        sampler=lambda rng, size, **p: rng.exponential(size=size, **p),
        discrete=False,
    ),
    "Uniform": DistributionDefinition(
        parameters={
            "low": ParameterDefinition("Lower bound", 0.0),
            "high": ParameterDefinition("Upper bound", 5.0),
        },
        sampler=lambda rng, size, **p: rng.uniform(size=size, **p),
        discrete=False,
    ),
    "Beta": DistributionDefinition(
        parameters={
            "a": ParameterDefinition(
                "Shape α", 2.0, minimum=0.01, strictly_positive=True
            ),
            "b": ParameterDefinition(
                "Shape β", 5.0, minimum=0.01, strictly_positive=True
            ),
        },
        sampler=lambda rng, size, **p: rng.beta(size=size, **p),
        discrete=False,
    ),
    "Bernoulli": DistributionDefinition(
        parameters={
            "p": ParameterDefinition(
                "Probability (p)", 0.5, minimum=0.0, maximum=1.0, step=0.05
            ),
        },
        sampler=lambda rng, size, **p: rng.binomial(n=1, size=size, **p),
        discrete=True,
    ),
    "Rademacher": DistributionDefinition(
        parameters={},
        sampler=lambda rng, size, **p: rng.choice((-1, 1), size=size),
        discrete=True,
    ),
}


def sample_distribution(
    name: str, parameters: dict[str, float | int], size: int, seed: int
) -> np.ndarray:
    if name not in DISTRIBUTIONS:
        raise ValueError(f"Unknown distribution: {name}")
    if not 1 <= size <= 2_000:
        raise ValueError("Sample size must be between 1 and 2,000.")

    definition = DISTRIBUTIONS[name]
    for parameter_name, parameter in definition.parameters.items():
        value = parameters[parameter_name]
        if parameter.integer and not isinstance(value, (int, np.integer)):
            raise ValueError(f"{parameter.label} must be an integer.")
        if parameter.minimum is not None and value < parameter.minimum:
            raise ValueError(f"{parameter.label} must be at least {parameter.minimum}.")
        if parameter.maximum is not None and value > parameter.maximum:
            raise ValueError(f"{parameter.label} must be at most {parameter.maximum}.")
        if parameter.strictly_positive and value <= 0:
            raise ValueError(f"{parameter.label} must be greater than zero.")

    if name == "Uniform" and parameters["high"] <= parameters["low"]:
        raise ValueError("Upper bound must be greater than lower bound.")

    return definition.sampler(np.random.default_rng(seed), size, **parameters)
