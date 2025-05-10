# FastAPI Simple Web Service

This project is a simple web service built with FastAPI, Uvicorn, and Pydantic, using UV for environment and package management. It\'s designed as a preparatory step for a coding interview.

## Features

*   **POST `/items/`**: Create a new item.
    *   Request body: JSON object with `name` (str), `description` (str, optional), `price` (float), `tags` (list of str, optional).
    *   Response: JSON object with `item_id`, the created `item` details, and a `message`.
*   **GET `/items/`**: Retrieve all created items.
    *   Response: JSON object with a list of `items` and the `count`.
*   **GET `/items/{item_id}`**: Retrieve a specific item by its ID.
    *   Response: JSON object of the item.
*   **GET `/health`**: A simple health check endpoint.

## Project Structure

```
LastAPI/
├── app/
│   ├── __init__.py
│   ├── main.py       # FastAPI application logic
│   └── models.py     # Pydantic models
├── tests/
│   ├── __init__.py
│   └── test_main.py  # Pytest tests
├── .venv/            # Virtual environment (managed by uv)
├── README.md         # This file
└── requirements.txt  # Project dependencies
```

## Setup and Running

This project uses [UV](https://github.com/astral-sh/uv) for virtual environment and package management. UV is a very fast Python package installer and resolver, written in Rust, intended as a drop-in replacement for `pip` and `pip-tools` workflows.

1.  **Install UV and dependencies** (if you haven\'t already):
    Follow the instructions on the [official UV installation guide](https://github.com/astral-sh/uv#installation).
    For example, on macOS/Linux:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    Or using pip (if you have an existing Python environment):
    ```bash
    pip install uv
    ```
    On Mac ARM64, we need to install redis-server:
    ```bash
    brew install redis
    ```

2.  **Create a virtual environment and install dependencies**:
    Navigate to the project root directory (`LastAPI`).
    ```bash
    # Create a virtual environment named .venv in the current directory
    uv sync --all-extras
    # Activate the virtual environment
    source .venv/bin/activate  # On macOS/Linux
    # .venv\\Scripts\\activate    # On Windows (Command Prompt)
    # . .venv/Scripts/activate # On Windows (PowerShell or Git Bash)
    ```

3.  **Run the FastAPI server**:
    Ensure your virtual environment is activated and you are in the `LastAPI` root directory.
    Use `./start_server.sh`
    or
    ```bash
    redis-server --daemonize yes
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `app.main:app`: Points to the `app` instance in the `app/main.py` file.
    *   `--reload`: Enables auto-reloading when code changes (for development).
    *   `--host 0.0.0.0`: Makes the server accessible from your local network (and localhost).
    *   `--port 8000`: Runs the server on port 8000.

    Ping Redis:
    ```bash
    redis-cli ping
    ```

4.  **Access the API**:
    *   API Docs (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    *   Alternative API Docs (ReDoc): [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Running Tests

Ensure your virtual environment is activated and development dependencies (like `pytest` and `httpx` from `requirements.txt`) are installed. From the `LastAPI` root directory:

```bash
pytest
```
This will discover and run tests in the `tests/` directory. The tests include a fixture to automatically clear the in-memory database before each test run for better isolation.

## `curl` Examples

Make sure the server is running (`uvicorn app.main:app --reload --port 8000`).

1.  **Health Check (GET)**:
    ```bash
    curl -X GET "http://127.0.0.1:8000/health"
    ```
    Expected output: `{"status":"ok"}`

2.  **Create an Item (POST)**:
    ```bash
    curl -X POST "http://127.0.0.1:8000/items/" \
    -H "Content-Type: application/json" \
    -d \'{
        "name": "My Awesome Gadget",
        "description": "The best gadget ever.",
        "price": 49.99,
        "tags": ["electronics", "cool"]
    }\'
    ```
    Expected output (item_id will be 1 if it\'s the first item):
    ```json
    {
        "item_id": 1,
        "item": {
            "name": "My Awesome Gadget",
            "description": "The best gadget ever.",
            "price": 49.99,
            "tags": ["electronics", "cool"]
        },
        "message": "Item created successfully"
    }
    ```

3.  **Attempt to Create a Duplicate Item (POST)**:
    (Run this after the previous command)
    ```bash
    curl -X POST "http://127.0.0.1:8000/items/" \
    -H "Content-Type: application/json" \
    -d \'{
        "name": "My Awesome Gadget",
        "description": "Another attempt with the same name.",
        "price": 59.99,
        "tags": ["duplicate_attempt"]
    }\'
    ```
    Expected output:
    ```json
    {
        "detail": "Item with name \'My Awesome Gadget\' already exists"
    }
    ```

4.  **Get All Items (GET)**:
    (Assuming the first item was created successfully)
    ```bash
    curl -X GET "http://127.0.0.1:8000/items/"
    ```
    Expected output:
    ```json
    {
        "items": [
            {
                "name": "My Awesome Gadget",
                "description": "The best gadget ever.",
                "price": 49.99,
                "tags": ["electronics", "cool"]
            }
        ],
        "count": 1
    }
    ```

5.  **Get a Specific Item (GET)**:
    (Assuming an item with ID 1 was created)
    ```bash
    curl -X GET "http://127.0.0.1:8000/items/1"
    ```
    Expected output:
    ```json
    {
        "name": "My Awesome Gadget",
        "description": "The best gadget ever.",
        "price": 49.99,
        "tags": ["electronics", "cool"]
    }
    ```

6.  **Attempt to Get a Non-existent Item (GET)**:
    ```bash
    curl -X GET "http://127.0.0.1:8000/items/999"
    ```
    Expected output:
    ```json
    {
        "detail": "Item not found"
    }
    ```

## Why FastAPI and Uvicorn?

For this simple web service, FastAPI and Uvicorn were chosen for several compelling reasons:

*   **FastAPI (Framework)**:
    *   **High Performance**: FastAPI is built on top of Starlette (for the web parts) and Pydantic (for data validation and serialization). It\'s one of the fastest Python web frameworks available, comparable to NodeJS and Go in many benchmarks. This is due to its asynchronous nature (ASGI) and efficient data handling.
    *   **Rapid Development**:
        *   **Automatic Data Validation**: Pydantic models allow for clear, concise data definitions. FastAPI uses these models to automatically validate request data and serialize response data, significantly reducing boilerplate code. This also includes helpful error messages for invalid data.
        *   **Automatic API Documentation**: Interactive API documentation (Swagger UI and ReDoc) is generated automatically from your Python type hints and Pydantic models. This is invaluable for development, testing, and collaboration, allowing you to interact with your API directly from the browser.
        *   **Type Safety & Editor Support**: Leverages Python type hints for robust code, leading to better editor support (autocompletion, type checking with tools like MyPy), and reduced runtime errors.
    *   **Modern Python Features**: Embraces `async/await` for concurrent programming, making it highly suitable for I/O-bound tasks without complex threading or multiprocessing setups.
    *   **Dependency Injection**: A simple yet powerful dependency injection system that helps in managing dependencies (like database connections, authentication logic) and writing cleaner, more testable code.
    *   **Conciseness**: Often requires less code to achieve the same functionality compared to frameworks like Flask or Django REST Framework, especially when it comes to API declaration, validation, and serialization.

*   **Uvicorn (ASGI Server)**:
    *   **ASGI Standard**: Uvicorn is an ASGI (Asynchronous Server Gateway Interface) server. ASGI is the successor to WSGI and is designed for asynchronous Python web frameworks like FastAPI and Starlette.
    *   **Performance**: It\'s a lightning-fast server, built using `uvloop` (a fast asyncio event loop drop-in) and `httptools` (a fast HTTP parser).
    *   **Compatibility**: It\'s the recommended server for FastAPI and Starlette applications, ensuring seamless integration.
    *   **Lightweight**: Uvicorn is focused on being a high-performance ASGI server without unnecessary bloat, making it ideal for microservices and APIs.

| Feature             | WSGI                                      | ASGI                                                 |
| :------------------ | :---------------------------------------- | :--------------------------------------------------- |
| **Paradigm**        | Synchronous                               | Asynchronous                                         |
| **Primary Use**     | Traditional request-response HTTP         | Request-response, WebSockets, long-lived connections |
| **Concurrency**     | Relies on threads/processes for scaling   | Native `async/await` for I/O-bound concurrency     |
| **Python Features** | Standard Python                           | Leverages `asyncio`, `async/await`                   |
| **Servers**         | Gunicorn, uWSGI (WSGI mode), Waitress     | Uvicorn, Daphne, Hypercorn                           |
| **Frameworks**      | Flask, Django (traditional), Pyramid      | FastAPI, Starlette, Quart, Django (async/Channels)   |

WSGI is still widely used and perfectly fine for many traditional web applications. However, for applications requiring high concurrency for I/O-bound tasks, real-time features like WebSockets, or leveraging modern Python async capabilities, ASGI is the more suitable and performant choice. Frameworks like FastAPI are built from the ground up on ASGI to take full advantage of these benefits.
**Comparison with Other Frameworks**:

*   **vs. Flask**:
    *   Flask is a highly respected micro-framework, very flexible but requires more manual setup or extensions for features that FastAPI provides out-of-the-box. For example:
        *   Data validation often uses libraries like Marshmallow or Werkzeug, requiring more explicit setup.
        *   Async support typically involves using Quart (a Flask-like ASGI framework) or more complex configurations with WSGI servers like Gunicorn + gevent/eventlet.
        *   API documentation usually needs third-party packages like Flasgger.
    *   FastAPI provides these features with a more integrated and often more performant approach, especially for async workloads. Pydantic integration in FastAPI is generally considered more modern and developer-friendly for data tasks.

*   **vs. Django (and Django REST Framework - DRF)**:
    *   Django is a full-featured "batteries-included" framework, excellent for larger, more complex applications, especially those that are database-centric (thanks to its powerful ORM) and require features like an admin panel, user authentication system, etc., out of the box.
    *   DRF is a powerful and mature toolkit for building Web APIs with Django, offering extensive features for serialization, authentication, permissions, and more.
    *   FastAPI is generally more lightweight and can be faster to get started with for pure API development or microservices. Its performance, especially with async, is often higher due to its ASGI-native design.
    *   While Django has significantly improved its async support, FastAPI was designed for async from the ground up.
    *   For simple APIs or when maximum performance and modern async features are key, FastAPI often feels less "heavy" and more direct than Django/DRF.

*   **vs. Other ASGI Servers (like Hypercorn, Daphne)**:
    *   Uvicorn is widely adopted, well-maintained, and specifically recommended by FastAPI. It strikes an excellent balance between raw performance, ease of use, and stability.
    *   Hypercorn is another excellent ASGI server that supports more features (e.g., HTTP/2 and HTTP/3 directly, Trio event loop support, serverless deployments), but Uvicorn is often sufficient and simpler for many common use cases.
    *   Daphne is primarily known for its use with Django Channels for handling WebSockets and other long-lived connections in Django applications.

**Choice Justification for this Project**:
Given the requirements for a *simple web service* with a couple of APIs, and the need to *run and test code efficiently*, FastAPI + Uvicorn is an excellent choice because:
1.  **Speed of Development**: Automatic validation, serialization, and API documentation mean less boilerplate code and faster iteration cycles.
2.  **High Performance**: Ensures the service is responsive and can handle concurrent requests efficiently due to its async nature.
3.  **Ease of Use & Modernity**: Leverages modern Python features (type hints, async/await) and has a clear, intuitive syntax.
4.  **Excellent Testability**: FastAPI\'s design and tools like `TestClient` (or `AsyncClient` with `httpx` for async tests) make writing unit and integration tests straightforward and effective.

**UV for Tooling**:
UV was chosen for environment and package management because:
1.  **Speed**: It is significantly faster than `pip` and `virtualenv` for creating environments and installing/resolving packages.
2.  **Simplicity**: It aims to provide a unified, fast tool for common Python packaging tasks.
3.  **Modern Approach**: It's a new tool gaining traction for its performance and potential to simplify Python workflows.

This combination allows for a productive and efficient development experience, especially for building APIs.
