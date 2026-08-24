"""Entity management — JSON schema → auto CRUD API (Base44-style).
Supports: per-app scoping, entity relations (foreign keys), relation field type."""
import json
import re
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class EntityManager:
    """Manages entity schemas and auto-generates database tables."""

    @staticmethod
    def validate_entity_name(name: str) -> bool:
        if not name or len(name) > 100:
            return False
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))

    @staticmethod
    def validate_schema(schema: dict) -> tuple[bool, str]:
        if not isinstance(schema, dict):
            return False, "Schema must be a dict"
        if "properties" not in schema:
            return False, "Schema must have 'properties'"
        if "type" not in schema or schema["type"] != "object":
            return False, "Schema type must be 'object'"
        props = schema["properties"]
        if not isinstance(props, dict):
            return False, "Properties must be a dict"

        valid_types = {"string", "integer", "number", "boolean", "array", "object", "file", "image", "relation"}
        for field_name, field_def in props.items():
            if not isinstance(field_def, dict):
                return False, f"Field '{field_name}' must be a dict"
            if "type" not in field_def:
                return False, f"Field '{field_name}' must have a type"
            if field_def["type"] not in valid_types:
                return False, f"Field '{field_name}' has invalid type '{field_def['type']}'"
            # Validate relation fields
            if field_def["type"] == "relation":
                if "relation" not in field_def:
                    return False, f"Relation field '{field_name}' must have 'relation' property"
                rel = field_def["relation"]
                if not isinstance(rel, dict) or "target" not in rel:
                    return False, f"Relation field '{field_name}' must specify 'relation.target'"

        return True, "Valid"

    @staticmethod
    def schema_to_sql_columns(schema: dict) -> str:
        type_map = {
            "string": "TEXT", "integer": "INTEGER", "number": "REAL",
            "boolean": "BOOLEAN", "array": "JSONB", "object": "JSONB",
            "file": "TEXT", "image": "TEXT", "relation": "INTEGER",
        }
        columns = []
        props = schema.get("properties", {})

        for field_name, field_def in props.items():
            sql_type = type_map.get(field_def["type"], "TEXT")
            default = ""
            if "default" in field_def:
                val = field_def["default"]
                if isinstance(val, str):
                    default = f" DEFAULT '{val}'"
                elif isinstance(val, bool):
                    default = f" DEFAULT {str(val).lower()}"
                elif val is None:
                    pass
                else:
                    default = f" DEFAULT {val}"

            col_def = f'"{field_name}" {sql_type}{default}'
            columns.append(col_def)

            # Add foreign key for relation fields
            if field_def["type"] == "relation":
                target_entity = field_def["relation"]["target"]
                target_table = f"entity_{target_entity.lower()}"
                fk_name = f"fk_{field_name}_{target_table}"
                col_def_fk = f'CONSTRAINT {fk_name} FOREIGN KEY ("{field_name}") REFERENCES {target_table}(id) ON DELETE SET NULL'
                columns.append(col_def_fk)

        return ",\n  ".join(columns)

    @staticmethod
    async def create_entity(db: AsyncSession, name: str, schema: dict, created_by: str = None, app_id: int = None):
        if not EntityManager.validate_entity_name(name):
            raise ValueError(f"Invalid entity name '{name}'. Must be PascalCase.")
        valid, msg = EntityManager.validate_schema(schema)
        if not valid:
            raise ValueError(msg)

        # Check if entity already exists (scoped to app if app_id provided)
        if app_id:
            result = await db.execute(
                text("SELECT id FROM platform_entities WHERE name = :name AND app_id = :app_id"),
                {"name": name, "app_id": app_id}
            )
        else:
            result = await db.execute(
                text("SELECT id FROM platform_entities WHERE name = :name AND (app_id IS NULL OR app_id = 0)"),
                {"name": name}
            )
        if result.fetchone():
            raise ValueError(f"Entity '{name}' already exists")

        # Insert schema record with app_id
        await db.execute(
            text("""
                INSERT INTO platform_entities (name, schema, created_by, app_id)
                VALUES (:name, :schema, :created_by, :app_id)
            """),
            {"name": name, "schema": json.dumps(schema), "created_by": created_by, "app_id": app_id}
        )

        # Create database table
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
    async def list_entities(db: AsyncSession, app_id: int = None):
        """List entity schemas, optionally scoped to an app."""
        if app_id:
            result = await db.execute(
                text("SELECT name, schema, created_date, app_id FROM platform_entities WHERE app_id = :app_id ORDER BY created_date DESC"),
                {"app_id": app_id}
            )
        else:
            result = await db.execute(
                text("SELECT name, schema, created_date, app_id FROM platform_entities ORDER BY created_date DESC")
            )
        rows = result.fetchall()
        return [
            {
                "name": row[0],
                "schema": row[1] if isinstance(row[1], dict) else json.loads(row[1]),
                "created_date": row[2].isoformat() if row[2] else None,
                "app_id": row[3]
            }
            for row in rows
        ]

    @staticmethod
    async def get_entity(db: AsyncSession, name: str, app_id: int = None):
        """Get entity schema by name, optionally scoped to app."""
        if app_id:
            result = await db.execute(
                text("SELECT name, schema FROM platform_entities WHERE name = :name AND app_id = :app_id"),
                {"name": name, "app_id": app_id}
            )
        else:
            result = await db.execute(
                text("SELECT name, schema FROM platform_entities WHERE name = :name"),
                {"name": name}
            )
        row = result.fetchone()
        if not row:
            return None
        return {"name": row[0], "schema": row[1] if isinstance(row[1], dict) else json.loads(row[1])}

    @staticmethod
    async def delete_entity(db: AsyncSession, name: str, app_id: int = None):
        result = await db.execute(text(f"SELECT COUNT(*) FROM entity_{name.lower()}"))
        count = result.scalar()
        if count and count > 0:
            raise ValueError(f"Cannot delete entity '{name}': {count} records exist")

        await db.execute(text(f"DROP TABLE IF EXISTS entity_{name.lower()}"))
        if app_id:
            await db.execute(text("DELETE FROM platform_entities WHERE name = :name AND app_id = :app_id"), {"name": name, "app_id": app_id})
        else:
            await db.execute(text("DELETE FROM platform_entities WHERE name = :name"), {"name": name})
        await db.commit()
        return {"message": f"Entity '{name}' deleted"}

    @staticmethod
    async def update_entity(db: AsyncSession, name: str, schema: dict, app_id: int = None):
        valid, msg = EntityManager.validate_schema(schema)
        if not valid:
            raise ValueError(msg)

        old = await EntityManager.get_entity(db, name, app_id)
        if not old:
            raise ValueError(f"Entity '{name}' not found")

        old_props = old["schema"].get("properties", {})
        new_props = schema.get("properties", {})

        type_map = {
            "string": "TEXT", "integer": "INTEGER", "number": "REAL",
            "boolean": "BOOLEAN", "array": "JSONB", "object": "JSONB", "relation": "INTEGER",
        }

        for field_name, field_def in new_props.items():
            if field_name not in old_props:
                sql_type = type_map.get(field_def["type"], "TEXT")
                await db.execute(text(f'ALTER TABLE entity_{name.lower()} ADD COLUMN "{field_name}" {sql_type}'))
                # Add FK for new relation fields
                if field_def["type"] == "relation":
                    target = field_def["relation"]["target"]
                    await db.execute(text(
                        f'ALTER TABLE entity_{name.lower()} ADD CONSTRAINT fk_{field_name}_entity_{target.lower()} '
                        f'FOREIGN KEY ("{field_name}") REFERENCES entity_{target.lower()}(id) ON DELETE SET NULL'
                    ))

        if app_id:
            await db.execute(
                text("UPDATE platform_entities SET schema = :schema, updated_date = NOW() WHERE name = :name AND app_id = :app_id"),
                {"name": name, "schema": json.dumps(schema), "app_id": app_id}
            )
        else:
            await db.execute(
                text("UPDATE platform_entities SET schema = :schema, updated_date = NOW() WHERE name = :name"),
                {"name": name, "schema": json.dumps(schema)}
            )
        await db.commit()
        return {"name": name, "schema": schema, "message": f"Entity '{name}' updated"}

    @staticmethod
    async def get_relations(db: AsyncSession, entity_name: str):
        """Get all relation fields for an entity — used for fetching related records."""
        entity = await EntityManager.get_entity(db, entity_name)
        if not entity:
            return []
        relations = []
        for field_name, field_def in entity["schema"].get("properties", {}).items():
            if field_def.get("type") == "relation":
                relations.append({
                    "field": field_name,
                    "target": field_def["relation"]["target"],
                    "label": field_def.get("relation", {}).get("label", field_name),
                    "display": field_def.get("relation", {}).get("display", "name")
                })
        return relations

    @staticmethod
    async def fetch_with_relations(db: AsyncSession, entity_name: str, record_id: int):
        """Fetch a record and expand all relation fields with related data."""
        entity = await EntityManager.get_entity(db, entity_name)
        if not entity:
            return None

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

        # Expand relation fields
        for field_name, field_def in entity["schema"].get("properties", {}).items():
            if field_def.get("type") == "relation" and record.get(field_name):
                target = field_def["relation"]["target"]
                display_field = field_def.get("relation", {}).get("display", "name")
                target_table = f"entity_{target.lower()}"
                try:
                    rel_result = await db.execute(
                        text(f"SELECT * FROM {target_table} WHERE id = :id"),
                        {"id": record[field_name]}
                    )
                    rel_row = rel_result.fetchone()
                    if rel_row:
                        rel_cols = rel_result.keys() if hasattr(rel_result, 'keys') else [d[0] for d in rel_result.cursor.description]
                        rel_record = {}
                        for j, c in enumerate(rel_cols):
                            v = rel_row[j]
                            if isinstance(v, datetime):
                                v = v.isoformat()
                            rel_record[c] = v
                        record[f"_rel_{field_name}"] = rel_record
                        record[f"_rel_{field_name}_label"] = rel_record.get(display_field, f"#{record[field_name]}")
                except Exception:
                    pass

        return record


