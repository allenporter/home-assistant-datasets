## Evaluation

This tool is meant to evaluate a Home Automation. The initial target is an
end-to-end feature evaluation that requires human evaluation, and is not
automated or a low level evaluation. This will be evolved as more evaluation
use cases are added to keep it simple.

## Summary evaluation

This is the initial baseline use case:

- Seed the devices in the home (with default state)
- Pick a model and a prompt
- For each summary task:
  - Run the LLM summary
  - Record the summary response
- Human rater (me) scores the result quality:
  - 1: Low: Bad, incorrect, misleading, etc.
  - 2: Medium: Solid, not incorrect, though perhaps a missed opportunity
  - 3: High: Good

### Running an eval

1. Configure any paths to custom components

```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/custom_components/:${PWD}/../home-assistant-synthetic-home/"
```

1. Create an the evaluation directory. The directory needs to contain `eval_config.yaml` and an `eval.py` . See [evals/area_summary](evals/area_summary/) for an example.

1. Run the evaluation

```
$ python3 -m script.eval --eval_dir evals/area_summary
WARNING:homeassistant.loader:We found a custom integration synthetic_home which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you experience issues with Home Assistant
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 9/9 [00:07<00:00,  1.14it/s]
```

1. View the results in `evals/area_summary`

```bash
$ cat evals/area_summary/out/*.yaml | head -11
```

Each area has its own file that contains the instructions and the LLM response in the `response` field:
```yaml
area: Backyard
response: In the backyard, there are Deck Lights which are outdoor smart string lights
  and an Outdoor Camera which is the Spotlight Cam Battery. These devices help provide
  lighting and security in the backyard area.
area: Bedroom 1
response: In Bedroom 1, you have a Dimmable Smart Bulb for lighting and a Encode Smart
  WiFi Deadbolt for smart lock security.
area: Bedroom 2
response: In Bedroom 2, you have a warm glow bulb and a climate sensor (smart temperature
  sensor) installed. The warm glow bulb provides a cozy and inviting atmosphere, while
  the climate sensor helps you monitor the temperature in the room. This area is designed
```

1. Rate the results (not yet managed)


### Seed the devices in the Home

The above example will run Home Assistant, will setup the home, complete onboarding, and create the synthetic devices
using the [Synthetic Home integration](https://github.com/allenporter/home-assistant-synthetic-home/).

You can run the evaluation with --no-delete_tmpdir and inspect the state of the created Home.

```bash
# Get the temprary dir from the script.eval
$ OUTPUT_DIR=/tmp/homeassistant-evalrqdy3axl
```

Verify synthetic areas were created properly:
```bash
$ cat "${OUTPUT_DIR}/config/.storage/core.area_registry" | jq '.data.areas[].name' | head -5
```
Will output:
```json
"Kitchen"
"Living Room"
"Game Room"
"Backyard"
"Garage"
```

Verify synthetic devices were created properly:
```bash
$ cat "${OUTPUT_DIR}/config/.storage/core.device_registry" | jq '.data.devices[].name' | head -5
```
Will output:
```json
"Kitchen Light"
"Refrigerator"
"Living Room Light"
"Smart Speaker"
"Game Room Light"
```

The devices currently have a default state, but can be updated with [Restorable Attributes](https://github.com/allenporter/home-assistant-synthetic-home/?tab=readme-ov-file#restorable-attributes-using-service-calls)
configured by the [Synthetic Home integration](https://github.com/allenporter/home-assistant-synthetic-home/).


### Human Evaluation

In the future we want to:
- Record the score (1, 2, 3)
- Gather statistics on the results
- Support many more homes and devices at once
