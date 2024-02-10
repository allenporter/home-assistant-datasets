"""A tool to collect data grouped by areas from Home Assistant.


This tool is used to collect data from a live Home Assistant instance which
can be used to understand how to better create other datasets.

This is effectively a CLI version of the `area-summary.ipynb` notebook so
that it can be run easily to collect data at different times of day, and
expand to do more complex modification of the data.
"""

import asyncio

import hass_client
import logging

from home_assistant_datasets.secrets import get_secret
from home_assistant_datasets import hass_data
from home_assistant_datasets import model_client


async def start() -> None:
    logging.basicConfig(level=logging.INFO)
    secrets = get_secret("hostport")
    client: hass_client.HomeAssistantClient = await hass_data.create_client(
        get_secret("hostport"), get_secret("hass_token")
    )

    home: hass_data.Home = await hass_data.get_home(client)

    for area in home.areas:
        area_id = area['area_id']
        entities = home.entities_by_area(area_id)
        if not entities:
            continue

        print(f"Area: {area['name']}")
        for entity in entities:
            entity_name = entity['entity_id']
            state = home.get_state(entity_name)
            attributes = state['attributes']
            friendly_name = attributes.get('friendly_name')

            state_value = state['state']
            if unit_of_measurement := attributes.get('unit_of_measurement'):
                state_value = f"{state_value} {unit_of_measurement}"

            print(f"    {friendly_name} ({entity_name}): {state_value}")

    await client.disconnect()


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
