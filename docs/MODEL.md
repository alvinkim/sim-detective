# The battery model

A short description of the simulated plant: the single cell used in Direction 1 and in rounds 1–2 of Direction 2, and what rounds 3 and 4 add. Parameter values are those in `config/default.yaml` and `config/control*.yaml`; the code is in `src/simdet/sim/cell.py`, `src/simdet/control/r3/thermal.py` and `src/simdet/control/r4/pack.py`.

All models are integrated with forward Euler at a 1 s step. Current is positive on discharge.

## 1. One cell

### Electrical side

An equivalent circuit: a voltage source that depends on state of charge, a series resistance that depends on temperature, and one RC branch.

```
            R0(T)             R1
   +------/\/\/\------+-----/\/\/\-----+--------o  +
   |                  |                |
   |                  +-------||-------+
  ( ) OCV(soc)                C1                  V   (measured, noise 1 mV)
   |
   |                 <--- v1 --->
   +--------------------------------------------o  -

                   I  -->  (discharge positive)
```

```
V        = OCV(soc) - I * R0(T) - v1
OCV(soc) = 3.30 V + 0.80 V * soc                    (linear)
R0(T)    = r0_ref * s * (1 + alpha * (T_ref - T))   (falls 3% per K of warming)
dv1/dt   = (I * R1 - v1) / tau1
dsoc/dt  = -I / (3600 * Q)
```

| Symbol | Value | Meaning |
|---|---|---|
| Q | 50 Ah | Capacity |
| r0_ref | 3.0 mΩ | Series resistance at T_ref = 25 °C |
| s | 1 | Resistance factor of the cell (larger for an aged cell) |
| alpha | 0.03 /K | Temperature coefficient of R0 |
| R1, tau1 | 1.0 mΩ, 30 s | RC branch |

### Thermal side

One lumped temperature. The only heat source is the series resistance; the only loss is cooling to ambient.

```
                      +---------------+        h
   I^2 * R0(T)  --->  |   C  (cell)   | ----/\/\/\----  T_amb
      (heat)          |       T       |
                      +---------------+
                              |
                    T measured, noise 0.1 K
```

```
C * dT/dt = I^2 * R0(T) - h * (T - T_amb)
```

| Symbol | Value | Meaning |
|---|---|---|
| C | 1000 J/K | Heat capacity |
| h | 0.556 W/K | Cooling to ambient (thermal time constant C/h of about 1,800 s) |

The two sides are coupled through R0(T): heating depends on the resistance, and the resistance depends on temperature. This coupling is what round 4 uses to read temperature from voltage.

### How Direction 1 uses it

The twin is this model with nominal parameters. Each planted cause changes one thing in the true cell:

| Cause | Change in the true cell | Shows in |
|---|---|---|
| R0 | s > 1 | Voltage (larger drop under current) and temperature (more heat) |
| SOC0 | Initial soc differs from what the twin believes | Voltage: a constant offset of 0.80 V × the soc difference |
| ST | A second RC branch (R2, tau2 = 300 s) that the twin does not have | Voltage: an extra drop that settles to I × R2 |
| TB | Bias on the temperature reading | Temperature only |
| N | Voltage noise multiplied | Scatter of the voltage |

The not-identifiable case follows from the table. Under a constant 25 A that has already run for 2,400 s (eight times tau2), the second branch is saturated, so ST gives a flat offset I × R2. SOC0 also gives a flat offset. Neither adds heat in this model, so the temperature channel does not help. A rest or a pulse separates them: the ST offset relaxes with a 300 s time constant, the SOC0 offset does not.

## 2. What Direction 2 changes by round

The electrical side is the same in every round. The thermal side and what is measured change.

| Round | Thermal model | Measured | Limit | Hidden from the monitors |
|---|---|---|---|---|
| 1, 2 | One node (section 1) | Current, voltage, temperature | 37 °C (ambient 25 °C + 12 K) | Round 1: true R0 and h differ from the twin's by up to 30% |
| 3 | Two nodes: core and surface | Surface temperature only | 42 °C on the core | The core temperature |
| 4 | Six cells in series, one node each, conduction between neighbours | Six cell voltages; temperature on cells 1 and 6 only | 40 °C on the hottest cell | Which cell is faulty, and how |

### Round 3: core and surface

