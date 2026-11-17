# Análisis de las categorías de mora

Equipo 6 Juan Pablo Cañas Sepúlveda, Daniela Alzate Echavarria, Tania C Obando Suarez

## Brief v1

| Campo | Respuesta |
|---|---|
| Usuario y decisión | |
| Pregunta | ¿Qué entidad financiera presenta la mayor cantidad de clientes en mora en cada categoría de calificación de riesgo y cómo se comporta esta distribución frente a las demás entidades? |
| Fuente con API | https://www.datos.gov.co/resource/rvii-eis8.json?$limit=5 |
| Qué representa una fila | Presenta el saldo mensual de cartera por entidad, modalidad, producto, altura de mora y calificación de riesgo. |
| Campo que la identifica | CODIGO_ENTIDAD, NOMBRE DE LA ENTIDAD, CALIFICACIÓN DE RIESGO |
| Cada cuánto se actualiza | Mensualmente |
| Dato a confirmar | Transformar los datos a su tipo correspondiente. |
| Tres indicadores | 1. Cantidad de clientes morosos por calificación de riesgo. · 2. Participación de cada calificación dentro de los clientes morosos del banco. · 3. Saldo de cartera morosa por calificación de riesgo. |
| Terminó bien si… | Se logra comparar la calificación de riesgo de cada banco para diferentes perfiles de clientes. |
| No vamos a construir | No vamos a identificar qué factores influyen en la calificación de riesgo de los bancos. |

## Contrato de datos

- Una fila es:
- La identifica:
- Si llega una fila repetida:
- Si falta un campo:

## Bitácora de decisiones

| Fecha | Decisión | Por qué |
|---|---|---|
| | | |

## Reglas del repositorio

- Es público: nada de datos personales, contraseñas, tokens ni llaves.
- Las credenciales van en un archivo `.env`, que Git ignora (ver `.gitignore`). `.env.example` muestra qué variables hacen falta, sin valores.
- Cada commit explica en su mensaje qué se decidió y por qué.
