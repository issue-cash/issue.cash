import pathlib


index_html = pathlib.Path("index.html").read_text()


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": index_html,
    }
