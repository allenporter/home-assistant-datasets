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
