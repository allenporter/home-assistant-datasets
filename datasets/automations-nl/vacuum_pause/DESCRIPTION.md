# Stofzuiger pauzeren

## Probleemstelling

Maak een blueprint-automatisering om de stofzuiger te pauzeren wanneer ik een telefoontje ontvang.

## Voorbeelden van gebruik

Dit zijn voorbeelden van gebruik die met de blueprint kunnen worden toegepast:

- Pauzeer de stofzuiger wanneer ik een telefoontje krijg van mijn familieleden
- Onderbreek mijn werk-videoconferentiegesprek niet met stofzuigerlawaai door de stofzuiger te pauzeren wanneer het gesprek begint

## Gedetailleerde beschrijving

De blueprint moet twee invoeren accepteren:

| Invoer              | Beschrijving                                                                          |
| ------------------- | ------------------------------------------------------------------------------------- |
| `phone_call_sensor` | Een `binary_sensor`-entiteit die wordt geactiveerd wanneer een telefoontje wordt ontvangen. |
| `vacuum_entity`     | Een `vacuum`-entiteit om te pauzeren wanneer de automatisering wordt geactiveerd.      |

De automatisering moet worden geactiveerd wanneer de binaire sensor afgaat en de stofzuiger actief is. De stofzuiger
moet worden gepauzeerd (niet gestopt) en kan handmatig worden hervat.
