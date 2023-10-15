import json
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from kafka import KafkaProducer

from outbox.models import Event


def key_serializer(key: str) -> bytes:
    return key.encode()


def value_serializer(value) -> bytes:
    return json.dumps(value).encode()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            help="Number of events sent in one batch.",
            type=int,
            default=10,
        )
        parser.add_argument(
            "--pause-for",
            help="Interval in seconds to pause for between sending batches of events.",
            type=int,
            default=1,
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        pause_for = options["pause_for"]

        kafka_producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_ADDRESS,
            key_serializer=key_serializer,
            value_serializer=value_serializer,
        )

        while True:
            with transaction.atomic():
                events = list(
                    Event.objects
                    .unsent()
                    .select_for_update(skip_locked=True)
                    [:batch_size]
                )
                for event in events:
                    kafka_producer.send(
                        topic=event.topic,
                        key=event.key,
                        value=event.payload,
                    )
                    event.mark_sent()
                # make sure events are written to kafka
                kafka_producer.flush()
                # save events
                Event.objects.bulk_update(events, ["sent_at"])

            time.sleep(pause_for)
