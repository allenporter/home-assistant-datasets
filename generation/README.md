# Data Generation

This directory contains notebooks and seeds for generating the datasets.

The phases of generating data are currently:
- Generate a description of a Home ([notebook](homes.ipynb))
- Generate the Areas of the Home useful for automation ([notebook](areas.ipynb))
- Generate the devices in each area ([notebook](devices.ipynb))
- Generate interesting actions that can be used within the home ([notebook](actions.ipynb))
- Generate the subset of devices needed to evaluate the action
- Generate a list of possible things to consider when summariziing an area ([notebook](summaries.ipynb))
- Generate a list of anomalies in a home ([notebook](anomalies.ipynb))

There is a notebook for each phase, as well as seed data that is used for the
n-shot examples at that phase. The notebooks help drive feeding data from the
previous phase into the next phase. This flow makes it straight forward to
iterate and checkpoint at any particular phase.

The data is generated in a format that can be consumed by https://github.com/allenporter/home-assistant-synthetic-home

The next phase needed is to generate useful state data for triggering those actions.

### Notebook Development enviroment

This is an example of how to prepare the python venv for use with the jupyet notebooks:

1. Create the virtual environment

    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install --upgrade pip
    $ pip3 install -r requirements.txt
    ```

1. Open the notebook and select the venv interpreter and kernel
