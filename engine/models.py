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

        return BIAProject(
            title=data.get("title", "Untitled BIA Project"),
            organization=org,
            processes=processes,
            impacts=impacts,
            decision_matrix=decision_matrix,
        )
