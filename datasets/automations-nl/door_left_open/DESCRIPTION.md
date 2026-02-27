# Deur open laten staan

## Probleemstelling

Maak een blueprint-automatisering om een waarschuwing af te spelen op de speaker wanneer de deur open is blijven staan.

## Voorbeelden van gebruik

Dit zijn voorbeelden van gebruik die met de blueprint kunnen worden toegepast:

- Speel een bericht af op de woonkamerspeaker als de garagedeur langer dan 30 minuten open heeft gestaan
- Wanneer de voordeur 5 minuten op een kier staat, speel een geluid af op de bluetooth-speaker in de keuken.

## Gedetailleerde beschrijving

De blueprint moet twee invoeren accepteren:

| Invoer          | Selectortype | Beschrijving                                                                                      |
| --------------- | ------------ | ------------------------------------------------------------------------------------------------- |
| `door_sensor`   | `entity`     | Een `binary_sensor` entiteitsselector deursensor die het doel is van de automatisering.            |
| `alert_media`   | `media`      | Het doel voor de `media`-selector voor de mediaspeler en media-id met de waarschuwing.             |
| `open_duration` | `duration`   | Een `duration`-selector, de hoeveelheid tijd voordat de waarschuwing wordt afgespeeld.             |

De automatisering moet het geselecteerde medium afspelen wanneer de deur gedurende de opgegeven tijd open heeft gestaan.
