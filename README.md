# Awesome Task Exchange System

## Event Storming

![Event Storming Result](event-storming.drawio.svg "Event Storming Result")

## Data Model

![Data Model](data-model.drawio.svg "Data Model")

## Services

* Auth - User authentication and management;
* Task Tracker;
* Accounting;
* Analytics.

## Service Communications

![Communications](communications.drawio.svg "Communication")

## Kafka Topic Naming Convention

Business topics are named after the root entities of the business events
(e.g. `tasks`).
Streaming topics are named after the streamed entities with addition of
`-stream` suffix (e.g. `tasks-stream`).
