from chalice.test import Client
from app import app


def test_notify():
    with Client(app) as client:
        response = client.lambda_.invoke(
            "cron_handler",
            client.events.generate_cw_event(
                source="",
                detail_type="",
                detail="",
                resources=""
            ),
        )

        assert response.payload == "Ok"
