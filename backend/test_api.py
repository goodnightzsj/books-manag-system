"""
简单的API测试脚本
需要先启动后端服务
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def print_response(response, title="Response"):
    """打印格式化的响应"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_health():
    """测试健康检查"""
    print("Testing health check...")
    response = requests.get("http://localhost:8000/health")
    print_response(response, "Health Check")
    return response.status_code == 200

def test_register():
    """测试用户注册"""
    print("Testing user registration...")
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print_response(response, "User Registration")
    return response.status_code == 201

def test_login():
    """测试用户登录"""
    print("Testing user login...")
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print_response(response, "User Login")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return token
    return None

def test_get_current_user(token):
    """测试获取当前用户信息"""
    print("Testing get current user...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print_response(response, "Current User")
    return response.status_code == 200

def test_get_books(token):
    """测试获取书籍列表"""
    print("Testing get books...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/books", headers=headers)
    print_response(response, "Books List")
    return response.status_code == 200

def test_create_book(token):
    """测试创建书籍"""
    print("Testing create book...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": "测试书籍",
        "author": "测试作者",
        "description": "这是一本测试书籍",
        "file_path": "C:/test/book.pdf",
        "file_format": "pdf"
    }
    response = requests.post(f"{BASE_URL}/books", json=data, headers=headers)
    print_response(response, "Create Book")
    
    if response.status_code == 201:
        return response.json().get("id")
    return None

def test_get_categories(token):
    """测试获取分类列表"""
    print("Testing get categories...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/categories", headers=headers)
    print_response(response, "Categories List")
    return response.status_code == 200

def test_create_category(token):
    """测试创建分类"""
    print("Testing create category...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "科幻小说",
        "description": "科幻类书籍"
    }
    response = requests.post(f"{BASE_URL}/categories", json=data, headers=headers)
    print_response(response, "Create Category")
    
    if response.status_code == 201:
        return response.json().get("id")
    return None

def test_random_recommendations(token):
    """测试随机推荐"""
    print("Testing random recommendations...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/recommendations/random?count=5", headers=headers)
    print_response(response, "Random Recommendations")
    return response.status_code == 200

def test_trending_books(token):
    """测试热门推荐"""
    print("Testing trending books...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/recommendations/trending?count=5", headers=headers)
    print_response(response, "Trending Books")
    return response.status_code == 200

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Starting API Tests")
    print("="*60 + "\n")
    
    results = {}
    
    # 1. 测试健康检查
    results["Health Check"] = test_health()
    
    # 2. 测试登录
    token = test_login()
    if not token:
        print("\n❌ Login failed! Cannot continue tests.")
        print("\n💡 Make sure:")
        print("   1. Backend service is running (run_local.bat)")
        print("   2. Database is set up (setup_db.bat)")
        print("   3. Admin user exists (username: admin, password: admin123)")
        return
    
    results["User Login"] = True
    
    # 3. 测试获取当前用户
    results["Get Current User"] = test_get_current_user(token)
    
    # 4. 测试书籍相关
    results["Get Books"] = test_get_books(token)
    book_id = test_create_book(token)
    results["Create Book"] = book_id is not None
    
    # 5. 测试分类相关
    results["Get Categories"] = test_get_categories(token)
    category_id = test_create_category(token)
    results["Create Category"] = category_id is not None
    
    # 6. 测试推荐
    results["Random Recommendations"] = test_random_recommendations(token)
    results["Trending Books"] = test_trending_books(token)
    
    # 打印测试结果摘要
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the output above.")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("\n💡 Make sure the backend service is running:")
        print("   cd backend")
        print("   run_local.bat")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
