#!/usr/bin/env python3
"""
AWS Bedrock Connection Test Script
Run this to verify your AWS setup before starting the application
"""

import boto3
import sys
import os
import json
from botocore.exceptions import NoCredentialsError, ClientError

def test_aws_credentials():
    """Test basic AWS credentials"""
    print("🔐 Testing AWS Credentials...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Credentials Valid")
        print(f"   Account: {identity.get('Account')}")
        print(f"   User: {identity.get('Arn')}")
        return True
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("   Solution: Run 'aws configure' or set environment variables")
        return False
    except Exception as e:
        print(f"❌ AWS credential error: {e}")
        return False

def test_bedrock_availability(region='ap-south-1'):
    """Test Bedrock service availability"""
    print(f"\n🧠 Testing Bedrock Service in {region}...")
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        models = bedrock.list_foundation_models()
        model_count = len(models.get('modelSummaries', []))
        print(f"✅ Bedrock service available")
        print(f"   Models available: {model_count}")
        
        # Check for specific models we need
        claude_models = [m for m in models['modelSummaries'] if 'claude' in m['modelId'].lower()]
        titan_models = [m for m in models['modelSummaries'] if 'titan' in m['modelId'].lower() and 'embed' in m['modelId'].lower()]
        
        print(f"   Claude models: {len(claude_models)}")
        print(f"   Titan embedding models: {len(titan_models)}")
        
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("❌ Bedrock access denied")
            print("   Solution: Check IAM permissions for Bedrock")
        else:
            print(f"❌ Bedrock error: {error_code}")
        return False
    except Exception as e:
        print(f"❌ Bedrock service error: {e}")
        return False

def test_model_access(region='ap-south-1'):
    """Test model access and invoke permissions"""
    print(f"\n🤖 Testing Model Access...")
    
    # Models to test (matching what user has access to)
    models_to_test = [
        {
            "name": "Claude 3 Haiku",
            "id": "anthropic.claude-3-haiku-20240307-v1:0",
            "test_body": {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Say 'test'"}]
            }
        },
        {
            "name": "Claude 3 Sonnet", 
            "id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "test_body": {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Say 'test'"}]
            }
        },
        {
            "name": "Titan Text Embeddings V2",
            "id": "amazon.titan-embed-text-v2:0", 
            "test_body": {"inputText": "test"}
        }
    ]
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        successful_tests = 0
        for model in models_to_test:
            try:
                print(f"   Testing {model['name']}...")
                
                response = bedrock_runtime.invoke_model(
                    body=json.dumps(model['test_body']),
                    modelId=model['id'],
                    accept='application/json',
                    contentType='application/json'
                )
                
                print(f"   ✅ {model['name']} accessible")
                successful_tests += 1
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"   ❌ {model['name']}: {error_code}")
            except Exception as e:
                print(f"   ❌ {model['name']}: {str(e)}")
        
        if successful_tests >= 2:  # At least Claude and Titan working
            print(f"\n✅ Model access successful ({successful_tests}/{len(models_to_test)} models)")
            return True
        else:
            print(f"\n❌ Insufficient model access ({successful_tests}/{len(models_to_test)} models)")
            return False
        
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions if tests fail"""
    print("\n" + "="*60)
    print("🚀 SETUP INSTRUCTIONS")
    print("="*60)
    print("\n1. Configure AWS Credentials:")
    print("   aws configure")
    print("   # Enter your Access Key ID, Secret Access Key, and Region")
    print("\n2. Enable Bedrock Model Access:")
    print("   - Go to AWS Console → Amazon Bedrock → Model Access")
    print("   - Enable access to Claude 3 Haiku and Titan Embeddings")
    print("\n3. Verify IAM Permissions:")
    print("   - Ensure your user/role has 'bedrock:InvokeModel' permissions")
    print("\n4. Test again:")
    print("   python test_bedrock_setup.py")
    print("\n5. Start the application:")
    print("   docker-compose up --build")

def main():
    print("AWS Bedrock Setup Verification")
    print("=" * 40)
    
    # Test 1: AWS Credentials
    creds_ok = test_aws_credentials()
    
    # Test 2: Bedrock Service
    bedrock_ok = False
    if creds_ok:
        bedrock_ok = test_bedrock_availability()
    
    # Test 3: Model Access
    model_ok = False
    if bedrock_ok:
        model_ok = test_model_access()
    
    # Summary
    print("\n" + "="*40)
    print("📊 SETUP STATUS")
    print("="*40)
    print(f"AWS Credentials: {'✅ OK' if creds_ok else '❌ FAILED'}")
    print(f"Bedrock Service: {'✅ OK' if bedrock_ok else '❌ FAILED'}")
    print(f"Model Access:    {'✅ OK' if model_ok else '❌ FAILED'}")
    
    if creds_ok and bedrock_ok and model_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your AWS Bedrock setup is ready. You can now start the application with AI features enabled.")
        return 0
    else:
        print("\n⚠️  SETUP INCOMPLETE")
        print("Some tests failed. Please follow the setup instructions below.")
        print_setup_instructions()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
