import requests


def notify_user(user, message):
    requests.post(f"https://ntfy.sh/{user}", data=message.encode(encoding="utf-8"))


def send_push(user, title, message):
    requests.post(
        f"https://ntfy.sh/{user}",
        data=message.encode(encoding="utf-8"),
        headers={
            "Title": title.encode(encoding="utf-8"),
            "Priority": "urgent",
        },
    )
