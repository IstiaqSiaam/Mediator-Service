import requests
import json
import time
from pprint import pprint

def test_alignment(remote_service_url, method='combined'):
    """Test alignment with a remote service"""
    print(f"\nTesting alignment with {remote_service_url} using method: {method}")
    
    # 1. Test RDG retrieval and alignment
    print("\n1. Testing RDG retrieval and alignment...")
    response = requests.post(
        'http://localhost:5000/get_rdg',
        json={
            'remote_service_url': remote_service_url,
            'alignment_method': method
        }
    )
    
    if response.status_code == 200:
        if 'application/json' in response.headers.get('Content-Type', ''):
            # We got alignments that need confirmation
            result = response.json()
            if result.get('status') == 'needs_confirmation':
                print("Alignments needing confirmation:")
                alignments = result['alignments']
                for a in alignments:
                    print(f"Source: {a['source_uri']}")
                    print(f"Target: {a['target_uri']}")
                    print(f"Confidence: {a['confidence']}")
                    print("---")
                
                # Confirm all alignments
                confirm_response = requests.post(
                    'http://localhost:5000/confirm_alignment',
                    json={
                        'service_id': result['service_id'],
                        'alignments': alignments
                    }
                )
                if confirm_response.status_code == 200:
                    print("Successfully confirmed alignments")
                else:
                    print(f"Error confirming alignments: {confirm_response.text}")
        else:
            print("Successfully retrieved RDG")
    else:
        print(f"Error retrieving RDG: {response.text}")
    
    # 2. Test cottage booking
    print("\n2. Testing cottage booking...")
    booking_data = {
        'remote_service_url': remote_service_url,
        'checkIn': '2024-01-01',
        'checkOut': '2024-01-07',
        'guests': 2,
        'location': 'Lakeside'
    }
    
    response = requests.post(
        'http://localhost:5000/book_cottage',
        json=booking_data
    )
    
    if response.status_code == 200:
        print("Booking response:")
        pprint(response.json())
    else:
        print(f"Error booking cottage: {response.text}")

def main():
    # Start testing
    print("Starting alignment tests...")
    
    # Test with fake remote service
    test_alignment('http://localhost:5002', 'custom')
    time.sleep(1)  # Wait a bit between tests
    
    test_alignment('http://localhost:5002', 'api')
    time.sleep(1)
    
    test_alignment('http://localhost:5002', 'combined')
    
    print("\nTests completed!")

if __name__ == '__main__':
    main()
