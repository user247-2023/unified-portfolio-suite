"""Deployment spec model + validation (stdlib only).

Purpose: Parse and *strictly validate* a deployment spec before anything touches
a cloud. Replaces a third-party validation library with explicit, dependency-free
checks so the validation logic is testable anywhere and the failure messages are
tailored.

Security trade-off: validation is fail-closed — unknown providers, out-of-range
ports/replicas, or missing fields raise `SpecError` rather than being coerced or
ignored. `network.public` defaults to False (private unless explicitly opened).
Credentials are never part of the spec; they come from each cloud's standard
environment credential chain.
"""
from __future__ import annotations

from dataclasses import dataclass, field

_PROVIDERS = {"aws", "gcp", "azure"}


class SpecError(ValueError):
    """Raised when a deployment spec is invalid."""


@dataclass
class AppSpec:
    name: str
    image: str
    port: int
    replicas: int


@dataclass
class ProviderSpec:
    name: str
    regions: list[str]


@dataclass
class NetworkSpec:
    cidr: str
    public: bool = False


@dataclass
class DeploymentSpec:
    app: AppSpec
    providers: list[ProviderSpec]
    network: NetworkSpec

    @classmethod
    def from_dict(cls, data: object) -> "DeploymentSpec":
        if not isinstance(data, dict):
            raise SpecError("spec must be a mapping")

        app = _require(data, "app", dict)
        name = _require(app, "name", str)
        image = _require(app, "image", str)
        port = _require(app, "port", int)
        replicas = _require(app, "replicas", int)
        if not (1 <= port <= 65535):
            raise SpecError(f"app.port out of range: {port}")
        if not (1 <= replicas <= 100):
            raise SpecError(f"app.replicas out of range: {replicas}")

        providers_raw = _require(data, "providers", list)
        if not providers_raw:
            raise SpecError("at least one provider is required")
        providers: list[ProviderSpec] = []
        for entry in providers_raw:
            if not isinstance(entry, dict):
                raise SpecError("each provider must be a mapping")
            pname = _require(entry, "name", str)
            if pname not in _PROVIDERS:
                raise SpecError(f"unsupported provider: {pname} "
                                f"(expected one of {sorted(_PROVIDERS)})")
            regions = _require(entry, "regions", list)
            if not regions or not all(isinstance(r, str) for r in regions):
                raise SpecError(f"provider {pname} needs a non-empty region list")
            providers.append(ProviderSpec(name=pname, regions=list(regions)))

        net = _require(data, "network", dict)
        network = NetworkSpec(
            cidr=_require(net, "cidr", str),
            public=bool(net.get("public", False)),
        )

        return cls(
            app=AppSpec(name=name, image=image, port=port, replicas=replicas),
            providers=providers,
            network=network,
        )


def _require(d: dict, key: str, typ: type):
    """Fetch `d[key]`, asserting type. Raises SpecError with a clear message."""
    if key not in d:
        raise SpecError(f"missing required field: {key}")
    value = d[key]
    # bool is a subclass of int — guard against it where we want a real int.
    if typ is int and isinstance(value, bool):
        raise SpecError(f"field {key} must be an int, not bool")
    if not isinstance(value, typ):
        raise SpecError(f"field {key} must be {typ.__name__}, got "
                        f"{type(value).__name__}")
    return value


def load_spec(path: str) -> DeploymentSpec:
    """Load + validate a spec from a YAML file (lazy YAML import)."""
    import yaml  # lazy: keeps the core importable/testable without PyYAML

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return DeploymentSpec.from_dict(raw)
