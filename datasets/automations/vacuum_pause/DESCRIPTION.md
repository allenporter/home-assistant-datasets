# Vacuum Pause

## Problem statement

Create a blueprint automation to pause the vacuum when I receive a phone call.

## Example use cases

These are example use cases that could be used with the blueprint:

- Pause the vacuum when I get a phone call from my relatives
- Don't interrupt my work video convererence call with vacuum noise by pausing it when the call starts

## Detailed Description

The blueprint should accept two inputs:

| Input               | Description                                                           |
| ------------------- | --------------------------------------------------------------------- |
| `phone_call_sensor` | A `binary_sensor` entity that triggers when a phone call is received. |
| `vacuum_entity`     | A `vacuum` entity to pause when the automation fires.                 |

The automation should trigger when the binary sensor fires and the vacuum is running. The vacuum
should be paused (not stopped) and can be resumed manually.
