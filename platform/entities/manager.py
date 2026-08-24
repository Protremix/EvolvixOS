"""Entity management — JSON schema → auto CRUD API (Base44-style)."""
import json
import re
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class EntityManager:
    """Manages entity schemas and auto-generates database tables."""

    @staticmethod
    def validate_entity_name(name: str) -> bool:
        """Entity name must be PascalCase, alphanumeric."""
        if not name or len(name) > 100:
            return False
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))

    @staticmethod
    def validate_schema(schema: dict) -> tuple[bool, str]:
        """Validate JSON schema for entity."""
        if not isinstance(schema, dict):
            return False, "Schema must be a dict"
        if "properties" not in schema:
            return False, "Schema must have 'properties'"
        if "type" not in schema or schema["type"] != "object":
            return False, "Schema type must be 'object'"
        props = schema["properties"]
        if not isinstance(props, dict):
            return False, "Properties must be a dict"

        valid_types = {"string", "integer", "number", "boolean", "array", "object", "file", "image"}
        for field_name, field_def in props.items():
            if not isinstance(field_def, dict):
                return False, f"Field '{field_name}' must be a dict"
            if "type" not in field_def:
                return False, f"Field '{field_name}' must have a type"
            if field_def["type"] not in valid_types:
                return False, f"Field '{field_name}' has invalid type '{field_def['type']}'"

        return True, "Valid"

    @staticmethod
    def schema_to_sql_columns(schema: dict) -> str:
        """Convert JSON schema properties to SQL column definitions."""
        type_map = {
            "string": "TEXT",
            "integer": "INTEGER",
            "number": "REAL",
            "boolean": "BOOLEAN",
            "array": "JSONB",
            "object": "JSONB",
            "file": "TEXT",
            "image": "TEXT",
        }
        columns = []
        props = schema.get("properties", {})

        for field_name, field_def in props.items():
            sql_type = type_map.get(field_def["type"], "TEXT")
            nullable = "" if field_def.get("required") else " NOT NULL" if field_def.get("required") else ""
            # Default values
            default = ""
            if "default" in field_def:
                val = field_def["default"]
                if isinstance(val, str):
                    default = f" DEFAULT '{val}'"
                elif isinstance(val, bool):
                    default = f" DEFAULT {str(val).lower()}"
                elif val is None:
                    default = ""
                else:
                    default = f" DEFAULT {val}"

            col_def = f'"{field_name}" {sql_type}{default}'
            columns.append(col_def)

        return ",\n  ".join(columns)

    @staticmethod
    async def create_entity(db: AsyncSession, name: str, schema: dict, created_by: str = None):
        """Create a new entity (schema + database table)."""
        if not EntityManager.validate_entity_name(name):
            raise ValueError(f"Invalid entity name '{name}'. Must be PascalCase.")

        valid, msg = EntityManager.validate_schema(schema)
        if not valid:
            raise ValueError(msg)

        # Check if entity already exists
        result = await db.execute(
            text("SELECT id FROM platform_entities WHERE name = :name"),
            {"name": name}
        )
        if result.fetchone():
            raise ValueError(f"Entity '{name}' already exists")

        # Insert schema record
        await db.execute(
            text("""
                INSERT INTO platform_entities (name, schema, created_by)
                VALUES (:name, :schema, :created_by)
            """),
            {"name": name, "schema": json.dumps(schema), "created_by": created_by}
        )

        # Create database table for the entity
        columns = EntityManager.schema_to_sql_columns(schema)
        table_sql = f"""
            CREATE TABLE IF NOT EXISTS entity_{name.lower()} (
                id SERIAL PRIMARY KEY,
                {columns},
                created_date TIMESTAMP DEFAULT NOW(),
                updated_date TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(255)
            )
        """
        await db.execute(text(table_sql))
        await db.commit()

        return {"name": name, "schema": schema, "message": f"Entity '{name}' created successfully"}

    @staticmethod
    async def list_entities(db: AsyncSession):
        """List all entity schemas."""
        result = await db.execute(
            text("SELECT name, schema, created_date FROM platform_entities ORDER BY created_date DESC")
        )
        rows = result.fetchall()
        return [
            {
                "name": row[0],
                "schema": row[1] if isinstance(row[1], dict) else json.loads(row[1]),
                "created_date": row[2].isoformat() if row[2] else None
            }
            for row in rows
        ]

    @staticmethod
    async def get_entity(db: AsyncSession, name: str):
        """Get entity schema by name."""
        result = await db.execute(
            text("SELECT name, schema FROM platform_entities WHERE name = :name"),
            {"name": name}
        )
        row = result.fetchone()
        if not row:
            return None
        return {"name": row[0], "schema": row[1] if isinstance(row[1], dict) else json.loads(row[1])}

    @staticmethod
    async def delete_entity(db: AsyncSession, name: str):
        """Delete entity (schema + table)."""
        # Check if records exist
        result = await db.execute(
            text(f"SELECT COUNT(*) FROM entity_{name.lower()}")
        )
        count = result.scalar()
        if count and count > 0:
            raise ValueError(f"Cannot delete entity '{name}': {count} records exist")

        await db.execute(text(f"DROP TABLE IF EXISTS entity_{name.lower()}"))
        await db.execute(
            text("DELETE FROM platform_entities WHERE name = :name"),
            {"name": name}
        )
        await db.commit()
        return {"message": f"Entity '{name}' deleted"}

    @staticmethod
    async def update_entity(db: AsyncSession, name: str, schema: dict):
        """Update entity schema (add new columns)."""
        valid, msg = EntityManager.validate_schema(schema)
        if not valid:
            raise ValueError(msg)

        # Get old schema
        old = await EntityManager.get_entity(db, name)
        if not old:
            raise ValueError(f"Entity '{name}' not found")

        old_props = old["schema"].get("properties", {})
        new_props = schema.get("properties", {})

        # Add new columns (don't remove existing)
        type_map = {
            "string": "TEXT", "integer": "INTEGER", "number": "REAL",
            "boolean": "BOOLEAN", "array": "JSONB", "object": "JSONB",
        }

        for field_name, field_def in new_props.items():
            if field_name not in old_props:
                sql_type = type_map.get(field_def["type"], "TEXT")
                await db.execute(text(
                    f'ALTER TABLE entity_{name.lower()} ADD COLUMN "{field_name}" {sql_type}'
                ))

        # Update schema record
        await db.execute(
            text("UPDATE platform_entities SET schema = :schema, updated_date = NOW() WHERE name = :name"),
            {"name": name, "schema": json.dumps(schema)}
        )
        await db.commit()
        return {"name": name, "schema": schema, "message": f"Entity '{name}' updated"}


