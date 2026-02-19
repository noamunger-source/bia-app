from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List


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

        return BIAProject(
            title=data.get("title", "Untitled BIA Project"),
            organization=org,
            processes=processes,
            impacts=impacts,
        )
