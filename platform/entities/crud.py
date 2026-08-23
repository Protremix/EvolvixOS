"""Enhanced Entity CRUD — Base44-style filtering, RLS, aggregation."""
import json
import re
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class EntityCRUD:
    """CRUD operations with advanced filtering, RLS, and aggregation."""

    VALID_OPERATORS = {"eq", "in", "not_in", "like", "gt", "gte", "lt", "lte", "ne"}

    @staticmethod
    async def list_records(
        db: AsyncSession, entity_name: str,
        limit: int = 50, skip: int = 0,
        filters: dict = None, sort: str = None,
        user_id: str = None, rls_enabled: bool = False
    ):
        """List records with filtering, pagination, sorting, and RLS."""
        table = f"entity_{entity_name.lower()}"
        query = f"SELECT * FROM {table} WHERE 1=1"
        params = {"limit": limit, "offset": skip}

        # Row-level security
        if rls_enabled and user_id:
            query += ' AND "created_by" = :rls_user'
            params["rls_user"] = user_id

        # Advanced filtering with operators
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict) and "operator" in value:
                    op = value["operator"]
                    val = value["value"]
                    if op == "eq":
                        query += f' AND "{key}" = :{key}'
                        params[key] = val
                    elif op == "ne":
                        query += f' AND "{key}" != :{key}'
                        params[key] = val
                    elif op == "gt":
                        query += f' AND "{key}" > :{key}'
                        params[key] = val
                    elif op == "gte":
                        query += f' AND "{key}" >= :{key}'
                        params[key] = val
                    elif op == "lt":
                        query += f' AND "{key}" < :{key}'
                        params[key] = val
                    elif op == "lte":
                        query += f' AND "{key}" <= :{key}'
                        params[key] = val
                    elif op == "like":
                        query += f' AND "{key}" LIKE :{key}'
                        params[key] = f"%{val}%"
                    elif op == "in" and isinstance(val, list):
                        placeholders = ", ".join([f":{key}_{i}" for i in range(len(val))])
                        query += f' AND "{key}" IN ({placeholders})'
                        for i, v in enumerate(val):
                            params[f"{key}_{i}"] = v
                    elif op == "not_in" and isinstance(val, list):
                        placeholders = ", ".join([f":{key}_{i}" for i in range(len(val))])
                        query += f' AND "{key}" NOT IN ({placeholders})'
                        for i, v in enumerate(val):
                            params[f"{key}_{i}"] = v
                else:
                    query += f' AND "{key}" = :{key}'
                    params[key] = value

        # Sorting
        if sort:
            direction = "DESC" if sort.startswith("-") else "ASC"
            sort_field = sort.lstrip("-")
            query += f' ORDER BY "{sort_field}" {direction}'
        else:
            query += " ORDER BY created_date DESC"

        query += " LIMIT :limit OFFSET :offset"

        result = await db.execute(text(query), params)
        rows = result.fetchall()
        col_names = list(result.keys())

        records = []
        for row in rows:
            record = {}
            for i, col in enumerate(col_names):
                val = row[i]
                if isinstance(val, datetime):
                    val = val.isoformat()
                record[col] = val
            records.append(record)

        count_query = f"SELECT COUNT(*) FROM {table} WHERE 1=1"
        if rls_enabled and user_id:
            count_query += ' AND "created_by" = :rls_user'
        count_result = await db.execute(text(count_query), 
            {"rls_user": user_id} if rls_enabled and user_id else {})
        total = count_result.scalar()

        return {"records": records, "total": total, "has_more": (skip + limit) < total}

    @staticmethod
    async def get_record(db: AsyncSession, entity_name: str, record_id: int, user_id: str = None, rls_enabled: bool = False):
        table = f"entity_{entity_name.lower()}"
        query = f"SELECT * FROM {table} WHERE id = :id"
        params = {"id": record_id}
        if rls_enabled and user_id:
            query += ' AND "created_by" = :rls_user'
            params["rls_user"] = user_id
        result = await db.execute(text(query), params)
        row = result.fetchone()
        if not row:
            return None
        col_names = list(result.keys())
        record = {}
        for i, col in enumerate(col_names):
            val = row[i]
            if isinstance(val, datetime):
                val = val.isoformat()
            record[col] = val
        return record

    @staticmethod
    async def create_record(db: AsyncSession, entity_name: str, data: dict, created_by: str = None):
        table = f"entity_{entity_name.lower()}"
        from .manager import EntityManager
        entity = await EntityManager.get_entity(db, entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")
        props = entity["schema"].get("properties", {})
        required = entity["schema"].get("required", [])
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: '{field}'")
        fields, values, placeholders = [], {}, []
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
        return {"id": row[0], "created_date": row[1].isoformat() if row[1] else None,
                "updated_date": row[2].isoformat() if row[2] else None, "created_by": created_by, **data}

    @staticmethod
    async def update_record(db: AsyncSession, entity_name: str, record_id: int, data: dict, user_id: str = None, rls_enabled: bool = False):
        table = f"entity_{entity_name.lower()}"
        from .manager import EntityManager
        entity = await EntityManager.get_entity(db, entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")
        props = entity["schema"].get("properties", {})
        set_clauses, params = [], {"id": record_id}
        for i, (key, value) in enumerate(data.items()):
            if key in props:
                param_name = f"val_{i}"
                set_clauses.append(f'"{key}" = :{param_name}')
                params[param_name] = json.dumps(value) if isinstance(value, (dict, list)) else value
        set_clauses.append('updated_date = NOW()')
        rls_clause = ""
        if rls_enabled and user_id:
            rls_clause = ' AND "created_by" = :rls_user'
            params["rls_user"] = user_id
        query = f'UPDATE {table} SET {", ".join(set_clauses)} WHERE id = :id{rls_clause} RETURNING id, updated_date'
        result = await db.execute(text(query), params)
        row = result.fetchone()
        if not row:
            raise ValueError(f"Record {record_id} not found or access denied")
        await db.commit()
        return {"id": row[0], "updated_date": row[1].isoformat() if row[1] else None, **data}

    @staticmethod
    async def delete_record(db: AsyncSession, entity_name: str, record_id: int, user_id: str = None, rls_enabled: bool = False):
        table = f"entity_{entity_name.lower()}"
        params = {"id": record_id}
        rls_clause = ""
        if rls_enabled and user_id:
            rls_clause = ' AND "created_by" = :rls_user'
            params["rls_user"] = user_id
        result = await db.execute(text(f"DELETE FROM {table} WHERE id = :id{rls_clause} RETURNING id"), params)
        row = result.fetchone()
        if not row:
            raise ValueError(f"Record {record_id} not found or access denied")
        await db.commit()
        return {"id": record_id, "deleted": True}

    @staticmethod
    async def aggregate(db: AsyncSession, entity_name: str, pipeline: list):
        """Run aggregation pipeline — group by, count, sum, avg, min, max."""
        table = f"entity_{entity_name.lower()}"
        query = f"SELECT "
        group_field = None
        aggregations = []

        for stage in pipeline:
            if "$group" in stage:
                group_config = stage["$group"]
                group_field = group_config.get("_id", "")
                if isinstance(group_field, str):
                    group_field = group_field.replace("$", "").replace("data.", "")
                else:
                    group_field = str(group_field)
                for alias, op in group_config.items():
                    if alias == "_id":
                        continue
                    if isinstance(op, dict):
                        for op_type, field in op.items():
                            field = field.replace("$", "").replace("data.", "") if isinstance(field, str) else str(field)
                            if op_type == "$sum":
                                if field:
                                    aggregations.append(f'SUM("{field}") AS {alias}')
                                else:
                                    aggregations.append(f'COUNT(*) AS {alias}')
                            elif op_type == "$avg":
                                aggregations.append(f'AVG("{field}") AS {alias}')
                            elif op_type == "$min":
                                aggregations.append(f'MIN("{field}") AS {alias}')
                            elif op_type == "$max":
                                aggregations.append(f'MAX("{field}") AS {alias}')
                            elif op_type == "$count":
                                aggregations.append(f'COUNT(*) AS {alias}')
            elif "$sort" in stage:
                sort_config = stage["$sort"]
                sort_clauses = []
                for field, direction in sort_config.items():
                    direction = "DESC" if direction == -1 else "ASC"
                    sort_clauses.append(f'"{field}" {direction}')
                # Will be appended later
                sort_sql = ", ".join(sort_clauses)

        if group_field:
            query += f'"{group_field}", '
        query += ", ".join(aggregations) if aggregations else "COUNT(*)"
        if group_field:
            query += f' FROM {table} GROUP BY "{group_field}"'
        else:
            query += f' FROM {table}'

        # Add sorting if present
        for stage in pipeline:
            if "$sort" in stage:
                sort_config = stage["$sort"]
                sort_clauses = []
                for field, direction in sort_config.items():
                    direction = "DESC" if direction == -1 else "ASC"
                    sort_clauses.append(f'"{field}" {direction}')
                query += f' ORDER BY {", ".join(sort_clauses)}'

        result = await db.execute(text(query))
        rows = result.fetchall()
        col_names = list(result.keys())
        return [{col: row[i] for i, col in enumerate(col_names)} for row in rows]
