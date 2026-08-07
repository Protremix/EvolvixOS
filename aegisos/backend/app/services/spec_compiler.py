"""
Spec-Driven Compiler.

Parses OpenAPI/AsyncAPI specifications and generates AST blueprints
that can be compiled into code scaffolding (models, endpoints, schemas,
route handlers, client SDKs).
"""

import json
import re
import logging
from typing import Any
from dataclasses import dataclass, field
from collections import OrderedDict

logger = logging.getLogger("evolvixos")


@dataclass
class FieldSpec:
    """A field in a model/schema."""
    name: str
    type: str  # string, integer, boolean, float, array, object, reference
    required: bool = True
    description: str = ""
    default: Any = None
    format: str = ""  # date-time, email, uuid, etc.
    items_type: str = ""  # for arrays
    reference: str = ""  # for $ref types
    enum: list = field(default_factory=list)
    min_length: int = 0
    max_length: int = 0
    minimum: Any = None
    maximum: Any = None
    pattern: str = ""


@dataclass
class ModelSpec:
    """A data model from the spec."""
    name: str
    description: str = ""
    fields: list[FieldSpec] = field(default_factory=list)
    table_name: str = ""  # for database mapping
    inherits: str = ""  # parent model if any


@dataclass
class EndpointSpec:
    """An API endpoint from the spec."""
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    operation_id: str = ""
    summary: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    parameters: list[FieldSpec] = field(default_factory=list)
    request_body: str = ""  # reference to model
    response_model: str = ""  # reference to model
    status_codes: list[int] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class CompiledBlueprint:
    """The compiled output — code scaffolding from a spec."""
    models: list[ModelSpec] = field(default_factory=list)
    endpoints: list[EndpointSpec] = field(default_factory=list)
    schemas: dict = field(default_factory=dict)  # raw schema definitions
    info: dict = field(default_factory=dict)
    generated_code: dict[str, str] = field(default_factory=dict)  # filename -> code
    stats: dict = field(default_factory=dict)


