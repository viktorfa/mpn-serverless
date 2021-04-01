lambda_context = None


def get_log_group_url() -> str:
    try:
        return f"https://eu-central-1.console.aws.amazon.com/cloudwatch/home?region=eu-central-1#logEventViewer:group={lambda_context.log_group_name};stream={lambda_context.log_stream_name}"
    except Exception:
        return ""