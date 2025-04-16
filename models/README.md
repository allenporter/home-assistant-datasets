# Models

This directory contains the model configuration files used by
`home-assistant-datasets` for running evaluations. Each file is essentially a
Home Assistant `ConfigEntry` that configures a specific model type with whatever
integration is needed (either core integration or custom component).

Some models require secrets such as API keys or urls that are specific to you
and not checked into the repository and referenced in this file like `!secret openai_api_key`.
Create a file called `secrets.yaml` and include the necessary keys.
