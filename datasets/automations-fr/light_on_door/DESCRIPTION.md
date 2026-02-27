# Lumiere a l'ouverture de la porte

## Enonce du probleme

Creez une automatisation blueprint pour allumer une lumiere lorsque la porte s'ouvre.

## Exemples d'utilisation

Voici des exemples d'utilisation qui pourraient etre utilises avec le blueprint :

- Allumer la lumiere du garde-manger lorsque la porte du garde-manger s'ouvre

## Description detaillee

Le blueprint doit accepter deux entrees :

| Entree         | Description                                                                                          |
| -------------- | ---------------------------------------------------------------------------------------------------- |
| `door_sensor`  | Un `binary_sensor` qui declenche le demarrage de l'automatisation.                                   |
| `light_switch` | Une ou plusieurs entites `light` cibles a allumer ou eteindre lorsque l'automatisation se declenche. |

L'automatisation doit se declencher lorsque la porte s'ouvre et allumer la lumiere. La
lumiere doit s'eteindre lorsque la porte se ferme ou apres un delai de 2 minutes.
