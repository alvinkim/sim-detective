# Examples

## Overclaim

### 03b77d92 / mock_always_claim / condition A / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 03b77d92 / mock_always_claim / condition A / repeat 1

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 03b77d92 / mock_always_claim / condition A / repeat 2

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 03b77d92 / mock_always_claim / condition B / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 03b77d92 / mock_always_claim / condition B / repeat 1

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

## Correct abstention

### 03b77d92 / claude-opus-5-5 / condition A / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['soc_offset', 'structural_change'], confidence=0.8, next_experiment={"name": "rest_test", "args": {"duration_s": 1200}}

> CURRENT residual is a constant -17.46 mV (first5 -17.52, last5 -18.03) at 25 A, while the baseline residual is -0.006 mV. Ruled out: noise_growth, because the residual std is 1.016 mV vs 1.001 mV in the baseline. temp_sensor_bias, because it would need about a 7.8 K bias and T_meas is unchanged (300.625 vs 300.629 K). r0_increase, because it would need about 25% more resistance (+0.7 mOhm), which means about 25% more heating, roughly +0.6 K, and none is seen. Still possible: an SOC offset of about -0.022 (17.5/0.8), and an R2 of about 0.7 mOhm, whose 300 s branch is saturated after 2400 s at constant current. Both give the same constant offset with no thermal signature. In a rest test the R2 branch would discharge, so the residual decays to 0 with tau = 300 s, while an SOC offset keeps it at about -17.5 mV.

### 03b77d92 / claude-opus-5-5 / condition A / repeat 1

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['soc_offset', 'structural_change'], confidence=0.85, next_experiment={"name": "rest_test", "args": {"duration_s": 1800}}

> The CURRENT residual is a steady -17.46 mV (first 5 s -17.52, last 5 s -18.03) at constant 25 A after 2400 s of history. Its std is 1.016 mV, the same as baseline (1.001), which rules out noise_growth. T_meas_mean is 300.625 K against 300.629 K in baseline, so the sensor reads as before and temp_sensor_bias is excluded. r0_increase would need r0_scale of about 1.25 (0.7 mOhm extra) to explain -17.5 mV. That would add about 0.4 W of heat and make the cell about 0.5-0.6 K hotter by t=2400 s, but the measured temperatures match within 0.004 K, so it is excluded. Two causes remain. An SOC offset of about -0.022 (17.5 mV / 0.8 V) gives a constant offset with no extra heat. A second RC branch with R2 of about 0.7 mOhm (tau 300 s, fully charged after 2400 s) gives the same constant offset and also adds no heat. These two cannot be told apart under constant current. A rest test separates them: an SOC offset keeps the residual at about -17.5 mV, while the RC branch's residual decays to 0 with tau = 300 s.

### 03b77d92 / claude-opus-5-5 / condition A / repeat 2

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['soc_offset', 'structural_change'], confidence=0.8, next_experiment={"name": "rest_test", "args": {"duration_s": 1800}}

> The CURRENT residual sits at a steady -17.46 mV (first 5 s -17.5, last 5 s -18.0) with standard deviation 1.016 mV, which matches baseline noise (1.001). So it is not no_change and not noise_growth. Measured temperature averages 300.625 K vs 300.629 K in baseline and matches the nominal thermal model. If R0 had risen, explaining -17.5 mV at 25 A would need r0_scale of about 1.25. The extra I^2R heat would raise T by about 0.5 K, which is not seen. A temperature sensor bias would need to be about +7.8 K (2.25 mV per K at 25 A), implying a true T below ambient, which is impossible. The two that remain give the same flat residual at constant current: an SOC offset of about -0.022 (17.5/800) or a second RC branch with R2 of about 0.7 mOhm (TAU2 = 300 s, fully settled by t = 2400 s). A rest test separates them: the v2 voltage decays to 0 with a 300 s time constant, while an SOC offset stays at about -17.5 mV.

### 09df166c / claude-opus-5-5 / condition A / repeat 0

- planted: structural_change; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['soc_offset', 'structural_change'], confidence=0.8, next_experiment={"name": "rest_test", "args": {"duration_s": 1800}}

> CURRENT residual over 2400-3000 s is a steady -12.34 mV with std 1.03 mV (first 5 s -12.81, last 5 s -12.46, so no drift). BASELINE was 0.03 +/- 1.00 mV. Noise growth and no change cannot give this mean. A temperature sensor bias would need about 5.5 K to produce it (2.25 mV/K), but measured temperature averages 300.615 K against 300.624 K in BASELINE under the same history, so it is ruled out. An R0 increase would need r0 about 18% higher; the extra ~0.3 W of heating would make the cell about 0.4 K warmer, which is not seen, so it is strongly disfavoured. A SOC offset of about -0.015 and an RC branch settled after 2400 s at 25 A (R2 about 0.49 mOhm) both give a constant offset under constant current. A rest test separates them: the RC branch makes the residual shrink with a 300 s time constant, while a SOC offset keeps it at about -12 mV.

### 09df166c / claude-opus-5-5 / condition A / repeat 1

- planted: structural_change; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['soc_offset', 'structural_change'], confidence=0.8, next_experiment={"name": "rest_test", "args": {"duration_s": 1800}}

> CURRENT residual is a constant -12.34 mV (std 1.03 mV vs baseline 1.00; first5 -12.81, last5 -12.46, no drift) at constant 25 A. noise_growth is ruled out because std is unchanged. temp_sensor_bias is ruled out: it would need about +5.5 K of sensor bias (2.25 mV/K at 25 A), but T_meas mean is 300.615 K vs baseline 300.624 K, and true T is set by physics from a trusted ambient. r0_increase is ruled out: it would need r0_scale of about 1.18, and the extra I^2*R heating would raise T by about 0.4 K (to about 301.0 K), which is not seen. Two causes remain. soc_offset with dSOC of about -0.0154 (0.8 V x 0.0154 = 12.3 mV) gives a constant offset. structural_change with R2 of about 0.49 mOhm also gives a constant offset, because v2 has reached steady state (tau2 = 300 s, which is much less than 2400 s). These two cannot be told apart at constant current. In a rest test, a soc offset stays at -12.3 mV, while the v2 contribution decays with tau of about 300 s.

