# Awesome Task Exchange System
В результате анализа требований были выявлены следующие предметные области:
* tasks - управление задачами;
* finance - учёт финансовых операций, расчёт финансовой аналитики;
* auth - управление пользователями, авторизация.

Каждая предметная область имеет набор тесно связанных операций и данных. Также
у разных предметных областей разный приоритет для бизнеса:
* tasks - основная предметная область с наивысшим приоритетом для разработки;
* finance - поддержка основной предметной области;
* auth - неспециализированная область, можно использовать готовое решение
  (например Keycloak).

Ожидается, что tasks будет использоваться командой разработки, в то время как
finance - командой бухгалтеров. Ожидается, что у данных команд разные
бизнес-процессы и разный цикл их изменения. Было бы полезно, чтобы введение
в эксплуатацию изменений в разные процессы было независимым.

Каждая предметная область должна быть представлена отдельным сервисом.
Названия сервисов совпадают с названиями предметных областей.

## Коммуникации

### Синхронные
Для получения данных из другого сервиса в момент обработки команд и событий
сервисы-клиенты могут использовать REST API друг друга.

REST API сервисов доступно только при использовании machine-to-machine токенов,
выдаваемых каждому сервису-клиенту, чтобы не допустить
несанкционированного доступа к данным.

### Асинхронные
Для событий, которые могут представлять интерес для других сервисов и их
предметных областей, сервисы должны публиковать сообщения с описанием событий.

Для обмена сообщениями будет использована RabbitMQ, т.к. он предоставляет всё
необходимое для реализации требуемой системы.

Каждый тип событий должен иметь отдельный ключ (`routing_key`).
Ключи сообщений должны иметь следующий формат:
```
<service_name>.<entity_name>.<event_name>
```
* `<service_name>` - название сервиса, отправляющего сообщение.
* `<entity_name>` - название сущности, с которой произошло событие.
* `<event_name>` - название события.

Сообщения должны публиковаться в общий topic exchange, на который
личные очереди сервисов-потребителей будут подписаны для получения тех типов
событий, которые им нужно обрабатывать.

Данные внутри сообщений будут закодированы в формате JSON.

## Сервисы

### Tasks
Сервис должен предоставлять весь функционал дашборда с задачами:
* отображение списка задач (в т.ч. назначенных на текущего пользователя);
* создание задач;
* отметка задач выполненными;
* назначение исполнителей задач.

Сервис должен хранить задачи с описанием и ссылкой на исполнителя.

Также сервис должен поддерживать локальный кэш активных пользователей системы
для ускорения выбора случайного исполнителя задачи и отображения данных о нём.

#### Исходящие сообщения
`tasks.task.assigned` - для задачи был выбран новый исполнитель
(в т.ч. для новой задачи).
```jsonc
{
  "task_uuid": "uuid", // UUID задачи
  "assigned_to": "uuid", // UUID исполнителя задачи
  "timestamp": "ISO 8601 Datetime" // время назначения
}
```

`tasks.task.completed` - задача отмечена как выполненная.
```jsonc
{
  "task_uuid": "uuid",
  "assigned_to": "uuid", // UUID последнего исполнителя задачи
  "timestamp": "ISO 8601 Datetime" // время выполнения
}
```

`tasks.task.changed` - описание задачи изменилось (в т.ч. для новой задачи).
```jsonc
{
  "task_uuid": "uuid",
  "timestamp": "ISO 8601 Datetime" // время обновления
}
```

#### Входящие сообщения
`auth.user.created`, `auth.user.changed` - добавление или обновление данных
пользователя в базе сервиса.
Если timestamp события меньше, чем timestamp последнего обновления
пользователя в базе сервиса, событие игнорируется.
Данные пользователя извлекаются через эндпоинт `GET /users/{uuid}`
сервиса Auth.
Если роль пользователя поменялась на роль не совместимую с выполнением задач
(менеджер, администратор), задачи пользователя переназначаются на кого-то
с подходящей для выполнения задач ролью.

`auth.user.deleted` - удаление пользователя из локального кэша.
Задачи удалённого пользователя переназначаются на пользователей
с подходящими ролями.

#### REST API
`GET /tasks/{uuid}` - получение данных о задаче.

### Finance
Сервис отвечает за учёт финансовых операций:
* назначение цен для задач;
* запись лога финансовых операций;
* выведение состояния счёта сотрудника;
* ежедневная отправка писем с суммами выплат сотрудникам;
* подсчёт заработков топ-менеджмента за день;
* выведение данных

Сервис должен хранить историю зачислений средств за выполнение и списываний
за переназначение задач для каждого пользователя.
В конце каждого рабочего дня для сотрудников с положительным балансом
создаётся запись о выплате и, соответственно, обнулении баланса.

На основе истории о зачислении средств на счёт исполнителей может быть построен
дашборд с аналитикой. Чтобы минимизировать нагрузку от аналитических запросов,
их результаты можно кэшировать. Кэш нужно инвалидировать или, когда это просто,
как в случае с суммой заработков, обновлять при создании новых записей.
Также кэш можно инвалидировать по времени.

Также сервис должен иметь локальный кэш с теми данными о задачах, которые должны
отображаться в аудит логах.

Чтобы отправлять ежедневные письма о заработках всем пользователям,
сервис должен иметь локальный кэш пользователей системы.

#### Входящие сообщения
Обработка событий `auth.user.created`, `auth.user.changed`, `auth.user.deleted`
такая же как в сервисе Tasks.

При обработке событий `tasks.task.assigned`, `tasks.task.completed`,
`tasks.task.changed` для задачи, которая ещё не известна сервису,
создаётся запись со сгенерированными ценами назначения и выполнения,
задача сохраняется в локальный кэш с данными с эндпоинта сервиса Tasks
`GET /tasks/{uuid}`.

`tasks.task.assigned` - создание записи о снятии средств со счёта исполнителя.
Время записи берётся из поля `timestamp` обрабатываемого сообщения
для сохранения порядка операций.

`tasks.task.completed` - создание записи о зачислении средств на счёт
исполнителя.
Время записи берётся из поля `timestamp` обрабатываемого сообщения
для сохранения порядка операций.

`tasks.task.changed` - обновление данных о задаче в локальном кэше.
Если timestamp события меньше, чем timestamp последнего обновления
пользователя в базе сервиса, событие игнорируется.

### Auth
Сервис должен хранить данные для аутентификации пользователей (логин, пароль),
их роль в системе (администратор, менеджер, бухгалтер, сотрудник).

Сервис должен поддерживать OAuth2 или OpenID Connect для аутентификации
пользователей в других сервисах системы.

Также сервис может отвечать за регистрацию и выдачу machine-to-machine токенов
для авторизации коммуникаций между сервисами по REST API.

#### Исходящие сообщения
Для всех исходящих событий будет использован следующий формат сообщений:
```jsonc
{
  "user_id": "uuid" // UUID пользователя
}
```

`auth.user.created` - пользователь добавлен в систему.

`auth.user.changed` - данные пользователя поменялись.

`auth.user.deleted` - пользователь удалён из системы.


#### REST API
`GET /users/{uuid}` - получение данных о пользователе (почта, роль, и т.д.).

# TODO
* Проблемы
* Спорные места
