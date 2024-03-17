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

This will setup the home, complete onboarding, and create the synthetic devices.

Prepare the environment
```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
$ pip3 install -r ../home-assistant-synthetic-home/requirements.txt
```

```
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/custom_components/:${PWD}/../home-assistant-synthetic-home/"
$ OUTPUT_DIR="/tmp/2024-03-10/"
$ python3 -m script.eval --config datasets/summaries/home1-us.yaml --output_dir="${OUTPUT_DIR}" create_config
```

### Create users

This step will create a test user.
```
$ hass --script auth -c "${OUTPUT_DIR}/config" add ${USER} example-pass
Auth created
$ hass --script auth -c "${OUTPUT_DIR}/config" list
allen

Total users: 1
```

### Manually configure the conversation agent

This is currently done manually. Run Home Assistant and set up the configuration
you would like to evaluate.
```
$ hass  -c "${OUTPUT_DIR}/config"
```

Later we can either automate these steps, or reverse the order: First setup the
conversation agent, then setup the synthetic devices for different scenarios.

Make sure to remove the default prompt, if any, that is configured for the model if
using a normal conversation agent.

### Run an LLM Summary service call

```
$ python3 -m script.eval --config datasets/summaries/home1-us.yaml --output_dir="/tmp/2024-03-10/" eval
```

- Collect area state
- Stick data into the prompt
- Record the results

### Human Evaluation

- Manually review all the answers
- Record the score (1, 2, 3)
- Gather statistics on the results
