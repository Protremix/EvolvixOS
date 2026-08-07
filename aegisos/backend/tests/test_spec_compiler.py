"""
Tests for the Spec-Driven Compiler.
"""

import json
import pytest

from app.services.spec_compiler import (
    SpecCompiler, ModelSpec, EndpointSpec, FieldSpec,
)


SAMPLE_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0",
        "description": "A test API spec",
    },
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers",
                "summary": "List all users",
                "tags": ["users"],
                "parameters": [
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "offset", "in": "query", "required": False, "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserList"}
                            }
                        }
                    }
                }
            },
            "post": {
                "operationId": "createUser",
                "summary": "Create a user",
                "tags": ["users"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateUserRequest"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    }
                }
            }
        },
        "/users/{user_id}": {
            "get": {
                "operationId": "getUser",
                "summary": "Get a user by ID",
                "tags": ["users"],
                "parameters": [
                    {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    }
                }
            },
            "delete": {
                "operationId": "deleteUser",
                "summary": "Delete a user",
                "tags": ["users"],
                "parameters": [
                    {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"204": {}},
            }
        }
    },
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "description": "A user model",
                "properties": {
                    "id": {"type": "string", "format": "uuid", "description": "User UUID"},
                    "email": {"type": "string", "format": "email", "minLength": 5, "maxLength": 255},
                    "name": {"type": "string", "minLength": 1, "maxLength": 100},
                    "age": {"type": "integer", "minimum": 0, "maximum": 150},
                    "isActive": {"type": "boolean", "default": True},
                    "roles": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "email", "name"],
            },
            "CreateUserRequest": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string"},
                },
                "required": ["email", "name"],
            },
            "UserList": {
                "type": "object",
                "properties": {
                    "users": {"type": "array", "items": {"$ref": "#/components/schemas/User"}},
                    "total": {"type": "integer"},
                },
                "required": ["users", "total"],
            }
        }
    }
}

SAMPLE_ASYNCAPI = {
    "asyncapi": "2.0.0",
    "info": {"title": "Event API", "version": "1.0.0"},
    "channels": {
        "user.created": {
            "subscribe": {
                "operationId": "onUserCreated",
                "summary": "User created event",
                "message": {
                    "$ref": "#/components/messages/UserEvent"
                }
            }
        }
    },
    "components": {
        "messages": {
            "UserEvent": {
                "payload": {"$ref": "#/components/schemas/UserEventPayload"}
            }
        },
        "schemas": {
            "UserEventPayload": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string"},
                    "eventType": {"type": "string", "enum": ["created", "updated", "deleted"]},
                },
                "required": ["userId", "eventType"],
            }
        }
    }
}


