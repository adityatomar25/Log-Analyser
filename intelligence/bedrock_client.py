"""
AWS Bedrock Integration for Intelligent Log Analysis
"""
import boto3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class BedrockLogAnalyzer:
    """
    AWS Bedrock client for intelligent log analysis using foundation models
    """
    
    def __init__(self, region_name: str = "ap-south-1"):
        """Initialize Bedrock client"""
        try:
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=region_name
            )
            self.region = region_name
            
            # Model IDs for different tasks
            self.models = {
                "claude_haiku": "anthropic.claude-3-haiku-20240307-v1:0",
                "claude_sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0", 
                "titan_embed": "amazon.titan-embed-text-v2:0"
            }
            
            # Test connection (non-blocking)
            self._test_connection()
            logger.info("Bedrock client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            logger.info("Bedrock client will be unavailable. Please configure AWS credentials to enable AI features.")
            # Don't raise the exception during initialization if AWS credentials are available
            # Let individual model calls handle their own errors gracefully
            pass
    
    def _test_connection(self):
        """Test Bedrock connection"""
        try:
            # Create a separate bedrock client for listing models (not runtime)
            bedrock_client = boto3.client(
                service_name='bedrock',
                region_name=self.region
            )
            response = bedrock_client.list_foundation_models()
            logger.info(f"Bedrock connection successful. Available models: {len(response.get('modelSummaries', []))}")
        except Exception as e:
            logger.warning(f"Bedrock connection test failed: {e}. This may be normal if AWS credentials are not configured.")
            # Don't raise the exception - allow initialization to continue
            # The actual model calls will fail gracefully if credentials are missing
    
    def analyze_log_anomaly(self, log_entry: Dict, context_logs: List[Dict] = None) -> Dict:
        """
        Analyze a single log entry for anomalies using Claude
        
        Args:
            log_entry: Single log entry to analyze
            context_logs: Recent logs for context (optional)
            
        Returns:
            Dict with anomaly analysis results
        """
        try:
            # Prepare context
            context = self._prepare_log_context(log_entry, context_logs or [])
            
            # Create prompt for anomaly detection
            prompt = self._create_anomaly_prompt(context)
            
            # Call Claude model
            response = self._invoke_claude(prompt, model="claude_haiku")
            
            # Parse response
            analysis = self._parse_anomaly_response(response)
            
            return {
                "log_id": log_entry.get("timestamp", time.time()),
                "anomaly_score": analysis.get("score", 0),
                "anomaly_type": analysis.get("type", "none"),
                "confidence": analysis.get("confidence", 0),
                "explanation": analysis.get("explanation", ""),
                "recommendations": analysis.get("recommendations", []),
                "severity": analysis.get("severity", "low"),
                "model_used": "claude_haiku"
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly analysis: {e}")
            return self._default_analysis_result()
    
    def classify_log_patterns(self, logs: List[Dict]) -> Dict:
        """
        Classify logs into patterns and categories using Claude
        
        Args:
            logs: List of log entries to classify
            
        Returns:
            Dict with classification results
        """
        try:
            # Prepare log batch for analysis
            log_summary = self._prepare_logs_for_classification(logs)
            
            # Create classification prompt
            prompt = self._create_classification_prompt(log_summary)
            
            # Call Claude model with fallback
            try:
                response = self._invoke_claude(prompt, model="claude_sonnet")
                model_used = "claude_sonnet"
            except Exception as e:
                logger.warning(f"Claude Sonnet failed, falling back to Haiku: {e}")
                response = self._invoke_claude(prompt, model="claude_haiku")
                model_used = "claude_haiku"
            
            # Parse classification results
            classification = self._parse_classification_response(response)
            
            return {
                "patterns": classification.get("patterns", []),
                "categories": classification.get("categories", {}),
                "trends": classification.get("trends", []),
                "insights": classification.get("insights", []),
                "model_used": model_used
            }
            
        except Exception as e:
            logger.error(f"Error in log classification: {e}")
            return {"patterns": [], "categories": {}, "trends": [], "insights": []}
    
    def generate_log_embeddings(self, log_messages: List[str]) -> List[List[float]]:
        """
        Generate embeddings for log messages using Titan
        
        Args:
            log_messages: List of log message strings
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = []
            
            for message in log_messages:
                # Prepare input for Titan
                body = json.dumps({
                    "inputText": message[:1000]  # Titan has input limits
                })
                
                # Call Titan embedding model
                response = self.bedrock_runtime.invoke_model(
                    body=body,
                    modelId=self.models["titan_embed"],
                    accept='application/json',
                    contentType='application/json'
                )
                
                # Parse embedding response
                response_body = json.loads(response.get('body').read())
                embedding = response_body.get('embedding', [])
                embeddings.append(embedding)
                
                # Rate limiting
                time.sleep(0.1)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def predict_system_issues(self, recent_logs: List[Dict], system_metrics: Dict = None) -> Dict:
        """
        Predict potential system issues based on log patterns
        
        Args:
            recent_logs: Recent log entries
            system_metrics: Optional system metrics for context
            
        Returns:
            Dict with predictions and recommendations
        """
        try:
            # Analyze log trends
            trends = self._analyze_log_trends(recent_logs)
            
            # Create prediction prompt
            prompt = self._create_prediction_prompt(trends, system_metrics)
            
            # Call Claude for analysis
            response = self._invoke_claude(prompt, model="claude_sonnet")
            
            # Parse predictions
            predictions = self._parse_prediction_response(response)
            
            return {
                "risk_level": predictions.get("risk_level", "low"),
                "predicted_issues": predictions.get("issues", []),
                "time_to_issue": predictions.get("time_estimate", "unknown"),
                "preventive_actions": predictions.get("actions", []),
                "confidence": predictions.get("confidence", 0),
                "model_used": "claude_sonnet"
            }
            
        except Exception as e:
            logger.error(f"Error in system prediction: {e}")
            return {"risk_level": "unknown", "predicted_issues": [], "preventive_actions": []}
    
    def _invoke_claude(self, prompt: str, model: str = "claude_haiku") -> str:
        """Invoke Claude model with prompt"""
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.models[model],
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body["content"][0]["text"]
            
        except Exception as e:
            logger.error(f"Error invoking Claude: {e}")
            raise
    
    def _prepare_log_context(self, log_entry: Dict, context_logs: List[Dict]) -> str:
        """Prepare log context for analysis"""
        context = f"Current Log Entry:\n"
        context += f"Level: {log_entry.get('level', 'UNKNOWN')}\n"
        context += f"Message: {log_entry.get('message', '')}\n"
        context += f"Source: {log_entry.get('source', '')}\n"
        context += f"Timestamp: {log_entry.get('timestamp', '')}\n\n"
        
        if context_logs:
            context += "Recent Context Logs:\n"
            for i, log in enumerate(context_logs[-5:]):  # Last 5 logs for context
                context += f"{i+1}. [{log.get('level', 'UNKNOWN')}] {log.get('message', '')[:100]}...\n"
        
        return context
    
    def _create_anomaly_prompt(self, context: str) -> str:
        """Create prompt for anomaly detection"""
        return f"""
You are an expert system administrator analyzing logs for anomalies. Analyze the following log entry and context:

{context}

Provide a JSON response with the following structure:
{{
    "score": <anomaly_score_0_to_100>,
    "type": "<anomaly_type: error_spike|resource_issue|security_concern|performance_degradation|none>",
    "confidence": <confidence_0_to_100>,
    "severity": "<low|medium|high|critical>",
    "explanation": "<brief_explanation_of_findings>",
    "recommendations": ["<action1>", "<action2>"]
}}

Focus on:
1. Error patterns and frequency
2. Resource utilization issues
3. Security indicators
4. Performance degradation signs
5. Unusual system behavior

Respond with valid JSON only.
"""
    
    def _create_classification_prompt(self, log_summary: str) -> str:
        """Create prompt for log classification"""
        return f"""
You are a log analysis expert. Classify the following logs into patterns and provide insights:

{log_summary}

Provide a JSON response with:
{{
    "patterns": [
        {{"name": "<pattern_name>", "frequency": <count>, "description": "<description>"}}
    ],
    "categories": {{
        "application_errors": <count>,
        "system_errors": <count>, 
        "security_events": <count>,
        "performance_issues": <count>,
        "normal_operations": <count>
    }},
    "trends": ["<trend1>", "<trend2>"],
    "insights": ["<insight1>", "<insight2>"]
}}

Respond with valid JSON only.
"""
    
    def _create_prediction_prompt(self, trends: Dict, metrics: Dict = None) -> str:
        """Create prompt for system issue prediction"""
        metrics_str = f"\nSystem Metrics: {json.dumps(metrics)}" if metrics else ""
        
        return f"""
You are a predictive analytics expert for system monitoring. Based on the log trends below, predict potential system issues:

Log Trends: {json.dumps(trends)}{metrics_str}

Provide a JSON response:
{{
    "risk_level": "<low|medium|high|critical>",
    "confidence": <0_to_100>,
    "issues": [
        {{"type": "<issue_type>", "probability": <0_to_100>, "description": "<description>"}}
    ],
    "time_estimate": "<when_issue_might_occur>",
    "actions": ["<preventive_action1>", "<preventive_action2>"]
}}

Consider:
1. Error rate trends
2. Resource usage patterns
3. Historical failure patterns
4. Cascade failure risks

Respond with valid JSON only.
"""
    
    def _parse_anomaly_response(self, response: str) -> Dict:
        """Parse Claude's anomaly analysis response"""
        try:
            # Clean response and parse JSON
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:-3]
                
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Error parsing anomaly response: {e}")
            return self._default_analysis_result()
    
    def _parse_classification_response(self, response: str) -> Dict:
        """Parse Claude's classification response"""
        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:-3]
                
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
            return {"patterns": [], "categories": {}, "trends": [], "insights": []}
    
    def _parse_prediction_response(self, response: str) -> Dict:
        """Parse Claude's prediction response"""
        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:-3]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:-3]
                
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Error parsing prediction response: {e}")
            return {"risk_level": "unknown", "issues": [], "actions": []}
    
    def _prepare_logs_for_classification(self, logs: List[Dict]) -> str:
        """Prepare logs summary for classification"""
        summary = f"Log Analysis Summary ({len(logs)} entries):\n\n"
        
        # Group by level
        level_counts = {}
        sample_messages = {}
        
        for log in logs:
            level = log.get('level', 'UNKNOWN')
            level_counts[level] = level_counts.get(level, 0) + 1
            
            if level not in sample_messages:
                sample_messages[level] = []
            if len(sample_messages[level]) < 3:
                sample_messages[level].append(log.get('message', '')[:150])
        
        # Add level distribution
        summary += "Level Distribution:\n"
        for level, count in level_counts.items():
            summary += f"  {level}: {count}\n"
        
        # Add sample messages
        summary += "\nSample Messages by Level:\n"
        for level, messages in sample_messages.items():
            summary += f"\n{level} samples:\n"
            for i, msg in enumerate(messages, 1):
                summary += f"  {i}. {msg}...\n"
        
        return summary
    
    def _analyze_log_trends(self, logs: List[Dict]) -> Dict:
        """Analyze trends in recent logs"""
        if not logs:
            return {}
            
        # Calculate trends
        levels = [log.get('level', 'UNKNOWN') for log in logs]
        level_counts = {}
        for level in levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Error rate calculation
        total_logs = len(logs)
        error_logs = level_counts.get('ERROR', 0) + level_counts.get('CRITICAL', 0)
        error_rate = (error_logs / total_logs * 100) if total_logs > 0 else 0
        
        return {
            "total_logs": total_logs,
            "error_rate": error_rate,
            "level_distribution": level_counts,
            "time_span_minutes": 60,  # Assuming 1-hour window
            "most_common_level": max(level_counts.items(), key=lambda x: x[1])[0] if level_counts else "UNKNOWN"
        }
    
    def _default_analysis_result(self) -> Dict:
        """Return default analysis result for error cases"""
        return {
            "score": 0,
            "type": "none",
            "confidence": 0,
            "explanation": "Analysis unavailable",
            "recommendations": [],
            "severity": "low"
        }
