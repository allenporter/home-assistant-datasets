# Mini Evaluation dataset for Home Assistant assist actions

This is a variation on the `assist` dataset that tests far fewer entities, devices,
and areas at once. This is designed given poor performance of local models on the
`assist` baseline to help with even smaller tasks to get right.

This is a dataset for the Home Assistant LLM API ([blog post](https://developers.home-assistant.io/blog/2024/05/20/llm-api/)).

See the `home-assistant-datasets assist` command for more details on how to
run evaluations.

See [../assist/README.md](../assist/README.md) for details on how the dataset
is configured including the inventory fixtures, and the eval tasks.
