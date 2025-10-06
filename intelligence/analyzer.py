import time
import logging
import asyncio
from collections import deque, Counter
from typing import Dict, List, Optional

# Conditional import for Bedrock (fallback if not available)
try:
    from .bedrock_client import BedrockLogAnalyzer
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False
    logging.warning("Bedrock client not available. Using basic analysis only.")

logger = logging.getLogger(__name__)

class LogAnalyzer:
    def __init__(self, window_seconds=60, enable_bedrock=True, aws_region="ap-south-1"):
        self.window_seconds = window_seconds
        self.logs = deque()
        
        # Bedrock integration
        self.enable_bedrock = enable_bedrock and BEDROCK_AVAILABLE
        self.bedrock_client = None
        
        # Enhanced analytics state
        self.analysis_cache = {}
        self.last_bedrock_analysis = 0
        self.bedrock_interval = 30  # Run Bedrock analysis every 30 seconds
        
        if self.enable_bedrock:
            try:
                self.bedrock_client = BedrockLogAnalyzer(region_name=aws_region)
                logger.info("Bedrock-enhanced analysis enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Bedrock client: {e}")
                logger.info("Falling back to basic analysis. Configure AWS credentials to enable AI features.")
                self.enable_bedrock = False
                self.bedrock_client = None

    def add_log(self, log):
        """Add new log and clean up old logs outside window"""
        now = time.time()
        self.logs.append(log)

        # Keep only logs within rolling window
        while self.logs and now - self.logs[0]["timestamp"] > self.window_seconds:
            self.logs.popleft()

    def analyze(self) -> Dict:
        """
        Enhanced analysis combining traditional rules with Bedrock AI insights
        """
        # Basic statistical analysis (always available)
        basic_analysis = self._basic_analysis()
        
        # Enhanced Bedrock analysis (if enabled and conditions met)
        bedrock_analysis = {}
        if self.enable_bedrock and self._should_run_bedrock_analysis():
            try:
                bedrock_analysis = self._bedrock_analysis()
                self.last_bedrock_analysis = time.time()
            except Exception as e:
                logger.error(f"Bedrock analysis failed: {e}")
        
        # Combine results
        return self._merge_analysis_results(basic_analysis, bedrock_analysis)
    
    def _basic_analysis(self) -> Dict:
        """Traditional rule-based analysis"""
        levels = [log["level"] for log in self.logs]
        counts = Counter(levels)

        anomalies = []
        now = time.time()

        # Rule 1: Error spike (>=5 errors in last 10 sec)
        recent_errors = [l for l in self.logs if l["level"] == "ERROR" and now - l["timestamp"] <= 10]
        if len(recent_errors) >= 5:
            anomalies.append("Error spike detected")

        # Rule 2: Critical escalation
        if "CRITICAL" in levels:
            anomalies.append("Critical system failure detected")

        # Rule 3: Error-to-info ratio (more than 50% errors)
        total_logs = len(self.logs)
        if total_logs > 0 and counts.get("ERROR", 0) / total_logs > 0.5:
            anomalies.append("System instability: too many errors")

        return {
            "counts": dict(counts),
            "anomalies": anomalies,
            "analysis_type": "basic"
        }
    
    def _should_run_bedrock_analysis(self) -> bool:
        """Determine if Bedrock analysis should run"""
        now = time.time()
        return (
            len(self.logs) > 5 and  # Have sufficient logs
            (now - self.last_bedrock_analysis) > self.bedrock_interval  # Interval passed
        )
    
    def _bedrock_analysis(self) -> Dict:
        """AI-powered analysis using AWS Bedrock"""
        if not self.bedrock_client:
            return {}
        
        try:
            logs_list = list(self.logs)
            
            # 1. Classify log patterns
            classification = self.bedrock_client.classify_log_patterns(logs_list)
            
            # 2. Analyze recent logs for anomalies
            anomaly_results = []
            if logs_list:
                # Analyze the most recent log with context
                recent_log = logs_list[-1]
                context_logs = logs_list[-10:] if len(logs_list) > 10 else logs_list[:-1]
                
                anomaly_analysis = self.bedrock_client.analyze_log_anomaly(
                    recent_log, context_logs
                )
                anomaly_results.append(anomaly_analysis)
            
            # 3. Predict potential issues
            predictions = self.bedrock_client.predict_system_issues(logs_list)
            
            return {
                "bedrock_classification": classification,
                "bedrock_anomalies": anomaly_results,
                "bedrock_predictions": predictions,
                "analysis_type": "bedrock_enhanced"
            }
            
        except Exception as e:
            logger.error(f"Bedrock analysis error: {e}")
            return {}
    
    def _merge_analysis_results(self, basic: Dict, bedrock: Dict) -> Dict:
        """Merge basic and Bedrock analysis results"""
        merged = basic.copy()
        
        if bedrock:
            # Enhance anomalies with AI insights
            ai_anomalies = self._extract_ai_anomalies(bedrock)
            merged["anomalies"].extend(ai_anomalies)
            
            # Add AI insights
            merged["ai_insights"] = {
                "patterns": bedrock.get("bedrock_classification", {}).get("patterns", []),
                "trends": bedrock.get("bedrock_classification", {}).get("trends", []),
                "predictions": bedrock.get("bedrock_predictions", {}),
                "risk_level": bedrock.get("bedrock_predictions", {}).get("risk_level", "low")
            }
            
            # Enhanced categorization
            categories = bedrock.get("bedrock_classification", {}).get("categories", {})
            if categories:
                merged["log_categories"] = categories
        
        # Remove duplicates from anomalies
        merged["anomalies"] = list(set(merged["anomalies"]))
        merged["bedrock_enabled"] = self.enable_bedrock
        
        return merged
    
    def _extract_ai_anomalies(self, bedrock_results: Dict) -> List[str]:
        """Extract actionable anomalies from Bedrock results"""
        anomalies = []
        
        # From anomaly analysis
        bedrock_anomalies = bedrock_results.get("bedrock_anomalies", [])
        for analysis in bedrock_anomalies:
            if analysis.get("anomaly_score", 0) > 60:  # High confidence threshold
                anomaly_type = analysis.get("type", "unknown")
                severity = analysis.get("severity", "low")
                
                if anomaly_type != "none":
                    anomalies.append(f"AI detected {severity} {anomaly_type}")
        
        # From predictions
        predictions = bedrock_results.get("bedrock_predictions", {})
        risk_level = predictions.get("risk_level", "low")
        if risk_level in ["high", "critical"]:
            predicted_issues = predictions.get("predicted_issues", [])
            for issue in predicted_issues[:2]:  # Limit to top 2 predictions
                if issue.get("probability", 0) > 70:
                    anomalies.append(f"Predicted: {issue.get('description', 'System issue')}")
        
        return anomalies
    
    def get_detailed_insights(self) -> Dict:
        """Get comprehensive analysis including Bedrock insights"""
        if not self.enable_bedrock or not self.bedrock_client:
            return {"error": "Bedrock not available"}
        
        try:
            logs_list = list(self.logs)
            
            # Get comprehensive analysis
            classification = self.bedrock_client.classify_log_patterns(logs_list)
            predictions = self.bedrock_client.predict_system_issues(logs_list)
            
            # Generate embeddings for semantic analysis (sample)
            if logs_list:
                sample_messages = [log.get("message", "") for log in logs_list[-5:]]
                embeddings = self.bedrock_client.generate_log_embeddings(sample_messages)
            else:
                embeddings = []
            
            return {
                "classification": classification,
                "predictions": predictions,
                "embeddings_count": len(embeddings),
                "semantic_analysis_ready": len(embeddings) > 0,
                "total_logs_analyzed": len(logs_list)
            }
            
        except Exception as e:
            logger.error(f"Detailed insights error: {e}")
            return {"error": str(e)}