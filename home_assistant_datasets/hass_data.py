"""A home assistant client library wrapper.

This is deprecated and can be replaced by the synthetic home inventory
collection tools.
"""

from dataclasses import dataclass
import hass_client
from hass_client.models import Area, Device, Entity, State

URL_FORMAT = "wss://{hostport}/api/websocket"


async def create_client(hostport: str, api_token: str) -> hass_client.HomeAssistantClient:
    """Create a new home assistant client."""
    client = hass_client.HomeAssistantClient(
        URL_FORMAT.format(hostport=hostport), api_token
    )
    await client.connect()
    if not client.connected:
        raise ValueError("Failed to connect to home assistant")
    return client


@dataclass
class Home:
    """A home assistant data wrapper."""
    areas: list[Area]
    devices: list[Device]
    entities: list[Entity]
    states: list[State]

    def devices_by_area(self, area_id: str) -> list[Device]:
        """Get all devices in an area."""
        return [device for device in self.devices if device['area_id'] == area_id]

    def entities_by_device_id(self, device_id: str) -> list[Entity]:
        """Get all entities for a device."""
        entities = []
        for entity in self.entities:
            if entity['device_id'] != device_id:
                continue
            if entity['disabled_by'] is not None or entity['hidden_by'] is not None:
                continue
            if entity['entity_category'] is not None:
                continue
            entities.append(entity)
        return entities

    def entities_by_area(self, area_id: str) -> list[Entity]:
        return [
            entity
            for device in self.devices_by_area(area_id)
            for entity in self.entities_by_device_id(device['id'])
        ]

    def get_state(self, entity_id: str) -> State | None:
        """Get the state for an entity."""
        for state in self.states:
            if state['entity_id'] == entity_id:
                return state
        return None


async def get_home(client: hass_client.HomeAssistantClient) -> Home:
    """Get the home assistant data."""
    devices: list[Device] = await client.get_device_registry()
    entities: list[Entity] = await client.get_entity_registry()
    states: list[State] = await client.get_states()
    areas: list[Area] = await client.get_area_registry()
    return Home(areas, devices, entities, states)
