# Licht aan bij deur openen

## Probleemstelling

Maak een blueprint-automatisering om een licht in te schakelen wanneer de deur opengaat.

## Voorbeelden van gebruik

Dit zijn voorbeelden van gebruik die met de blueprint kunnen worden toegepast:

- Schakel het voorraadkastlicht in wanneer de voorraadkastdeur opengaat

## Gedetailleerde beschrijving

De blueprint moet twee invoeren accepteren:

| Invoer         | Beschrijving                                                                                      |
| -------------- | ------------------------------------------------------------------------------------------------- |
| `door_sensor`  | Een `binary_sensor` die de automatisering activeert.                                              |
| `light_switch` | Een of meer `light`-entiteiten als doel om in of uit te schakelen wanneer de automatisering wordt geactiveerd. |

De automatisering moet worden geactiveerd wanneer de deur opengaat en het licht inschakelen. Het
licht moet worden uitgeschakeld wanneer de deur sluit of na een time-out van 2 minuten.
