# Examples

## Overclaim

### 03b77d92 / mock_always_claim / condition A / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 03b77d92 / mock_always_claim / condition B / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 09df166c / mock_always_claim / condition A / repeat 0

- planted: structural_change; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 09df166c / mock_always_claim / condition B / repeat 0

- planted: structural_change; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

### 0ecf604c / mock_always_claim / condition A / repeat 0

- planted: structural_change; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=identified, cause=r0_increase, candidates=['r0_increase'], confidence=1.0, next_experiment={"name": "none", "args": {}}

> mock: always claims r0_increase

## Correct abstention

### 03b77d92 / mock_always_abstain / condition A / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['r0_increase', 'soc_offset', 'temp_sensor_bias', 'structural_change'], confidence=0.5, next_experiment={"name": "rest_test", "args": {"duration_s": 5400}}

> mock: always abstains

### 03b77d92 / mock_oracle / condition A / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['soc_offset', 'structural_change'], confidence=1.0, next_experiment={"name": "pulse_test", "args": {"amplitude_a": 10.0, "duration_s": 30.0}}

> mock: read from the private file

### 03b77d92 / mock_random_experiment / condition A / repeat 0

- planted: soc_offset; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['r0_increase', 'soc_offset', 'temp_sensor_bias', 'structural_change'], confidence=0.5, next_experiment={"name": "cc_run", "args": {"current_a": 5, "duration_s": 600}}

> mock: abstains and picks a random experiment

### 09df166c / mock_always_abstain / condition A / repeat 0

- planted: structural_change; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['r0_increase', 'soc_offset', 'temp_sensor_bias', 'structural_change'], confidence=0.5, next_experiment={"name": "rest_test", "args": {"duration_s": 5400}}

> mock: always abstains

### 09df166c / mock_oracle / condition A / repeat 0

- planted: structural_change; oracle set after the agent's data: {soc_offset, structural_change}
- answer: verdict=not_identifiable, cause=None, candidates=['soc_offset', 'structural_change'], confidence=1.0, next_experiment={"name": "pulse_test", "args": {"amplitude_a": 10.0, "duration_s": 30.0}}

> mock: read from the private file

