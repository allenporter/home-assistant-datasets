# Humidity Fan

## Problem statement

Create a blueprint automation to turn on the fan based on the value of the humidity sensor.

## Example use cases

These are example use cases that could be used with the blueprint:

- Turn on the bathroom exhaust fan when the bathroom humidty is above 60%
- Make sure the garage does not get too humid

## Detailed Description

The blueprint should accept two inputs:

| Input               | Description                                                           |
| ------------------- | --------------------------------------------------------------------- |
| `humidity_sensor` | A `sensor` entity that is a humidty sensor that triggers the automation. |
| `humidity_level` | A `number` selector to set the value used as the trigger. |
| `fan_entity`     | A `fan` entity to turn on when the automation fires. |

The automation should trigger when the `humidity_sensor` level goes above `humidity_level`. When
triggered, the fan should be turned off. The fan should also be stopped when the
sensor goes back down below the desired level. The automation should not try to
turn the fan on if it is already on, and should not turn the fan off when it is
already off.