class EntityCRUD:
    """CRUD operations for entity records."""

    @staticmethod
    async def list_records(db: AsyncSession, entity_name: str, limit: int = 50, skip: int = 0, filters: dict = None, sort: str = None, expand_relations: bool = False):
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

        # Expand relations if requested
        if expand_relations and records:
            entity = await EntityManager.get_entity(db, entity_name)
            if entity:
                for record in records:
                    for field_name, field_def in entity["schema"].get("properties", {}).items():
                        if field_def.get("type") == "relation" and record.get(field_name):
                            target = field_def["relation"]["target"]
                            display_field = field_def.get("relation", {}).get("display", "name")
                            target_table = f"entity_{target.lower()}"
                            try:
                                rel_result = await db.execute(
                                    text(f"SELECT * FROM {target_table} WHERE id = :id"),
                                    {"id": record[field_name]}
                                )
                                rel_row = rel_result.fetchone()
                                if rel_row:
                                    rel_cols = rel_result.keys() if hasattr(rel_result, 'keys') else [d[0] for d in rel_result.cursor.description]
                                    rel_record = {}
                                    for j, c in enumerate(rel_cols):
                                        v = rel_row[j]
                                        if isinstance(v, datetime):
                                            v = v.isoformat()
                                        rel_record[c] = v
                                    record[f"_rel_{field_name}"] = rel_record
                                    record[f"_rel_{field_name}_label"] = rel_record.get(display_field, f"#{record[field_name]}")
                            except Exception:
                                pass

        count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
        total = count_result.scalar()

        return {"records": records, "total": total, "has_more": (skip + limit) < total}

    @staticmethod
    async def get_record(db: AsyncSession, entity_name: str, record_id: int):
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
    async def create_record(db: AsyncSession, entity_name: str, data: dict, user_id: str = None):
        table = f"entity_{entity_name.lower()}"
        cols = list(data.keys())
        placeholders = ", ".join([f":{c}" for c in cols])
        col_list = ", ".join([f'"{c}"' for c in cols])
        if user_id:
            col_list += ', "created_by"'
            placeholders += ", :created_by"

        query = f'INSERT INTO {table} ({col_list}) VALUES ({placeholders}) RETURNING *'
        params = dict(data)
        if user_id:
            params["created_by"] = user_id

        result = await db.execute(text(query), params)
        row = result.fetchone()
        await db.commit()
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
    async def update_record(db: AsyncSession, entity_name: str, record_id: int, data: dict):
        table = f"entity_{entity_name.lower()}"
        set_clauses = ", ".join([f'"{k}" = :{k}' for k in data.keys()])
        set_clauses += ', "updated_date" = NOW()'
        query = f'UPDATE {table} SET {set_clauses} WHERE id = :id RETURNING *'
        params = dict(data)
        params["id"] = record_id

        result = await db.execute(text(query), params)
        row = result.fetchone()
        await db.commit()
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
    async def delete_record(db: AsyncSession, entity_name: str, record_id: int):
        table = f"entity_{entity_name.lower()}"
        await db.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": record_id})
        await db.commit()
        return {"message": f"Record {record_id} deleted"}
