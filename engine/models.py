from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class TriangularFuzzyNumber:
    lower: float = 0.0
    middle: float = 0.0
    upper: float = 0.0

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.lower, self.middle, self.upper)


@dataclass
class Criterion:
    name: str
    criterion_type: str = "benefit"  # benefit | cost


@dataclass
class Product:
    name: str
    description: str = ""


@dataclass
class DecisionMatrix:
    criteria: List[Criterion] = field(default_factory=list)
    products: List[Product] = field(default_factory=list)
    evaluations: List[List[TriangularFuzzyNumber]] = field(default_factory=list)


@dataclass
class Asset:
    name: str
    category: str = "Facility"
    owner: str = ""


@dataclass
class LikelihoodInputs:
    dpf: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)
    ddf: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)
    ucf: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)
    def_: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)


@dataclass
class ImpactInputs:
    sf: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)
    pf: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)
    rc: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)
    ls: TriangularFuzzyNumber = field(default_factory=TriangularFuzzyNumber)


@dataclass
class FactorWeights:
    likelihood: dict[str, float] = field(
        default_factory=lambda: {"daf": 0.4, "ucf": 0.3, "def": 0.3}
    )
    impact: dict[str, float] = field(
        default_factory=lambda: {"sf": 0.25, "pf": 0.25, "rc": 0.25, "ls": 0.25}
    )


@dataclass
class ContinuityParams:
    criticality_threshold: float = 3.0
    watch_threshold: float = 2.0


@dataclass
class RiskAppetiteSettings:
    max_acceptable_likelihood: float = 2.5
    max_acceptable_impact: float = 2.5


@dataclass
class RiskScore:
    asset_name: str
    likelihood: float
    impact: float
    risk_value: float
    critical: bool
    wpa: float = 0.0


@dataclass
class Organization:
    name: str = ""
    industry: str = ""
    headquarters: str = ""


@dataclass
class Dependency:
    name: str
    category: str = "Internal"
    criticality: int = 3


@dataclass
class Process:
    name: str
    owner: str = ""
    description: str = ""
    dependencies: List[Dependency] = field(default_factory=list)


@dataclass
class Impact:
    process_name: str
    financial_score: int = 1
    operational_score: int = 1
    reputational_score: int = 1


@dataclass
class BIAProject:
    title: str = "Untitled BIA Project"
    organization: Organization = field(default_factory=Organization)
    processes: List[Process] = field(default_factory=list)
    impacts: List[Impact] = field(default_factory=list)
    decision_matrix: DecisionMatrix = field(default_factory=DecisionMatrix)
    assets: List[Asset] = field(default_factory=list)
    likelihood_inputs: dict[str, LikelihoodInputs] = field(default_factory=dict)
    impact_inputs: dict[str, ImpactInputs] = field(default_factory=dict)
    factor_weights: FactorWeights = field(default_factory=FactorWeights)
    continuity_params: ContinuityParams = field(default_factory=ContinuityParams)
    risk_appetite: RiskAppetiteSettings = field(default_factory=RiskAppetiteSettings)
    risk_scores: List[RiskScore] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "BIAProject":
        org = Organization(**data.get("organization", {}))

        processes: List[Process] = []
        for p in data.get("processes", []):
            deps = [Dependency(**d) for d in p.get("dependencies", [])]
            process = Process(
                name=p.get("name", ""),
                owner=p.get("owner", ""),
                description=p.get("description", ""),
                dependencies=deps,
            )
            processes.append(process)

        impacts = [Impact(**i) for i in data.get("impacts", [])]

        dm_data = data.get("decision_matrix", {})
        criteria = [Criterion(**c) for c in dm_data.get("criteria", [])]
        products = [Product(**p) for p in dm_data.get("products", [])]
        evaluations = [
            [TriangularFuzzyNumber(**cell) for cell in row] for row in dm_data.get("evaluations", [])
        ]
        decision_matrix = DecisionMatrix(criteria=criteria, products=products, evaluations=evaluations)

        assets = [Asset(**a) for a in data.get("assets", [])]

        likelihood_inputs = {
            name: LikelihoodInputs(
                dpf=TriangularFuzzyNumber(**value.get("dpf", {})),
                ddf=TriangularFuzzyNumber(**value.get("ddf", {})),
                ucf=TriangularFuzzyNumber(**value.get("ucf", {})),
                def_=TriangularFuzzyNumber(**value.get("def_", {})),
            )
            for name, value in data.get("likelihood_inputs", {}).items()
        }

        impact_inputs = {
            name: ImpactInputs(
                sf=TriangularFuzzyNumber(**value.get("sf", {})),
                pf=TriangularFuzzyNumber(**value.get("pf", {})),
                rc=TriangularFuzzyNumber(**value.get("rc", {})),
                ls=TriangularFuzzyNumber(**value.get("ls", {})),
            )
            for name, value in data.get("impact_inputs", {}).items()
        }

        factor_weights = FactorWeights(**data.get("factor_weights", {}))
        continuity_params = ContinuityParams(**data.get("continuity_params", {}))
        risk_appetite = RiskAppetiteSettings(**data.get("risk_appetite", {}))
        risk_scores = [RiskScore(**r) for r in data.get("risk_scores", [])]

        return BIAProject(
            title=data.get("title", "Untitled BIA Project"),
            organization=org,
            processes=processes,
            impacts=impacts,
            decision_matrix=decision_matrix,
            assets=assets,
            likelihood_inputs=likelihood_inputs,
            impact_inputs=impact_inputs,
            factor_weights=factor_weights,
            continuity_params=continuity_params,
            risk_appetite=risk_appetite,
            risk_scores=risk_scores,
        )
