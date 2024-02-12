# Datasets

This directory contains synthetic data used for generating home information.

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
to create from the data generation step:
```
---
- name: Home3
  thoughts:
  - Being a farmhouse in a rural area with a barn workshop suggests a rustic and traditional
    lifestyle.
  - The large backyard with fruit trees may benefit from smart irrigation systems
    or garden lights.
  - The kitchen and dining area may have smart appliances like a smart oven or refrigerator.
  desc: Farmhouse in rural area in Brandenburg, Germany
  area_devices:
    Kitchen:
    - light
    - smart_oven
    - smart_fridge
    Dining Area:
    - light
    Bedroom 1:
    - light
    Bedroom 2:
    - light
    Bedroom 3:
    - light
    Workshop:
    - smart_tools
    Backyard:
    - irrigation_system
    - garden_lights
```
