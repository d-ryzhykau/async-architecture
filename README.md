# Awesome Task Exchange System

## Kafka Topic Naming Convention

```text
<domain>.<type>.<description>.<version>
```

* `domain` - name of the Domain in which the event has occurred;
* `type` - `cud` for data streaming events, `business` for business events;
* `description` - short description of the event,
  (e.g. entity name for `cud` events, event name for `business` events);
* `version` - version of the topic.

Examples:

* `auth.cud.user.0` - topic for CUD-events of Auth domain for User entity, version 0;
* `task_tracker.business.task_assigned.1` - topic for business events
  "Task assigned" of Task Tracker domain, version 1.
