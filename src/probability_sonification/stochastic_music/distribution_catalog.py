"""User-facing reference information for stochastic sampling distributions."""

from dataclasses import dataclass
from enum import Enum

from probability_sonification.stochastic_music.models import (
    EventCountDistribution,
    EventPitchDistribution,
    EventTimeDistribution,
)


@dataclass(frozen=True)
class DistributionInfo:
    """Textbook-style information shared by controls and explanatory UI."""

    name: str
    formula: str
    purpose: str
    description: str
    parameters: tuple[tuple[str, str], ...]
    implemented: bool


DISTRIBUTION_INFO: dict[tuple[type[Enum], str], DistributionInfo] = {
    (EventCountDistribution, EventCountDistribution.POISSON.value): DistributionInfo(
        name="Poisson distribution",
        formula=r"N \sim \operatorname{Poisson}(\lambda)",
        purpose="Samples the number of events for an instrument in each time block.",
        description=(
            "The Poisson distribution models non-negative event counts at a stable "
            "average rate. Its expected value and variance are both λ."
        ),
        parameters=(("λ", "Expected number of events per time block."),),
        implemented=True,
    ),
    (
        EventCountDistribution,
        EventCountDistribution.NEGATIVE_BINOMIAL.value,
    ): DistributionInfo(
        name="Negative binomial distribution",
        formula=r"N \sim \operatorname{NegBin}(r, p)",
        purpose="Samples event counts with more variation than a Poisson model.",
        description=(
            "This distribution can represent occasional dense bursts separated by "
            "quieter blocks. Its exact parameterization will be finalized later."
        ),
        parameters=(
            ("r", "Count or shape parameter; exact interpretation is pending."),
            ("p", "Probability parameter; exact interpretation is pending."),
        ),
        implemented=False,
    ),
    (EventCountDistribution, EventCountDistribution.BINOMIAL.value): DistributionInfo(
        name="Binomial distribution",
        formula=r"N \sim \operatorname{Binomial}(n, p)",
        purpose="Samples a count from a fixed number of event opportunities.",
        description=(
            "The count cannot exceed n, giving each time block a deliberate upper "
            "limit on the number of generated events."
        ),
        parameters=(
            ("n", "Number of event opportunities."),
            ("p", "Probability of an event in each opportunity."),
        ),
        implemented=False,
    ),
    (EventTimeDistribution, EventTimeDistribution.UNIFORM.value): DistributionInfo(
        name="Uniform distribution",
        formula=r"T \sim \operatorname{Uniform}(a, b)",
        purpose="Samples the start time of each event inside its assigned block.",
        description=(
            "Every time between the beginning a and end b of the block is equally "
            "likely. Sampled times are sorted before events are assembled."
        ),
        parameters=(
            ("a", "Beginning of the current time block."),
            ("b", "End of the current time block."),
        ),
        implemented=True,
    ),
    (EventTimeDistribution, EventTimeDistribution.BETA.value): DistributionInfo(
        name="Beta distribution",
        formula=r"\frac{T-a}{b-a} \sim \operatorname{Beta}(\alpha, \beta)",
        purpose="Shapes where events tend to occur inside a time block.",
        description=(
            "Different α and β values can favor the beginning, middle, or end of a "
            "block. The final control ranges will be chosen with the implementation."
        ),
        parameters=(
            ("α", "Shape toward the beginning of the block."),
            ("β", "Shape toward the end of the block."),
        ),
        implemented=False,
    ),
    (
        EventTimeDistribution,
        EventTimeDistribution.EXPONENTIAL.value,
    ): DistributionInfo(
        name="Exponential distribution",
        formula=r"T \sim \operatorname{Exponential}(\lambda)",
        purpose="Favors event starts near the beginning of a time block.",
        description=(
            "Probability decreases as time advances. The policy for keeping samples "
            "inside a block will be decided when this option is implemented."
        ),
        parameters=(("λ", "Timing rate; its final UI interpretation is pending."),),
        implemented=False,
    ),
    (EventPitchDistribution, EventPitchDistribution.NORMAL.value): DistributionInfo(
        name="Normal distribution",
        formula=r"P \sim \mathcal{N}(\mu, \sigma^2)",
        purpose="Samples MIDI pitches around a central note.",
        description=(
            "The sampler draws continuous values, rounds them to MIDI notes, and clips "
            "them to the configured allowed-pitch range. This is clipping, not a "
            "mathematically truncated Normal distribution."
        ),
        parameters=(
            ("μ", "Mean MIDI pitch, which sets the center."),
            ("σ", "Standard deviation, which controls pitch spread."),
            ("minimum–maximum", "Allowed MIDI pitch range after rounding."),
        ),
        implemented=True,
    ),
    (EventPitchDistribution, EventPitchDistribution.UNIFORM.value): DistributionInfo(
        name="Uniform distribution",
        formula=r"P \sim \operatorname{Uniform}(a, b)",
        purpose="Samples pitches without favoring a center note.",
        description=(
            "Every value in the configured interval is equally likely before conversion "
            "to an integer MIDI pitch. Endpoint behavior will be finalized later."
        ),
        parameters=(
            ("a", "Lowest pitch boundary."),
            ("b", "Highest pitch boundary."),
        ),
        implemented=False,
    ),
    (
        EventPitchDistribution,
        EventPitchDistribution.TRIANGULAR.value,
    ): DistributionInfo(
        name="Triangular distribution",
        formula=r"P \sim \operatorname{Triangular}(a, m, b)",
        purpose="Favors a modal pitch while retaining firm lower and upper limits.",
        description=(
            "Probability rises toward the mode m and falls toward the two boundaries, "
            "providing a clear center without unbounded tails."
        ),
        parameters=(
            ("a", "Lowest pitch boundary."),
            ("m", "Most likely or modal pitch."),
            ("b", "Highest pitch boundary."),
        ),
        implemented=False,
    ),
}


def distribution_info(distribution: Enum) -> DistributionInfo:
    """Return the reference entry for a supported distribution assignment."""

    return DISTRIBUTION_INFO[(type(distribution), distribution.value)]
