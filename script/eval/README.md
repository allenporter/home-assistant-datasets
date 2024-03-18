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


### Seed the devices in the Home

This will setup the home, complete onboarding, and create the synthetic devices
using the [Synthetic Home integration](https://github.com/allenporter/home-assistant-synthetic-home/).

Prepare the environment
```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
$ pip3 install -r ../home-assistant-synthetic-home/requirements.txt
```

Create a new Home Assistant configuration:
```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/custom_components/:${PWD}/../home-assistant-synthetic-home/"
$ OUTPUT_DIR="/tmp/2024-03-10/"
$ python3 -m script.eval  --output_dir="${OUTPUT_DIR}" create_config --config datasets/summaries/home1-us.yaml
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


### Create users

This step will create a test user taht you can use when manually logging in in the next step.
```bash
$ hass --script auth -c "${OUTPUT_DIR}/config" add ${USER} example-pass
Auth created
$ hass --script auth -c "${OUTPUT_DIR}/config" list
allen

Total users: 1
```

This step should not be needed in the future when automating integration setup.

### Manually configure the conversation agent

This is currently done manually. Run Home Assistant and set up the configuration,
prompt, etc you would like to evaluate.
```bash
$ hass -c "${OUTPUT_DIR}/config"
```

Later we can either automate these steps, or reverse the order: First setup the
conversation agent, then setup the synthetic devices for different scenarios.

Make sure to update the default prompt and that is configured for the model if
using a normal conversation agent.

Get the conversation agent ID:
```bash
$ cat "${OUTPUT_DIR}/config/.storage/core.config_entries"  | jq -c '.data.entries[] | [.
entry_id, .title]'
```

Will have the following output:
```json
["efaf1150ad0c1b30d3dce673cec1c096","Synthetic Home"]
["00d640128da43b46a94eda6d094efd64","Sun"]
["c6fe47c341a1c257139ea1e4ea22d342","OpenAI Conversation"]
```

### Run Data Collection

This runs an eval of the "Area Summary" conversation agent. This will evaluate the "Answer summary"
agent and create output files in the output directory under `eval/`

```bash
$ AGENT_ID=b46636a2b78f3b7068ccffd10d500f99
$ python3 -m script.eval --output_dir="${OUTPUT_DIR}" eval --agent_id="${AGENT_ID}" --eval_config_file=script/eval/eval_config.yaml
...
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████| 9/9 [00:16<00:00,  1.79s/it]
$ ls -l -R ${OUTPUT_DIR}/eval/
/tmp/2024-03-10//eval/1710727690:
backyard.yaml  bedroom-1.yaml  bedroom-2.yaml  bedroom-3.yaml  game-room.yaml  garage.yaml  kitchen.yaml  living-room.yaml  master-bedroom.yaml
```

### Human Evaluation

You can now manually review the output of data collection:

```bash
$ cat /tmp/2024-03-10//eval/1710727690/*.yaml | head -11
```

Each area has its own file that contains the instructions and the LLM response in the `response` field:
```yaml
area: Backyard
instructions:
- Ensure that the Deck Lights in the Backyard are operational
- Verify if the Outdoor Camera in the Backyard is detecting motion accurately
response: The Deck Lights in the backyard are off, and the Outdoor Camera is not detecting
  any motion.
area: Bedroom 1
instructions:
- Determine if the Bedroom 1 Light is on or off
- Check if the Smart Lock in Bedroom 1 is locked properly
response: The bedroom is secure with the light off and the smart lock properly locked.
```


In the future we want to:
- Record the score (1, 2, 3)
- Gather statistics on the results
- Support many more homes and devices at once
