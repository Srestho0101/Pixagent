import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    print("Testing login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "email": "tech@example.com",
        "password": "password123"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"Token: {data['token'][:20]}...")
        print(f"Technician: {data['technician']['name']}")
        return data['token']
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_create_ticket(token):
    print("\nTesting create ticket...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/tickets", 
        headers=headers,
        json={
            "customer_name": "John Doe",
            "device_info": "MacBook Pro 2021 - Screen replacement",
            "status": "pending"
        })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Ticket created! ID: {data['id']}")
        return data['id']
    else:
        print(f"❌ Failed to create ticket: {response.status_code}")
        print(response.text)
        return None

def test_add_log(token, ticket_id):
    print("\nTesting add log...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/logs",
        headers=headers,
        json={
            "ticket_id": ticket_id,
            "note": "Diagnosed the issue. Screen needs replacement. Ordered new screen."
        })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Log added! ID: {data['id']}")
        print(f"Note: {data['note']}")
        return True
    else:
        print(f"❌ Failed to add log: {response.status_code}")
        print(response.text)
        return False

def test_get_tickets(token):
    print("\nTesting get tickets...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/tickets/my", headers=headers)
    
    if response.status_code == 200:
        tickets = response.json()
        print(f"✅ Retrieved {len(tickets)} tickets")
        for ticket in tickets:
            print(f"  - Ticket {ticket['id']}: {ticket['customer_name']} - {ticket['status']}")
        return True
    else:
        print(f"❌ Failed to get tickets: {response.status_code}")
        return False

def test_chat(ticket_id):
    print("\nTesting chat...")
    response = requests.post(f"{BASE_URL}/api/chat",
        json={
            "ticket_id": ticket_id,
            "message": "What's the status of my repair?",
            "history": []
        },
        stream=True)
    
    if response.status_code == 200:
        print("✅ Chat response (streaming):")
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data != '[DONE]':
                        try:
                            parsed = json.loads(data)
                            if 'content' in parsed:
                                print(f"  AI: {parsed['content']}")
                        except:
                            pass
        return True
    else:
        print(f"❌ Chat failed: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Backend Test Suite")
    print("=" * 50)
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Stopping tests - login failed")
        exit(1)
    
    # Test create ticket
    ticket_id = test_create_ticket(token)
    if not ticket_id:
        print("\n❌ Stopping tests - ticket creation failed")
        exit(1)
    
    # Test add log
    test_add_log(token, ticket_id)
    
    # Test get tickets
    test_get_tickets(token)
    
    # Test chat
    test_chat(ticket_id)
    
    print("\n" + "=" * 50)
    print("Test suite complete!")
    print("=" * 50)