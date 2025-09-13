import argparse
from collector import dir_collector
from collector import cloudwatch_collector
from collector import api_collector
from processor import parser
from intelligence.analyzer import LogAnalyzer
import boto3

def get_latest_log_stream(group, region):
    client = boto3.client('logs', region_name=region)
    streams = client.describe_log_streams(
        logGroupName=group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    if streams['logStreams']:
        return streams['logStreams'][0]['logStreamName']
    return None

def main():
    parser_arg = argparse.ArgumentParser(description="Intelligent Log Analyzer")
    parser_arg.add_argument('--source', choices=['local', 'cloudwatch', 'api'], default='local', help='Log source: local directory, AWS CloudWatch, or API')
    parser_arg.add_argument('--group', type=str, help='CloudWatch log group name')
    parser_arg.add_argument('--stream', type=str, help='CloudWatch log stream name')
    parser_arg.add_argument('--region', type=str, default='us-east-1', help='AWS region for CloudWatch')
    parser_arg.add_argument('--api-url', type=str, help='API endpoint for logs')
    args = parser_arg.parse_args()

    analyzer = LogAnalyzer(window_seconds=60)  # 1-min rolling window

    if args.source == 'cloudwatch':
        if not args.group:
            print("Please provide --group for CloudWatch logs.")
            return
        if not args.stream:
            print("No stream specified, fetching latest log stream...")
            latest_stream = get_latest_log_stream(args.group, args.region)
            if not latest_stream:
                print("No log streams found in group.")
                return
            args.stream = latest_stream
            print(f"Auto-selected latest stream: {args.stream}")
        print(f"🔍 Watching CloudWatch logs: group={args.group}, stream={args.stream}...")
        log_iter = cloudwatch_collector.cloudwatch_logs(args.group, args.stream, args.region)
    elif args.source == 'api':
        if not args.api_url:
            print("Please provide --api-url for API log source.")
            return
        print(f"🔍 Watching logs from API: {args.api_url}")
        log_iter = api_collector.fetch_logs_from_api(args.api_url)
    else:
        print("🔍 Watching logs/ directory... (append logs to see results)")
        log_iter = dir_collector.tail_directory("logs")

    for raw_log in log_iter:
        # Step 1: Parse log
        parsed_log = parser.parse_log(raw_log["message"])
        parsed_log.update(raw_log)  # add timestamp + source

        # Step 2: Feed into analyzer
        analyzer.add_log(parsed_log)
        analysis = analyzer.analyze()

        # Step 3: Print structured output
        print("\n Log:", parsed_log)
        if analysis["anomalies"]:
            print("Anomalies Detected:", analysis["anomalies"])
        else:
            print("Analysis:", analysis)

if __name__ == "__main__":
    main()