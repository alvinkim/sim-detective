"""Twin monitor of the pack (FOLLOWUP-003, 5, M2): estimator and predictor.

The twin has the nominal electrical-thermal model of the pack (in G0''' equal to the plant except
for the hidden plant state) and sees the current, the six cell voltages, the two temperature
sensors and the ambient temperature.

1. Check pulse: R0 factor s_i of every cell, from the voltage drop during the pulse divided by
   the nominal R0 at the temperature the model gives for the pulse.
2. Operation: per cell an extended Kalman filter on (T_i, c_i), c_i = cooling factor of the cell
   (h_i = c_i h_nominal). The cell voltage is linear in T_i through R0(T_i); sensor cells also
   use their temperature reading. Conduction to the neighbours uses the current estimates.
3. Score: largest cell temperature the estimated pack reaches over the plan and the hold, minus
   the limit.
"""

from __future__ import annotations

import numpy as np

from simdet.control.config import ControlConfig
from simdet.control.r4 import pack as pk
from simdet.sim.cell import ocv


class Twin:
    def __init__(self, cfg: ControlConfig, nominal: pk.Pack, t_amb: float):
        tw = cfg["twin_monitor"]
        n = nominal.n
        self.cfg, self.nominal, self.t_amb = cfg, nominal, float(t_amb)
        self.sensors = np.array(cfg["pack"]["sensor_cells"]) - 1
        self.s = np.ones(n)
        self.temp = np.full(n, float(t_amb))
        self.c = np.full(n, float(tw["c_prior"]))
        self.p11 = np.full(n, float(tw["p_temp0_k"]) ** 2)
        self.p12 = np.zeros(n)
        self.p22 = np.full(n, float(tw["c_sigma"]) ** 2)
        self.deg = np.array([1.0] + [2.0] * (n - 2) + [1.0]) if n > 1 else np.zeros(1)

    # -- 1. check pulse ------------------------------------------------------------------------
    def fit_r0(self, current, v_meas, soc, v1) -> np.ndarray:
        """R0 factor per cell from the samples of the pulse with current."""
        p = self.nominal.cell
        current = np.asarray(current, dtype=float)
        on = np.abs(current) > 1e-9
        drop = (ocv(p, np.asarray(soc)) - np.asarray(v1))[:, None] - np.asarray(v_meas)   # I R0_i
        r_meas = (drop[on] / current[on, None]).mean(axis=0)
        s = np.ones(self.nominal.n)
        for _ in range(2):   # the temperature during the pulse depends a little on s
            model = pk.Pack(p, self.nominal.k, s, self.nominal.h)
            temps, _ = pk.simulate(model, np.full(model.n, self.t_amb), self.t_amb, current)
            s = r_meas / (p.r0_ref * (1.0 + p.alpha * (p.t_ref - temps[on]))).mean(axis=0)
        self.s = s
        return s

    # -- 2. operation --------------------------------------------------------------------------
    def advance(self, current, v_meas, t_meas, soc, v1) -> None:
        """Samples k: readings of the state at k, then the current of [k, k+1)."""
        p, tw = self.nominal.cell, self.cfg["twin_monitor"]
        n = self.nominal.n
        h, k, c_th, a = self.nominal.h, self.nominal.k, p.c_th, p.alpha
        r0s = p.r0_ref * self.s
        rv, rt = p.sigma_v ** 2, p.sigma_t ** 2
        qt, qc = float(tw["q_temp_k"]) ** 2, float(tw["q_c"]) ** 2
        c_lo, c_hi = tw["c_bounds"]
        sens, deg, t_amb = self.sensors, self.deg, self.t_amb
        temp, c, p11, p12, p22 = self.temp, self.c, self.p11, self.p12, self.p22
        e0 = ocv(p, np.asarray(soc)) - np.asarray(v1)
        lap = np.empty(n)
        for j in range(len(current)):
            i = float(current[j])
            # voltage update (no information without current)
            if i != 0.0:
                hv = i * r0s * a
                y = v_meas[j] - (e0[j] - i * r0s * (1.0 + a * (p.t_ref - temp)))
                sv = hv * hv * p11 + rv
                k1, k2 = p11 * hv / sv, p12 * hv / sv
                temp = temp + k1 * y
                c = c + k2 * y
                p11, p12, p22 = p11 - k1 * hv * p11, p12 - k1 * hv * p12, p22 - k2 * hv * p12
            # temperature sensors
            y = t_meas[j] - temp[sens]
            st = p11[sens] + rt
            k1, k2 = p11[sens] / st, p12[sens] / st
            temp[sens] += k1 * y
            c[sens] += k2 * y
            p11s, p12s = p11[sens].copy(), p12[sens].copy()
            p11[sens], p12[sens], p22[sens] = p11s - k1 * p11s, p12s - k1 * p12s, p22[sens] - k2 * p12s
            c = np.clip(c, c_lo, c_hi)
            # model step
            theta = temp - t_amb
            if n > 1:
                lap[0] = temp[0] - temp[1]
                lap[-1] = temp[-1] - temp[-2]
                lap[1:-1] = 2.0 * temp[1:-1] - temp[:-2] - temp[2:]
            else:
                lap[0] = 0.0
            f11 = 1.0 - (i * i * r0s * a + c * h + k * deg) / c_th
            f12 = -h * theta / c_th
            temp = temp + (i * i * r0s * (1.0 + a * (p.t_ref - temp)) - c * h * theta - k * lap) / c_th
            p11, p12, p22 = (f11 * f11 * p11 + 2.0 * f11 * f12 * p12 + f12 * f12 * p22 + qt,
                             f11 * p12 + f12 * p22, p22 + qc)
        self.temp, self.c, self.p11, self.p12, self.p22 = temp, c, p11, p12, p22

    # -- 3. prediction -------------------------------------------------------------------------
    def estimated_pack(self) -> pk.Pack:
        return pk.Pack(self.nominal.cell, self.nominal.k, self.s.copy(), self.c * self.nominal.h)

    def score(self, commands) -> float:
        cfg = self.cfg
        period = cfg["plant"]["command_period_s"]
        commands = np.asarray(commands, dtype=float)
        current = np.concatenate([np.repeat(commands, period),
                                  np.full(int(cfg["twin_monitor"]["hold_s"]), commands[-1])])
        return pk.peak(self.estimated_pack(), self.temp, self.t_amb, current) - cfg["plant"]["t_limit_k"]
