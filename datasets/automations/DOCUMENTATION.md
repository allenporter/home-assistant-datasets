# About blueprints

From https://www.home-assistant.io/docs/blueprint/

## What is a blueprint?

A blueprint is a script, automation or template entity configuration with certain
parts marked as configurable. This allows you to create different scripts,
automations or template entities based on the same blueprint.

Imagine you want to control lights based on motion. A blueprint provides the
generic automation framework, while letting you select one specific motion sensor
as a trigger, and the exact light to control. This blueprint makes it possible
to create two automations. Each automation has their own configuration and act
completely independently. Yet, they share some basic automation configuration
so that you do not have to set this up every time.

Automations inherit from blueprints, which means that changes made to a blueprint
will be reflected in all automations based on that blueprint the next time the
automations are reloaded. This occurs as part of Home Assistant starting. To
manually reload the automations, go to Developer tools > YAML and reload the
automations.

Blueprints are shared by the community in the blueprint community forum.
