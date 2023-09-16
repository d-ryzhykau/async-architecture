# Awesome Task Exchange System

After analyzing the requirements, the following domains have been identified:

* Tasks - task management;
* Finance - financial transaction management, financial analytics calculation;
* Auth - user management, authentication.

Each subject area has a set of closely related operations and data.
Additionally, different subject areas have different business priorities:

* Tasks - the main subject area with the highest priority for development;
* Finance - supporting the main subject area;
* Auth - a non-specialized area, where a ready-made solution can be used (e.g., Keycloak).

It is expected that Tasks will be used by the development team, and Finance will
be used by the accounting team. These teams have different business processes
and lifecycles. It would be useful to have the ability to deploy changes to
different business processes independently of each other.

Each subject area should be represented by a separate service.
The names of the services match the names of the subject areas.

## Communications

### Synchronous

To retrieve data from one service to another service during the processing of
commands and events, client services can use each other's REST APIs.

REST APIs of the services are only available to holders of machine-to-machine
tokens to prevent unauthorized access to the data.

### Asynchronous

For events that may be of interest to other services and their subject areas,
services should publish messages describing events.

RabbitMQ will be used for message exchange; it provides everything necessary to
implement the required system, and I have experience working with it.

Each type of event should have a separate key (`routing_key`). Message keys
should have the following format:

```text
<service_name>.<entity_name>.<event_name>
```

## Services

### Tasks

The service should provide all the functionality of the task tracker dashboard:

* Displaying a list of tasks (including those assigned to the current user);
* Creating tasks;
* Marking tasks as completed;
* Assigning task performers.

The service should store tasks with descriptions and links to the assignees.

Additionally, the service should support a local cache of active system users
to speed up the selection of a random task performer and display their data.

#### Outgoing Messages

`tasks.task.assigned` - a new performer has been selected for the task
(including for a new task).

```jsonc
{
  "task_uuid": "uuid", // Task UUID
  "assigned_to": "uuid", // Performer's UUID
  "timestamp": "ISO 8601 Datetime" // Assignment time
}
```

`tasks.task.completed` - the task has been marked as completed.

```jsonc
{
  "task_uuid": "uuid",
  "assigned_to": "uuid", // UUID of the last task performer
  "timestamp": "ISO 8601 Datetime" // Completion time
}
```

`tasks.task.changed` - the task description has changed (including for a new task).

```jsonc
{
  "task_uuid": "uuid",
  "timestamp": "ISO 8601 Datetime" // Update time
}
```

#### Incoming Messages

`auth.user.created`, `auth.user.changed` - adding or updating user data in the
service database. If the event timestamp is earlier than the timestamp of the
user's last update in the service database, the event is ignored. User data is
retrieved through the `GET /users/{uuid}` endpoint of the Auth service. If a
user's role changes to a role incompatible with task execution (e.g., manager
or administrator), the user's tasks are reassigned to someone with a suitable
task-execution role.

`auth.user.deleted` - removal of a user from the local cache.
Tasks of the deleted user are reassigned to users with suitable roles.

To properly handle `auth.user.changed` and `auth.user.deleted` events in the
absence of processing order guarantees, users in the cache should not be
physically deleted but marked as deleted using a flag (e.g., `is_deleted`).
This way, `changed` events after "deletion" can be ignored, and no records need
to be created for deleted users.

#### REST API

`GET /tasks/{uuid}` - obtaining task data.

### Finance

The service is responsible for financial operations:

* Setting prices for tasks;
* Logging financial transactions;
* Displaying an employee's account balance;
* Sending daily emails with payout sums to employees;
* Calculating earnings for top management per day;
* Providing analytical data by days.

The service should store the history of funds deposited for task completion and
deductions for task reassignment for each employee. At the end of each working
day, a record of payment and, accordingly, balance reset is created for
employees with a positive balance.

Based on the history of funds deposited into the performers' accounts, an
analytics dashboard can be built. To minimize the load of analytical queries,
their results can be cached. The cache needs to be invalidated or updated when
necessary, as in the case of earnings sum, which should be updated when creating
new records. The cache can also be invalidated based on time.

