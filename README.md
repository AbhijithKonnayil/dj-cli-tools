# dj-cli-tools
![dj-cli-tools Banner](banner.png)
**dj-cli-tools** is a command-line utility for Django developers designed to streamline the process of creating applications and managing boilerplate code. It extends Django's built-in management commands to provide enhanced scaffolding capabilities, particularly focused on Django REST Framework (DRF) workflows.

## Features

*   **Enhanced `start_app`**: Create new Django applications using custom, pre-configured templates (e.g., versioned REST API structures). **Automatically registers the new app in `INSTALLED_APPS`** in your project's `settings.py`.
*   **`create`**: A powerhouse command that generates a fully functional vertical slice for a new resource. One command creates:
    *   **Model**: Custom model definition.
    *   **Serializer**: Corresponding `ModelSerializer`.
    *   **ViewSet**: `ModelViewSet` with standard import.
    *   **Factory**: `factory_boy` factory for testing.
    *   **Admin**: Registers the model in `admin.py`.
    *   **URLs**: Registers the ViewSet in `urls.py`.

## Installation

```bash
pip install dj-cli-tools
```

Or for local development:

```bash
git clone https://github.com/AbhijithKonnayil/dj-cli-tools
cd dj-cli-tools
pip install .
```

## Usage

### 1. Starting a New App
Create a new app using a specific template. This command acts like `startapp` but better:

```bash
python manage.py start_app <app_name> --dj_template <template_name>
```

**Example:**
To create a REST API app:
```bash
python manage.py start_app core_api --dj_template simple_drf
```

**What happens?**
*   The `core_api` directory is created with the structure defined in `simple_drf`.
*   The app is automatically added to `INSTALLED_APPS` in `settings.py` (e.g., `'core_api.apps.CoreApiConfig'`).

### 2. Creating a Resource (Model, API, & More)
Generate the full stack for a new domain model in an existing app.

```bash
python manage.py create <app_name> <ModelName>
```

**Example:**
```bash
python manage.py create core_api Product
```

**What happens?**
This single command will:
1.  **Model**: Append `class Product(models.Model): ...` to `core_api/models.py`.
2.  **Serializer**: Create `ProductSerializer` in `core_api/serializers.py` with necessary imports.
3.  **Views**: Create `ProductViewSet` in `core_api/views.py`.
4.  **URLs**: Register `ProductViewSet` with a router in `core_api/urls.py` (e.g., `router.register(r'products', ProductViewSet)`).
5.  **Admin**: Register `Product` in `core_api/admin.py`.
6.  **Factories**: Create `ProductFactory` in `core_api/factories.py`.

## Requirements

*   Python 3.10+
*   Django 5.2+

## License

BSD-3-Clause
