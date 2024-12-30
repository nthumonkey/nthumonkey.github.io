import os
import sys
import requests
from typing import Dict, Any

def get_env_var(name: str, required: bool = True) -> str:
    """Get environment variable or exit if required variable is missing."""
    value = os.getenv(name)
    if required and not value:
        print(f"Error: Required environment variable {name} is not set")
        sys.exit(1)
    return value or ''


def create_teams_adaptive_card() -> dict[str, Any]:
    """Create the Teams message payload based on the event type."""
    event_name = get_env_var('GITHUB_EVENT_NAME')
    repository = get_env_var('GITHUB_REPOSITORY')
    repo_name = repository.split('/', maxsplit=1)[1]
    actor = get_env_var('GITHUB_ACTOR')
    ref = get_env_var('GITHUB_REF')
    branch = ref.replace('refs/heads/', '').replace('refs/pull/', '')
    sha = get_env_var('GITHUB_SHA')

    title: str | None = None
    body: str | None = None
    
    match event_name:
        case 'pull_request':
            title = f"[PR] {get_env_var('PR_TITLE').strip()}"
            body = get_env_var('PR_BODY', required=False).strip()
        case 'push':
            message = get_env_var('COMMIT_MESSAGE').strip()
            splitted_message = message.split("\n", maxsplit=1)
            title = splitted_message[0].strip()
            body = message
        case _:
            raise Exception(f"Unknown event name for {event_name}")

    action_name = "Commit"
    title_url = f"https://github.com/{repository}/commit/{sha}"
    repo_url = f"https://github.com/{repository}"
    user_url = f"https://github.com/{actor}"

    content: dict[str, Any] = {
        "type": "AdaptiveCard",
        "speak": title,
        "version": "1.5",
        "body": [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "Image",
                                "url": f"https://github.com/{actor}.png",
                                "width": "40px",
                                "height": "auto",
                                "altText": "Logo",
                                "style": "RoundedCorners"
                            }
                        ],
                        "targetWidth": "atLeast:Narrow"
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "wrap": True,
                                "text": action_name,
                                "spacing": "None",
                                "size": "Small",
                                "color": "Accent"
                            },
                            {
                                "type": "TextBlock",
                                "text": title,
                                "wrap": True,
                                "weight": "Bolder",
                                "spacing": "None",
                                "style": "heading",
                                "maxLines": 2
                            },
                        ],
                        "selectAction": {
                            "type": "Action.OpenUrl",
                            "url": title_url
                        }
                    }
                ]
            },
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": actor,
                                "wrap": True,
                                "separator": True,
                                "maxLines": 1,
                                "size": "Small"
                            }
                        ],
                        "spacing": "None",
                        "verticalContentAlignment": "Center",
                        "separator": True,
                        "targetWidth": "atLeast:Narrow",
                        "selectAction": {
                            "type": "Action.OpenUrl",
                            "url": user_url
                        }
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": repo_name,
                                "wrap": True,
                                "maxLines": 1,
                                "size": "Small"
                            }
                        ],
                        "spacing": "Small",
                        "verticalContentAlignment": "Center",
                        "separator": True,
                        "selectAction": {
                            "type": "Action.OpenUrl",
                            "url": repo_url
                        }
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": branch,
                                "wrap": True,
                                "maxLines": 1,
                                "size": "Small"
                            }
                        ],
                        "spacing": "Small",
                        "verticalContentAlignment": "Center",
                        "separator": True,
                        "targetWidth": "atLeast:Narrow"
                    }
                ],
                "spacing": "Small"
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": body,
                        "wrap": True,
                        "spacing": "None",
                        "maxLines": 4,
                        "fontType": "Monospace"
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Author",
                                "value": actor
                            },
                            {
                                "title": "Branch",
                                "value": branch
                            }
                        ],
                        "targetWidth": "atMost:VeryNarrow",
                        "separator": True
                    }
                ]
            },
            {
                "type": "ActionSet",
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "Open Commit",
                        "url": title_url,
                        "style": "positive"
                    },
                    {
                        "type": "Action.OpenUrl",
                        "title": "Open Repo",
                        "url": repo_url
                    }
                ],
                "horizontalAlignment": "Right"
            }
        ],
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json"
    }
    
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": content
            }
        ]
    }


def main():
    # Get the webhook URL from environment variables
    webhook_url = get_env_var('TEAMS_WEBHOOK_URL')
    
    try:
        # Create and send the teams notification
        payload = create_teams_adaptive_card()
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("✅ Notification sent to Teams successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Teams notification: {str(e)}")
        print(payload)
        sys.exit(1)

if __name__ == "__main__":
    main()
