# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv
from pricing_service import PricingService
from Tea.exceptions import TeaException

def main():
    # Load environment variables
    load_dotenv()
    
    access_key_id = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    
    if not access_key_id or not access_key_secret:
        print("Error: ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET must be set in .env file.")
        sys.exit(1)

    # Debug credentials (masked)
    print(f"Debug: AccessKeyID Length: {len(access_key_id)}")
    print(f"Debug: AccessKeySecret Length: {len(access_key_secret)}")
    print(f"Debug: AccessKeyID Start/End: {access_key_id[:2]}...{access_key_id[-2:]}")
    print(f"Debug: AccessKeySecret Start/End: {access_key_secret[:2]}...{access_key_secret[-2:]}")


    # Configuration
    REGION = "cn-hangzhou"
    INSTANCE_TYPE = "ecs.g6.large"
    PERIOD = 1 # Year
    
    print("Connecting to Aliyun BSS API...")
    
    try:
        # Initialize Service
        service = PricingService(access_key_id, access_key_secret, REGION)
        
        print(f"Querying Price for: ECS ({REGION}, {INSTANCE_TYPE}, {PERIOD} Year)")
        
        # Get Price
        price = service.get_official_price(REGION, INSTANCE_TYPE, PERIOD)
        
        print("-" * 43)
        print(f"Official List Price: {price} CNY")
        print("-" * 43)
        
    except TeaException as e:
        print(f"Error: Aliyun API Request Failed.")
        request_id = e.data.get('RequestId', 'N/A') if e.data else 'N/A'
        print(f"RequestId: {request_id}")
        print(f"Message: {e.message}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
