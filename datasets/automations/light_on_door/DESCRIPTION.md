# Light on door

## Problem statement

Create an blueprint automation to turn on a light when the door opens.

## Example use cases

These are example use cases that could be used with the blueprint:

- Turn on the pantry light when the pantry door opens

## Detailed Description

The blueprint should accept two inputs:

| Input          | Description                                                                     |
| -------------- | ------------------------------------------------------------------------------- |
| `door_sensor`  | A `binary_sensor` that triggers the automation to start.                        |
| `light_switch` | One or more `light` entity targets to turn on or off when the automation fires. |

The automation should trigger when the door opens, and turn the light on. The
light should be shut off when the door closes or after a 2 minute timeout.
