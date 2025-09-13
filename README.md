# Intelligent Log Analyser & Alert Bot

A real-time, multi-source log analysis and anomaly detection system with alerting and extensibility. Supports local files, AWS CloudWatch, and REST API log sources.

## Features
- 📂 Collect logs from local files, AWS CloudWatch, or any REST API
- 🧠 Real-time anomaly detection (error spikes, critical failures, high error ratio)
- 🔍 Flexible log parsing (plain text & JSON logs)
- ⚡ Automated CloudWatch stream selection
- 🛠️ Modular, extensible architecture
- 📝 Command-line configuration

## Setup & Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/adityatomar25/Log-Analyser.git
   cd Log-Analyser
   ```
2. (Recommended) Create and activate a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. (Optional) Configure AWS credentials for CloudWatch:
   ```sh
   aws configure
   ```

## Usage
Run the analyser with your desired log source:

- **Local logs:**
  ```sh
  python main.py
  ```
- **AWS CloudWatch:**
  ```sh
  python main.py --source cloudwatch --group /aws/lambda/your-lambda-name --region ap-south-1
  ```
  (Stream auto-selected if not provided)
- **REST API:**
  ```sh
  python main.py --source api --api-url https://your-api-endpoint.com/logs
  ```

## Roadmap
**Phase 1 – Alerts**
- Email, Slack, Discord, or push notifications for anomalies

**Phase 2 – Smarter Intelligence**
- Statistical anomaly detection, NLP (AWS Bedrock)

**Phase 3 – Web Dashboard**
- Modern dashboard for live log and anomaly visualization

**Phase 4 – API Integration**
- Support for more log sources (GitHub, Kubernetes, etc.)

**Phase 5 – Production Ready**
- Docker, systemd, config file, cloud deployment

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](LICENSE)
