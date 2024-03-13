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

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/cus
tom_components/"
$ pip3 install -r ../home-assistant-synthetic-home/requirements.txt
$ python3 -m script.eval --config datasets/summaries/home1-us.yaml --output_dir="/tmp/2024-03-10/"
```

### Create users

TODO: Determine if this is needed
```
$ hass -c /tmp/2024-03-10/ --script auth add allen example-pass
Auth created
$ hass -c /tmp/2024-03-10/ --script auth list
allen

Total users: 1
```

### Configure the model

- Add a config entry for Open AI
- Set a prompt to summarize an area
- Could/should this be a pre-canned config entry that we just write as a .json file?

### Run an LLM Summary service call

- Collect area state
- Stick data into the prompt
- Record the results

### Human Evaluation

- Manually review all the answers
- Record the score (1, 2, 3)
- Gather statistics on the results
