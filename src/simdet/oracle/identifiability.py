"""Consistent set of causes for a segment (spec 6.2)."""

from __future__ import annotations

from dataclasses import dataclass

from simdet.oracle.fit import HYPOTHESES, FitResult, OracleData, estimate_sigma, fit_hypothesis


@dataclass(frozen=True)
class OracleResult:
    sigma_hat: float
    noise_ratio: float
    fits: dict[str, FitResult]
    consistent_set: tuple[str, ...]
    status: str  # "ok" | "ambiguous" | "invalid"
    gray: tuple[str, ...]  # hypotheses that are neither consistent nor clearly rejected

    @property
    def identifiable(self) -> bool:
        return self.status == "ok" and len(self.consistent_set) == 1

    def to_json(self) -> dict:
        return {
            "sigma_hat": self.sigma_hat,
            "noise_ratio": self.noise_ratio,
            "decision_rms": {h: max(f.rms_v, f.rms_t) for h, f in self.fits.items()},
            "pooled_rms": {h: f.normalized_rms for h, f in self.fits.items()},
            "rms_v": {h: f.rms_v for h, f in self.fits.items()},
            "rms_t": {h: f.rms_t for h, f in self.fits.items()},
            "fit_param": {h: f.param for h, f in self.fits.items()},
            "consistent_set": list(self.consistent_set),
            "status": self.status,
            "gray": list(self.gray),
            "identifiable": self.identifiable,
        }


def decision_rms(thresholds, fit: FitResult) -> float:
    """The number compared with the thresholds.

    The spec says normalized_rms is normalised by sigma_hat and SIGMA_T but not how the
    two channels combine. `max_channel` (default) takes the worse channel, so a
    hypothesis has to explain voltage and temperature each on its own; `pooled` is the
    RMS over both channels together, which lets a perfect fit of one channel dilute a
    misfit of the other by up to sqrt(2).
    """
    if thresholds.get("rms_mode", "max_channel") == "pooled":
        return fit.normalized_rms
    return max(fit.rms_v, fit.rms_t)


def evaluate(cfg, data: OracleData, planted: str | None = None) -> OracleResult:
    """Apply rules 1-4 of spec 6.2. `planted` enables rule 4."""
    p = cfg.cell
    th = cfg["oracle"]
    sigma_hat = estimate_sigma(data)
    noise_ratio = sigma_hat / p.sigma_v
    fits = {h: fit_hypothesis(p, data, h, sigma_hat) for h in HYPOTHESES}

    score = {h: decision_rms(th, f) for h, f in fits.items()}
    consistent = {h for h in fits if score[h] <= th["consistent_max"]}
    rejected = {h for h in fits if score[h] >= th["clear_reject_min"]}
    gray = tuple(h for h in HYPOTHESES if h not in consistent and h not in rejected)

    if "H" in consistent:  # rule 1
        result = ("N",) if noise_ratio >= th["noise_ratio_min"] else ("H",)
    else:  # rule 2
        result = tuple(h for h in HYPOTHESES if h != "H" and h in consistent)

    if gray:  # rule 3
        status = "ambiguous"
    elif planted is not None and planted not in result:  # rule 4
        status = "invalid"
    else:
        status = "ok"
    return OracleResult(sigma_hat, noise_ratio, fits, result, status, gray)
