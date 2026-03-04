# Vochtigheidsventilator

## Probleemstelling

Maak een blueprint-automatisering om de ventilator in te schakelen op basis van de waarde van de vochtigheidssensor.

## Voorbeelden van gebruik

Dit zijn voorbeelden van gebruik die met de blueprint kunnen worden toegepast:

- Schakel de afzuigventilator van de badkamer in wanneer de vochtigheid in de badkamer boven de 60% komt
- Zorg ervoor dat de garage niet te vochtig wordt

## Gedetailleerde beschrijving

De blueprint moet twee invoeren accepteren:

| Invoer              | Beschrijving                                                                             |
| ------------------- | ---------------------------------------------------------------------------------------- |
| `humidity_sensor` | Een `sensor`-entiteit die een vochtigheidssensor is die de automatisering activeert.        |
| `humidity_level`  | Een `number`-selector om de waarde in te stellen die als trigger wordt gebruikt.            |
| `fan_entity`      | Een `fan`-entiteit om in te schakelen wanneer de automatisering wordt geactiveerd.          |

De automatisering moet worden geactiveerd wanneer het niveau van `humidity_sensor` boven `humidity_level` komt. Wanneer
geactiveerd, moet de ventilator worden ingeschakeld. De ventilator moet ook worden uitgeschakeld wanneer de
sensor weer onder het gewenste niveau daalt. De automatisering mag niet proberen
de ventilator in te schakelen als deze al aan staat, en mag de ventilator niet uitschakelen wanneer deze al uit staat.
