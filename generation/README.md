# Data Generation

This directory contains notebooks and seeds for generating the datasets.

The phases of generating data are currently:
- Generate a description of a Home
- Generate the Areas of the Home useful for automation
- Generate the devices in each area
- Generate interesting actions that can be used with the Home
- Generate the subset of devices needed to evaluate the action

There is a notebook for each phase, as well as seed data that is used for the
n-shot examples at that phase. The notebooks help drive feeding data from the
previous phase into the next phase. This flow makes it straight forward to 
iterate and checkpoint at any particular phase.

The data is generated in a format that can be consumed by https://github.com/allenporter/home-assistant-synthetic-home

The next phase needed is to generate useful state data for triggering those actions.