class SpecCompiler:
    """Parses OpenAPI/AsyncAPI specs and generates code blueprints."""

    def __init__(self):
        self.blueprint = CompiledBlueprint()

    def compile(self, spec: dict | str, spec_format: str = "openapi") -> dict:
        """Compile a spec into a code blueprint.

        Args:
            spec: OpenAPI/AsyncAPI spec as dict or JSON string
            spec_format: "openapi" or "asyncapi"

        Returns:
            Compiled blueprint as dict
        """
        if isinstance(spec, str):
            spec = json.loads(spec)

        self.blueprint = CompiledBlueprint()

        if spec_format == "openapi":
            self._parse_openapi(spec)
        elif spec_format == "asyncapi":
            self._parse_asyncapi(spec)
        else:
            raise ValueError(f"Unsupported spec format: {spec_format}")

        # Generate code from the blueprint
        self._generate_code()

        # Build stats
        self.blueprint.stats = {
            "total_models": len(self.blueprint.models),
            "total_endpoints": len(self.blueprint.endpoints),
            "total_fields": sum(len(m.fields) for m in self.blueprint.models),
            "generated_files": len(self.blueprint.generated_code),
            "spec_format": spec_format,
            "spec_version": spec.get("openapi", spec.get("asyncapi", "unknown")),
        }

        return self._to_dict()

    def _parse_openapi(self, spec: dict):
        """Parse an OpenAPI spec."""
        # Parse info
        self.blueprint.info = {
            "title": spec.get("info", {}).get("title", "Untitled"),
            "version": spec.get("info", {}).get("version", "1.0.0"),
            "description": spec.get("info", {}).get("description", ""),
        }

        # Parse schemas (models)
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        self.blueprint.schemas = schemas

        for name, schema in schemas.items():
            model = self._parse_schema(name, schema)
            self.blueprint.models.append(model)

        # Parse paths (endpoints)
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    continue
                endpoint = self._parse_endpoint(path, method, operation)
                self.blueprint.endpoints.append(endpoint)

    def _parse_asyncapi(self, spec: dict):
        """Parse an AsyncAPI spec."""
        self.blueprint.info = {
            "title": spec.get("info", {}).get("title", "Untitled"),
            "version": spec.get("info", {}).get("version", "1.0.0"),
            "description": spec.get("info", {}).get("description", ""),
        }

        # Parse channel message schemas
        components = spec.get("components", {})
        schemas = components.get("schemas", components.get("messages", {}))
        self.blueprint.schemas = schemas

        for name, schema in schemas.items():
            model = self._parse_schema(name, schema)
            self.blueprint.models.append(model)

        # Parse channels as endpoints
        channels = spec.get("channels", {})
        for channel_name, channel in channels.items():
            for direction in ("subscribe", "publish"):
                if direction in channel:
                    operation = channel[direction]
                    endpoint = EndpointSpec(
                        path=channel_name,
                        method=direction.upper(),
                        operation_id=operation.get("operationId", f"{direction}_{channel_name}"),
                        summary=operation.get("summary", ""),
                        description=operation.get("description", ""),
                        tags=operation.get("tags", []),
                    )
                    # Parse message
                    msg = operation.get("message", {})
                    if "$ref" in msg:
                        endpoint.response_model = msg["$ref"].split("/")[-1]
                    elif "payload" in msg and "$ref" in msg["payload"]:
                        endpoint.response_model = msg["payload"]["$ref"].split("/")[-1]
                    self.blueprint.endpoints.append(endpoint)

    def _parse_schema(self, name: str, schema: dict) -> ModelSpec:
        """Parse a schema definition into a ModelSpec."""
        model = ModelSpec(
            name=name,
            description=schema.get("description", ""),
            table_name=self._to_snake_case(name),
        )

        # Handle allOf/oneOf/anyOf
        if "allOf" in schema:
            for part in schema["allOf"]:
                if "$ref" in part:
                    model.inherits = part["$ref"].split("/")[-1]
                elif "properties" in part:
                    for field_name, field_spec in part["properties"].items():
                        model.fields.append(self._parse_field(field_name, field_spec, schema.get("required", [])))

        # Regular properties
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field_name, field_spec in properties.items():
            model.fields.append(self._parse_field(field_name, field_spec, required))

        return model

    def _parse_field(self, name: str, field_spec: dict, required: list) -> FieldSpec:
        """Parse a field from schema properties."""
        field = FieldSpec(
            name=name,
            type=field_spec.get("type", "string"),
            required=name in required,
            description=field_spec.get("description", ""),
            default=field_spec.get("default"),
            format=field_spec.get("format", ""),
            pattern=field_spec.get("pattern", ""),
        )

        # Handle $ref
        if "$ref" in field_spec:
            field.reference = field_spec["$ref"].split("/")[-1]
            field.type = "reference"
        elif field.type == "array" and "items" in field_spec:
            items = field_spec["items"]
            if "$ref" in items:
                field.items_type = items["$ref"].split("/")[-1]
            else:
                field.items_type = items.get("type", "string")
        elif field.type == "string":
            field.min_length = field_spec.get("minLength", 0)
            field.max_length = field_spec.get("maxLength", 0)
            field.enum = field_spec.get("enum", [])
        elif field.type in ("integer", "number"):
            field.minimum = field_spec.get("minimum")
            field.maximum = field_spec.get("maximum")

        return field

    def _parse_endpoint(self, path: str, method: str, operation: dict) -> EndpointSpec:
        """Parse an endpoint from an OpenAPI path."""
        endpoint = EndpointSpec(
            path=path,
            method=method.upper(),
            operation_id=operation.get("operationId", ""),
            summary=operation.get("summary", ""),
            description=operation.get("description", ""),
            tags=operation.get("tags", []),
            deprecated=operation.get("deprecated", False),
        )

        # Parse parameters
        for param in operation.get("parameters", []):
            schema = param.get("schema", {})
            field = FieldSpec(
                name=param.get("name", ""),
                type=schema.get("type", "string"),
                required=param.get("required", False),
                description=param.get("description", ""),
                format=schema.get("format", ""),
            )
            endpoint.parameters.append(field)

        # Parse request body
        request_body = operation.get("requestBody", {})
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        if "$ref" in json_content.get("schema", {}):
            endpoint.request_body = json_content["schema"]["$ref"].split("/")[-1]

        # Parse responses
        responses = operation.get("responses", {})
        for status_code, response in responses.items():
            try:
                endpoint.status_codes.append(int(status_code))
            except ValueError:
                endpoint.status_codes.append(0)
            content = response.get("content", {})
            json_content = content.get("application/json", {})
            if "$ref" in json_content.get("schema", {}) and not endpoint.response_model:
                endpoint.response_model = json_content["schema"]["$ref"].split("/")[-1]

        return endpoint

    def _generate_code(self):
        """Generate code files from the blueprint."""
        # Generate Pydantic models
        self.blueprint.generated_code["models.py"] = self._generate_pydantic_models()
        # Generate FastAPI routes
        self.blueprint.generated_code["routes.py"] = self._generate_fastapi_routes()
        # Generate TypeScript interfaces
        self.blueprint.generated_code["types.ts"] = self._generate_ts_types()

    def _generate_pydantic_models(self) -> str:
        """Generate Pydantic model code."""
        lines = [
            '"""',
            f"Auto-generated Pydantic models from {self.blueprint.info.get('title', 'API')} spec.",
            f"Version: {self.blueprint.info.get('version', '1.0.0')}",
            '"""',
            "",
            "from typing import Optional, List, Any",
            "from pydantic import BaseModel, Field",
            "",
            "",
        ]

        for model in self.blueprint.models:
            # Class docstring
            if model.description:
                lines.append(f'"""{model.description}"""')

            # Class definition
            lines.append(f"class {model.name}(BaseModel):")

            if model.inherits:
                lines.append(f"    # Inherits from {model.inherits}")

            if not model.fields:
                lines.append("    pass")
            else:
                for field in model.fields:
                    py_type = self._field_to_py_type(field)
                    default = "" if field.required else " = None"
                    desc = f', description="{field.description}"' if field.description else ""
                    lines.append(f"    {field.name}: {py_type}{default}")
                    if field.description:
                        lines.append(f'    """{field.description}"""')

            lines.append("")
            lines.append("")

        return "\n".join(lines)

    def _generate_fastapi_routes(self) -> str:
        """Generate FastAPI route code."""
        lines = [
            '"""',
            f"Auto-generated FastAPI routes from {self.blueprint.info.get('title', 'API')} spec.",
            '"""',
            "",
            "from fastapi import APIRouter, Depends, HTTPException",
            "from app.api.deps import get_current_active_user",
            "from app.models.user import User",
            "from .models import *",
            "",
            "router = APIRouter()",
            "",
            "",
        ]

        for endpoint in self.blueprint.endpoints:
            # Route decorator
            tags = f', tags={endpoint.tags}' if endpoint.tags else ""
            lines.append(f'@router.{endpoint.method.lower()}("{endpoint.path}"{tags})')

            # Function signature
            params = []
            if endpoint.method in ("POST", "PUT", "PATCH") and endpoint.request_body:
                params.append(f"data: {endpoint.request_body}")
            for param in endpoint.parameters:
                py_type = self._field_to_py_type(param)
                if param.required:
                    params.append(f"{param.name}: {py_type}")
                else:
                    params.append(f"{param.name}: Optional[{py_type}] = None")
            params.append("current_user: User = Depends(get_current_active_user)")

            func_name = endpoint.operation_id or f"{endpoint.method.lower()}_{endpoint.path.strip('/')}"
            func_name = re.sub(r'[^a-zA-Z0-9_]', '_', func_name)

            lines.append(f"async def {func_name}({', '.join(params)}):")
            if endpoint.summary:
                lines.append(f'    """{endpoint.summary}"""')

            # Response
            if endpoint.response_model:
                lines.append(f'    # Returns: {endpoint.response_model}')
                lines.append(f'    # Status codes: {", ".join(str(s) for s in endpoint.status_codes)}')
                lines.append(f"    return {{}}")
            else:
                lines.append(f"    return {{'status': 'ok'}}")

            lines.append("")
            lines.append("")

        return "\n".join(lines)

    def _generate_ts_types(self) -> str:
        """Generate TypeScript interface definitions."""
        lines = [
            f"// Auto-generated TypeScript types from {self.blueprint.info.get('title', 'API')} spec",
            f"// Version: {self.blueprint.info.get('version', '1.0.0')}",
            "",
        ]

        for model in self.blueprint.models:
            lines.append(f"export interface {model.name} {{")
            for field in model.fields:
                ts_type = self._field_to_ts_type(field)
                optional = "" if field.required else "?"
                lines.append(f"  {field.name}{optional}: {ts_type};")
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _field_to_py_type(self, field: FieldSpec) -> str:
        """Convert a field spec to a Python type string."""
        if field.type == "reference":
            return field.reference
        elif field.type == "array":
            return f"List[{self._field_to_py_type(FieldSpec(name='', type=field.items_type, reference=field.items_type if field.items_type[0].isupper() else ''))}]"
        elif field.type == "integer":
            return "int"
        elif field.type == "number":
            return "float"
        elif field.type == "boolean":
            return "bool"
        elif field.type == "object":
            return "dict"
        else:
            return "str"

    def _field_to_ts_type(self, field: FieldSpec) -> str:
        """Convert a field spec to a TypeScript type string."""
        if field.type == "reference":
            return field.reference
        elif field.type == "array":
            return f"{self._ts_type(field.items_type)}[]"
        elif field.type == "integer" or field.type == "number":
            return "number"
        elif field.type == "boolean":
            return "boolean"
        elif field.type == "object":
            return "Record<string, any>"
        else:
            return "string"

    def _ts_type(self, type_name: str) -> str:
        if type_name and type_name[0].isupper():
            return type_name
        elif type_name == "integer" or type_name == "number":
            return "number"
        elif type_name == "boolean":
            return "boolean"
        elif type_name == "object":
            return "Record<string, any>"
        return "string"

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        result = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', result)
        return result.lower()

    def _to_dict(self) -> dict:
        """Serialize the blueprint to a dict for API response."""
        return {
            "models": [
                {
                    "name": m.name,
                    "description": m.description,
                    "fields": [
                        {
                            "name": f.name,
                            "type": f.type,
                            "required": f.required,
                            "description": f.description,
                            "format": f.format,
                            "items_type": f.items_type,
                            "reference": f.reference,
                        }
                        for f in m.fields
                    ],
                    "table_name": m.table_name,
                    "inherits": m.inherits,
                }
                for m in self.blueprint.models
            ],
            "endpoints": [
                {
                    "path": e.path,
                    "method": e.method,
                    "operation_id": e.operation_id,
                    "summary": e.summary,
                    "tags": e.tags,
                    "parameters": [
                        {"name": p.name, "type": p.type, "required": p.required}
                        for p in e.parameters
                    ],
                    "request_body": e.request_body,
                    "response_model": e.response_model,
                    "status_codes": e.status_codes,
                    "deprecated": e.deprecated,
                }
                for e in self.blueprint.endpoints
            ],
            "info": self.blueprint.info,
            "generated_code": self.blueprint.generated_code,
            "stats": self.blueprint.stats,
        }
