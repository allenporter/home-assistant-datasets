# home-assistant-datasets

A collection of datasets for evaluation (and in the future training) home automation
AI models.

## Datasets

See the [datasets README](datasets/README.md) for details on the available
datasets including Home descriptions, Area descriptions, Device descriptions
and summaries that can be performed on a home.

The device level datasets are defined using the [Synthetic Home](https://github.com/allenporter/home-assistant-synthetic-home/)
format including its device registry of synthetic devices.

## Synthetic Data Generation

See the [generation README](generation/README.md) for more details on how synthetic
data generation using LLMs works. The data is generated from a small amount of seed
example data and a prompt, then is persisted.

## Notebook Development enviroment

This is an example of how to prepare the python venv for use with the jupyet notebooks:

1. Create the virtual environment

    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install --upgrade pip
    $ pip3 install -r requirements.txt
    ```

1. Clone the https://github.com/marcelveldt/python-hass-client repo locally and install `pip3 install -e .`

1. Open the notebook and select the venv interpreter and kernel
