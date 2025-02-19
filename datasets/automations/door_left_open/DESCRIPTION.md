# Door left open

## Problem statement

Create an blueprint automation to play an alert on the speaker when the door is
left open.

## Example use cases

These are example use cases that could be used with the blueprint:

- Play an message on the living room speaker if the garage door has been left open for more than 30 minutes
- When the front door is ajar for 5 minutes, play a sound on the kitchen bluetooth speaker.

## Detailed Description

The blueprint should accept two inputs:

| Input           | Selector Type | Description                                                                           |
| --------------- | ------------- | ------------------------------------------------------------------------------------- |
| `door_sensor`   | `entity`      | A `binary_sensor` entity selector door sensor that is the target of the automation.   |
| `alert_media`   | `media`       | The target for the `media` selector for the media player and media id with the alter. |
| `open_duration` | `duration`    | A `duration` selector, the amount of time before playing the alert.                   |

The automation should play the selected media when the door has been open for the specified duration.