```
                    +----------+     R_cs     +-----------+      h
  I^2 * R0(T_c) --> |   C_c    | ---/\/\/\--- |    C_s    | ---/\/\/\---  T_amb
                    |   T_c    |              |    T_s    |
                    +----------+              +-----------+
                    limit applies                  |
                    here, not measured        T_s measured
```

```
C_c * dT_c/dt = I^2 * R0(T_c) - (T_c - T_s) / R_cs
C_s * dT_s/dt = (T_c - T_s) / R_cs - h * (T_s - T_amb)
```

C_c = 700 J/K, C_s = 300 J/K (their sum is the single node of rounds 1–2), R_cs = 0.3 K/W. Under a fast current pulse the core runs ahead of the surface, so a temperature alarm on the surface reading sees the rise late.

### Round 4: a six-cell pack with a hidden fault

```
   I -->   [cell 1]---[cell 2]---[cell 3]---[cell 4]---[cell 5]---[cell 6]    same current
              |          |          |          |          |          |
   voltage    V1         V2         V3         V4         V5         V6       all measured
   temperature T1        .          .          .          .          T6       sensors on 1 and 6 only

   heat flow:
              k          k          k          k          k
      T1 <------> T2 <------> T3 <------> T4 <------> T5 <------> T6          between neighbours
       |          |           |           |           |           |
       h1         h2          h3          h4          h5          h6          each cell to T_amb
```

```
C * dT_i/dt = I^2 * R0_i(T_i) - h_i * (T_i - T_amb) - k * (T_i - T_(i-1)) - k * (T_i - T_(i+1))
R0_i(T)     = r0_ref * s_i * (1 + alpha * (T_ref - T))
V_i         = OCV(soc) - I * R0_i(T_i) - v1
```

k = 0.1 W/K between neighbours. Ambient is 30–35 °C per episode and known to everyone. Every episode starts with a check pulse (25 A for 60 s, then 60 s rest) at ambient temperature.

The hidden plant state is one of four, with the fault always in one of cells 2–5, the cells without a temperature sensor:

| State | Share of episodes | Fault |
|---|---|---|
| F0 | 40% | None |
| F1 | 20% | Aged cell: s_i between 1.3 and 1.8 (more heat at the same current) |
| F2 | 20% | Blocked cooling: h_i between 0.3 and 0.5 of nominal |
| F3 | 20% | Both, on the same cell |

The same current plan is safe on a healthy pack and overheats a faulty one. A rule that looks only at the plan, or only at the two temperature sensors, cannot tell which pack it has.

**Reading temperature from voltage.** The cell voltage contains the cell temperature through R0_i(T_i):

```
V_i = OCV(soc) - v1 - I * r0_ref * s_i * (1 + alpha * (T_ref - T_i))
```

OCV, v1 and I are known from the current history. The check pulse gives s_i, because the temperature is known then (ambient). During operation the only unknown left is T_i. At 40 A, 1 K changes the cell voltage by 40 A × 3.0 mΩ × 0.03 /K = 3.6 mV, against a voltage noise of 1 mV. Equivalently, a 1 mV error in the voltage is about 0.3 K, which is why a 5 mV sensor bias is enough to break this estimate.

Two monitors use this relation:

| Monitor | Uses | Does not use |
|---|---|---|
| Rule R9 | The relation above, solved for T_i by least squares over the latest samples. Alarm on the largest estimated temperature now | Heat capacity, cooling, conduction; no prediction |
| Twin | The same relation inside a filter that also estimates each cell's cooling factor, then a prediction of the largest cell temperature over the submitted plan plus a 300 s hold | — |

The difference between the two is the thermal model and the prediction. In the confirmation run that difference was worth 0–7.5 points of safety; see [RESULTS_DIRECTION2.md](RESULTS_DIRECTION2.md), section 3.4.

## 3. What the model leaves out

- Heat comes from the series resistance only. The RC branches, entropic heat and heat from the pack's connections are not modelled.
- OCV is linear in state of charge, with no hysteresis and no temperature dependence. State of charge is kept within 0.2–0.8 (0.25–0.75 in Direction 2).
- Only R0 depends on temperature. R1, the time constants and the capacity do not.
- All six cells in round 4 have the same state of charge and the same RC voltage. A fault changes R0 or cooling of one cell and does not develop during an episode.
- The twin has the same structure as the plant. Errors were applied to one parameter at a time; a twin with the wrong structure was tested only as the ST cause in Direction 1.
- Sensor noise is Gaussian and white. Current is measured exactly.
