from app.jobs.youtube_poller import run_once as run_youtube
from app.jobs.twitch_poller import run_once as run_twitch
from app.jobs.x_poller import run_once as run_x
from app.jobs.notification_sender import run_once as run_notify


def run_once() -> None:
    y = run_youtube()
    t = run_twitch()
    x_created, x_rl, x_failed = run_x()
    n_created, n_sent, n_failed = run_notify()

    print(
        "run_all_once finished:",
        {
            "youtube_created": y,
            "twitch_created": t,
            "x_created": x_created,
            "x_rate_limited": x_rl,
            "x_failed": x_failed,
            "notif_created": n_created,
            "notif_sent": n_sent,
            "notif_failed": n_failed,
        },
    )


if __name__ == "__main__":
    run_once()
