# Pause de l'aspirateur

## Enonce du probleme

Creez une automatisation blueprint pour mettre en pause l'aspirateur lorsque je recois un appel telephonique.

## Exemples d'utilisation

Voici des exemples d'utilisation qui pourraient etre utilises avec le blueprint :

- Mettre en pause l'aspirateur lorsque je recois un appel de ma famille
- Ne pas interrompre ma videoconference de travail avec le bruit de l'aspirateur en le mettant en pause lorsque l'appel commence

## Description detaillee

Le blueprint doit accepter deux entrees :

| Entree              | Description                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------- |
| `phone_call_sensor` | Une entite `binary_sensor` qui se declenche lorsqu'un appel telephonique est recu.       |
| `vacuum_entity`     | Une entite `vacuum` a mettre en pause lorsque l'automatisation se declenche.             |

L'automatisation doit se declencher lorsque le capteur binaire se declenche et que l'aspirateur est en fonctionnement. L'aspirateur
doit etre mis en pause (pas arrete) et peut etre repris manuellement.