Additionally, the service should have a local cache with the task data that
should be displayed in audit logs.

To send daily emails about earnings to all users, the service should have a
local cache of system users.

#### Incoming Messages

Processing of `auth.user.created`, `auth.user.changed`, `auth.user.deleted`
events is the same as in the Tasks service.

When processing `tasks.task.assigned`, `tasks.task.completed`,
`tasks.task.changed` events for a task that is not yet known to the service, a
record is created with randomly generated assignment and completion prices, and
the task is saved in the local cache with data from the Tasks service endpoint
`GET /tasks/{uuid}`.

`tasks.task.assigned` - creating a record of funds withdrawal from the
performer's account. The recording time is taken from the `timestamp` field of
the processed message to preserve the order of operations.

`tasks.task.completed` - creating a record of funds deposit into the
performer's account. The recording time is taken from the `timestamp` field of
the processed message to preserve the order of operations.

`tasks.task.changed` - updating task data in the local cache.
If the event timestamp is earlier than the timestamp of the user's last update
in the service's database, the event is ignored.

### Auth

The service should store user authentication data (username, password) and their
role in the system (administrator, manager, accountant, employee, etc.).

The service should support OAuth2 or OpenID Connect for user authentication in
other services of the system.

Additionally, the service can handle user registration and issue
machine-to-machine tokens for authorization of communications between services
via REST API.

#### Outgoing Messages

The following message format will be used for all outgoing events:

```jsonc
{
  "user_id": "uuid", // User UUID
  "timestamp": "ISO 8601 Datetime" // Event time
}
```

`auth.user.created` - user added to the system.

`auth.user.changed` - user data has changed.

`auth.user.deleted` - user has been removed from the system.

#### REST API

`GET /users/{uuid}` - obtaining user data (email, role, etc.).

## Problem Handling

Without a connection to the database, none of the services will be able to function.
However, since each service will have its own database, issues with the database
of one service will not affect the operability of another.

Lack of connection to the message broker will prevent the Tasks service from
working properly because it won't be able to correctly handle changes in task
status that other services need to be notified about. The Auth service is also
susceptible to the same problem. To restore the functionality of a service
without a connection to the broker, you can redirect the storage of its messages
to a local database, from which they will be forwarded to the broker once the
issues are resolved.

Issues with inter-service connectivity will prevent services from synchronizing
their local caches with other services. However, if messages from RabbitMQ about
the need to update data are not deleted, synchronization will occur after the
connection is restored.

To prevent DoS attacks from one service to another when there is a large
accumulation of updates (for example, after network issues), services should
limit the number of simultaneous requests to other services. Services should
handle error responses correctly: they should not retry requests after receiving
responses with status codes 400-499, and they should retry requests after
receiving a 503 status code only after a pause, etc.

Connection problems will prevent users from successfully logging in because it
requires an exchange of OAuth2 tokens between Auth and other services. Users who
have successfully logged in before the issues occurred will continue to use the
available services.

For the rest of the service functions, a connection is not required. However,
displayed data will become outdated without synchronization.

## Controversial Points

The main controversial aspect of this project is the need for data duplication
between services: users from Auth to Tasks and Finance, and tasks from Tasks to
Finance. This could be avoided by using API requests to services. I believe that
data duplication and gradual synchronization will make the system load more
evenly distributed compared to making requests whenever data is needed from
another service.

Replacing RabbitMQ with another message broker could simplify the system if the
broker could provide guarantees about task execution order. Then, there would be
no need for timestamp checks for different events.

It might be possible to avoid manual data synchronization through database
replication. However, this would tie one service to the schema of another
service (the details of its implementation) instead of using a public interface.

Calculating analytics in the Finance service could negatively impact the speed
of other operations. This could be avoided by moving analytics to a separate
service. However, this might lead to additional data and logic duplication:
calculating total earnings for top management is needed both on the accounting
dashboard for accountants and on the analytics dashboard. To partially address
the load issue, caching or a separate database replica for analytical queries
could be considered.
