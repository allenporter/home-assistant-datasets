# Datasets

This directory contains synthetic data used for generating home information.
The datasets in this repository are generated using the notebooks and seeds in
the `../generation` directory.

## Homes

Home data is generated using the `synthetic-home` notebook. These homes are
used as a basis to generate other downstream data such as areas, devices,
entities, and values.

Example data:

```
homes:
  - name: "Cozy Cottage"
    country_code: "US"
    location: "Rural area in Maine"
    type: "Single-family house"
    amenities:
      - 2 bedrooms
      - 1 bathroom
      - Open concept living room and kitchen
      - Front porch with swing
      - Fire pit in the backyard
      - Detached garage
```

## Area devices

This is created by reading the homes data and creating areas and devices for the
home. See `synthetic-devices` notebook.

The data is a single yaml file with many documents in it (since that was easier)
to create from the data generation step. The dataset contains the chain of
thought used to create the areas and devices.
```
---
...
areas:
  thoughts:
  - The house is in a suburban neighborhood in Munich, so the climate may vary throughout
    the year.
  - The front yard with a vegetable garden suggests possible smart irrigation for
    plants.
  - With 4 bedrooms, there may be multiple family members living in the house.
  - The detached garage may have a smart garage door opener.
  - The kitchen with a breakfast nook could benefit from smart lighting for various
    uses.
  area_devices:
    Living Room:
    - light
    - thermostat
    - smart_tv
    Kitchen:
    - light
    - smart_light
    - smart_speaker
    Dining Area:
    - light
    - smart_light
    - smart_speaker
    Master Bedroom:
    - light
    - smart_tv
    Bedroom 2:
    - light
    - smart_speaker
    Front Yard:
    - light
    - sprinkler
    Garage:
    - cover
    - light
  other_devices:
  - smartphone
  - tablet
  - laptop
```

## Entities

The entities are created by `synthetic-device-entities` based on the devices,
with an additional dictonary for storing the entity information for each device.
The area information is repeated to make it easier to access.
```
device_entities:
- Living Room:
  - name: light
    entities:
    - light.living_room
  - name: thermostat
    entities:
    - climate.living_room
    - sensor.living_room_temperature
    - sensor.living_room_humidity
  - name: smart_tv
    entities:
    - media_player.living_room
- Kitchen:
  - name: light
    entities:
    - light.kitchen
  - name: smart_light
    entities:
    - light.kitchen_counter
    - light.kitchen_island
  - name: smart_speaker
    entities:
    - media_player.kitchen
- Dining Area:
  - name: light
    entities:
    - light.dining_area
  - name: smart_light
    entities:
    - light.dining_area_chandelier
  - name: smart_speaker
    entities:
    - media_player.dining_area
- Master Bedroom:
  - name: light
    entities:
    - light.master_bedroom
  - name: smart_tv
    entities:
    - media_player.master_bedroom_tv
    - remote.master_bedroom_tv
    - binary_sensor.master_bedroom_tv_headphones_connected
- Bedroom 2:
  - name: light
    entities:
    - light.bedroom_2
  - name: smart_speaker
    entities:
    - media_player.bedroom_2
- Front Yard:
  - name: light
    entities:
    - light.front_yard
  - name: sprinkler
    entities:
    - switch.front_yard_sprinkler
- Garage:
  - name: cover
    entities:
    - cover.garage_door
  - name: light
    entities:
    - light.garage
- Other:
  - name: smartphone
    entities:
    - device_tracker.iphone
  - name: tablet
    entities:
    - device_tracker.tablet
  - name: laptop
    entities:
    - device_tracker.laptop
```

## Actions

Synthetic actions for a home are created with `synthetic-actions` and appended
to the home record. The instructions are to generate actions that may or
may not be valid for the particular home.

```
actions:
- Summarize the current temperature and humidity levels in the living room
- Evaluate the energy usage in the home over the past week
- Turn on the air purifier in the bedroom if the air quality is poor
- Notify the user if the front door has been left open for more than 10 minutes
- Determine if any lights have been left on when the last person left the home
- Set the thermostat to an energy-saving mode when the home is unoccupied
- Notify the user if the refrigerator door has been open for an extended period
- Evaluate the water usage in the home during the last month
- Turn off all electronic devices in the home before bedtime
- Notify the user if the smart oven has finished preheating
- Determine if the garage door is closed when the last person leaves the home
- Evaluate the performance of the smart sprinkler system based on recent watering
  schedules
- Notify the user if the smart smoke detector detects smoke or fire
- Set the smart blinds to open at sunrise and close at sunset
- Determine if the smart security camera has detected any motion in the backyard
- Evaluate the performance of the smart thermostat in maintaining a comfortable temperature
- Notify the user if the smart speaker detects unusual sounds in the home
- Turn off the bathroom lights automatically if they have been left on for more than
  30 minutes
- Determine if the smart TV has been left on while nobody is in the living room
- Evaluate the energy efficiency of the smart dishwasher based on usage patterns
```