class EntityCRUD:
    """CRUD operations for entity records (Base44-style)."""

    @staticmethod
    async def list_records(db: AsyncSession, entity_name: str, limit: int = 50, skip: int = 0, filters: dict = None, sort: str = None):
        """List entity records with filtering, pagination, and sorting."""
        table = f"entity_{entity_name.lower()}"
        query = f"SELECT * FROM {table} WHERE 1=1"
        params = {"limit": limit, "offset": skip}

        if filters:
            for key, value in filters.items():
                query += f' AND "{key}" = :{key}'
                params[key] = value

        if sort:
            direction = "DESC" if sort.startswith("-") else "ASC"
            sort_field = sort.lstrip("-")
            query += f' ORDER BY "{sort_field}" {direction}'
        else:
            query += " ORDER BY created_date DESC"

        query += " LIMIT :limit OFFSET :offset"

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        # Get column names
        col_names = result.keys() if hasattr(result, 'keys') else [d[0] for d in result.cursor.description]

        records = []
        for row in rows:
            record = {}
            for i, col in enumerate(col_names):
                val = row[i]
                if isinstance(val, datetime):
                    val = val.isoformat()
                record[col] = val
            records.append(record)

        # Check if more records exist
        count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
        total = count_result.scalar()

        return {
            "records": records,
            "total": total,
            "has_more": (skip + limit) < total
        }

    @staticmethod
    async def get_record(db: AsyncSession, entity_name: str, record_id: int):
        """Get a single entity record by ID."""
        table = f"entity_{entity_name.lower()}"
        result = await db.execute(text(f"SELECT * FROM {table} WHERE id = :id"), {"id": record_id})
        row = result.fetchone()
        if not row:
            return None

        col_names = result.keys() if hasattr(result, 'keys') else [d[0] for d in result.cursor.description]
        record = {}
        for i, col in enumerate(col_names):
            val = row[i]
            if isinstance(val, datetime):
                val = val.isoformat()
            record[col] = val
        return record

    @staticmethod
    async def create_record(db: AsyncSession, entity_name: str, data: dict, created_by: str = None):
        """Create a new entity record."""
        table = f"entity_{entity_name.lower()}"

        # Get entity schema for validation
        entity = await EntityManager.get_entity(db, entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")

        props = entity["schema"].get("properties", {})
        required = entity["schema"].get("required", [])

        # Validate required fields
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: '{field}'")

        # Filter to only schema fields
        fields = []
        values = {}
        placeholders = []
        for i, (key, value) in enumerate(data.items()):
            if key in props:
                fields.append(f'"{key}"')
                param_name = f"val_{i}"
                placeholders.append(f":{param_name}")
                values[param_name] = json.dumps(value) if isinstance(value, (dict, list)) else value

        if created_by:
            fields.append('"created_by"')
            placeholders.append(":created_by")
            values["created_by"] = created_by

        if not fields:
            raise ValueError("No valid fields to insert")

        query = f'INSERT INTO {table} ({", ".join(fields)}) VALUES ({", ".join(placeholders)}) RETURNING id, created_date, updated_date'

        result = await db.execute(text(query), values)
        row = result.fetchone()
        await db.commit()

        return {
            "id": row[0],
            "created_date": row[1].isoformat() if row[1] else None,
            "updated_date": row[2].isoformat() if row[2] else None,
            "created_by": created_by,
            **data
        }

    @staticmethod
    async def update_record(db: AsyncSession, entity_name: str, record_id: int, data: dict):
        """Update an entity record."""
        table = f"entity_{entity_name.lower()}"

        # Get entity schema
        entity = await EntityManager.get_entity(db, entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")

        props = entity["schema"].get("properties", {})

        set_clauses = []
        params = {"id": record_id}
        for i, (key, value) in enumerate(data.items()):
            if key in props:
                param_name = f"val_{i}"
                set_clauses.append(f'"{key}" = :{param_name}')
                params[param_name] = json.dumps(value) if isinstance(value, (dict, list)) else value

        set_clauses.append('updated_date = NOW()')

        if not set_clauses:
            raise ValueError("No valid fields to update")

        query = f'UPDATE {table} SET {", ".join(set_clauses)} WHERE id = :id RETURNING id, updated_date'

        result = await db.execute(text(query), params)
        row = result.fetchone()
        if not row:
            raise ValueError(f"Record {record_id} not found")
        await db.commit()

        return {"id": row[0], "updated_date": row[1].isoformat() if row[1] else None, **data}

    @staticmethod
    async def delete_record(db: AsyncSession, entity_name: str, record_id: int):
        """Delete an entity record."""
        table = f"entity_{entity_name.lower()}"
        result = await db.execute(text(f"DELETE FROM {table} WHERE id = :id RETURNING id"), {"id": record_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Record {record_id} not found")
        await db.commit()
        return {"id": record_id, "deleted": True}