class TestSpecCompiler:
    """Test the spec-driven compiler."""

    def test_compile_openapi(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        assert result["stats"]["total_models"] == 3
        assert result["stats"]["total_endpoints"] == 4
        assert result["stats"]["spec_format"] == "openapi"

    def test_compile_openapi_info(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        assert result["info"]["title"] == "Test API"
        assert result["info"]["version"] == "1.0.0"

    def test_parse_models(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        model_names = [m["name"] for m in result["models"]]
        assert "User" in model_names
        assert "CreateUserRequest" in model_names
        assert "UserList" in model_names

    def test_parse_model_fields(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        user_model = next(m for m in result["models"] if m["name"] == "User")
        field_names = [f["name"] for f in user_model["fields"]]
        assert "id" in field_names
        assert "email" in field_names
        assert "name" in field_names
        assert "isActive" in field_names
        assert "roles" in field_names

    def test_required_fields(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        user_model = next(m for m in result["models"] if m["name"] == "User")
        id_field = next(f for f in user_model["fields"] if f["name"] == "id")
        assert id_field["required"] is True
        age_field = next(f for f in user_model["fields"] if f["name"] == "age")
        assert age_field["required"] is False

    def test_array_field(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        user_model = next(m for m in result["models"] if m["name"] == "User")
        roles_field = next(f for f in user_model["fields"] if f["name"] == "roles")
        assert roles_field["type"] == "array"
        assert roles_field["items_type"] == "string"

    def test_reference_field(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        user_list = next(m for m in result["models"] if m["name"] == "UserList")
        users_field = next(f for f in user_list["fields"] if f["name"] == "users")
        assert users_field["type"] == "array"
        assert users_field["items_type"] == "User"

    def test_parse_endpoints(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        paths = [e["path"] for e in result["endpoints"]]
        assert "/users" in paths
        assert "/users/{user_id}" in paths

    def test_endpoint_methods(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        methods = [(e["path"], e["method"]) for e in result["endpoints"]]
        assert ("/users", "GET") in methods
        assert ("/users", "POST") in methods
        assert ("/users/{user_id}", "GET") in methods
        assert ("/users/{user_id}", "DELETE") in methods

    def test_endpoint_request_body(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        post_ep = next(e for e in result["endpoints"] if e["method"] == "POST")
        assert post_ep["request_body"] == "CreateUserRequest"

    def test_endpoint_response_model(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        get_ep = next(e for e in result["endpoints"] if e["path"] == "/users" and e["method"] == "GET")
        assert get_ep["response_model"] == "UserList"

    def test_endpoint_parameters(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        get_ep = next(e for e in result["endpoints"] if e["path"] == "/users" and e["method"] == "GET")
        param_names = [p["name"] for p in get_ep["parameters"]]
        assert "limit" in param_names
        assert "offset" in param_names

    def test_generate_pydantic_models(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        assert "models.py" in result["generated_code"]
        code = result["generated_code"]["models.py"]
        assert "class User(BaseModel)" in code
        assert "class CreateUserRequest(BaseModel)" in code
        assert "id:" in code
        assert "email:" in code

    def test_generate_fastapi_routes(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        assert "routes.py" in result["generated_code"]
        code = result["generated_code"]["routes.py"]
        assert "router.get" in code
        assert "router.post" in code
        assert "router.delete" in code
        assert "listUsers" in code or "list_users" in code
        assert "createUser" in code or "create_user" in code

    def test_generate_ts_types(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_OPENAPI, "openapi")
        assert "types.ts" in result["generated_code"]
        code = result["generated_code"]["types.ts"]
        assert "interface User" in code
        assert "interface CreateUserRequest" in code

    def test_compile_asyncapi(self):
        compiler = SpecCompiler()
        result = compiler.compile(SAMPLE_ASYNCAPI, "asyncapi")
        assert result["stats"]["spec_format"] == "asyncapi"
        assert result["stats"]["total_models"] >= 1
        assert result["stats"]["total_endpoints"] >= 1

    def test_compile_from_string(self):
        compiler = SpecCompiler()
        result = compiler.compile(json.dumps(SAMPLE_OPENAPI), "openapi")
        assert result["stats"]["total_models"] == 3

    def test_snake_case_conversion(self):
        compiler = SpecCompiler()
        assert compiler._to_snake_case("UserModel") == "user_model"
        assert compiler._to_snake_case("CreateUserRequest") == "create_user_request"
        assert compiler._to_snake_case("HTTPError") == "http_error"

    def test_empty_spec(self):
        compiler = SpecCompiler()
        result = compiler.compile({}, "openapi")
        assert result["stats"]["total_models"] == 0
        assert result["stats"]["total_endpoints"] == 0

    def test_unsupported_format(self):
        compiler = SpecCompiler()
        with pytest.raises(ValueError):
            compiler.compile({}, "graphql")


class TestSpecCompilerAPI:
    """Test the spec compiler API endpoints."""

    def test_compile_unauthorized(self, client):
        response = client.post("/api/v1/spec-compiler/compile", json={"spec": {}, "spec_format": "openapi"})
        assert response.status_code == 401

    def test_info_unauthorized(self, client):
        response = client.get("/api/v1/spec-compiler/info")
        assert response.status_code == 401

    def test_compile_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/spec-compiler/compile", json={
            "spec": SAMPLE_OPENAPI,
            "spec_format": "openapi",
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_models"] == 3
        assert data["stats"]["total_endpoints"] == 4
        assert "models.py" in data["generated_code"]

    def test_compile_string_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/spec-compiler/compile-string", json={
            "spec_json": json.dumps(SAMPLE_OPENAPI),
            "spec_format": "openapi",
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["stats"]["total_models"] == 3

    def test_compile_string_invalid_json(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/spec-compiler/compile-string", json={
            "spec_json": "not valid json",
            "spec_format": "openapi",
        }, headers=headers)
        assert response.status_code == 400

    def test_info_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.get("/api/v1/spec-compiler/info", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data["supported_formats"]
        assert "pydantic_models" in data["output_types"]

    def test_validate_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/spec-compiler/validate", json={
            "spec": SAMPLE_OPENAPI,
            "spec_format": "openapi",
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_compile_asyncapi_authorized(self, client, test_user):
        headers = test_user["headers"]
        response = client.post("/api/v1/spec-compiler/compile", json={
            "spec": SAMPLE_ASYNCAPI,
            "spec_format": "asyncapi",
        }, headers=headers)
        assert response.status_code == 200
        assert response.json()["stats"]["spec_format"] == "asyncapi"
