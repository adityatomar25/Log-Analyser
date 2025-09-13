import boto3
import time

def cloudwatch_logs(group_name, stream_name, region="us-east-1"):
    """
    Fetch logs from AWS CloudWatch.
    """
    client = boto3.client("logs", region_name=region)
    next_token = None

    while True:
        kwargs = {"logGroupName": group_name, "logStreamName": stream_name, "limit": 10}
        if next_token:
            kwargs["nextToken"] = next_token

        response = client.get_log_events(**kwargs)
        events = response["events"]

        for event in events:
            yield {
                "timestamp": event["timestamp"] / 1000.0,
                "source": f"cloudwatch:{group_name}/{stream_name}",
                "message": event["message"],
            }

        next_token = response.get("nextForwardToken")
        time.sleep(2)