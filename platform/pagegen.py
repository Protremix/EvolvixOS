"""Page Template Generator — auto-generate page layouts from entity schemas."""
import json

class PageGenerator:
    """Generates page layouts for entities: list view, detail view, create form."""

    @staticmethod
    def generate_pages_for_entity(entity_name: str, schema: dict) -> list:
        props = schema.get("properties", {})
        pages = []

        list_columns = []
        for i, (field, ftype) in enumerate(props.items()):
            if i < 6:
                list_columns.append({
                    "field": field,
                    "label": field.replace("_", " ").title(),
                    "type": ftype.get("type", "string"),
                    "sortable": True,
                })
        pages.append({
            "name": entity_name + " List",
            "type": "list",
            "layout": [
                {"component": "header", "props": {"title": entity_name + "s", "subtitle": "Manage your " + entity_name.lower() + "s"}},
                {"component": "datatable", "props": {"entity": entity_name, "columns": list_columns, "searchable": True, "pagination": True, "actions": ["view", "edit", "delete"]}},
                {"component": "button", "props": {"label": "Add " + entity_name, "action": "create", "variant": "primary", "icon": "plus"}}
            ]
        })

        detail_fields = [{"field": f, "label": f.replace("_", " ").title(), "type": t.get("type", "string")} for f, t in props.items()]
        pages.append({
            "name": entity_name + " Detail",
            "type": "detail",
            "layout": [
                {"component": "header", "props": {"title": entity_name + " Details", "showBack": True}},
                {"component": "fieldlist", "props": {"entity": entity_name, "fields": detail_fields}},
                {"component": "actions", "props": {"buttons": ["edit", "delete"]}}
            ]
        })

        form_fields = []
        for field, ftype in props.items():
            ft = ftype.get("type", "string")
            input_type = {"string": "text", "integer": "number", "number": "number", "boolean": "checkbox", "array": "tags", "object": "json", "file": "file", "image": "image"}.get(ft, "text")
            form_fields.append({"field": field, "label": field.replace("_", " ").title(), "type": input_type, "required": field in schema.get("required", [])})
        pages.append({
            "name": "Create " + entity_name,
            "type": "form",
            "layout": [
                {"component": "header", "props": {"title": "Create " + entity_name, "showBack": True}},
                {"component": "form", "props": {"entity": entity_name, "fields": form_fields, "mode": "create"}}
            ]
        })
        return pages

    @staticmethod
    def generate_dashboard_page(entities: list) -> dict:
        cards = [{"component": "statcard", "props": {"entity": e.get("name", ""), "label": e.get("name", "") + "s", "icon": "database"}} for e in entities]
        return {
            "name": "Dashboard",
            "type": "dashboard",
            "layout": [
                {"component": "header", "props": {"title": "Dashboard"}},
                {"component": "grid", "props": {"columns": 4, "children": cards}},
                {"component": "chart", "props": {"type": "bar", "title": "Records Overview"}},
            ]
        }

    @staticmethod
    def get_component_palette() -> list:
        return [
            {"type": "header", "name": "Header", "icon": "type", "props": {"title": "Page Title", "subtitle": ""}},
            {"type": "datatable", "name": "Data Table", "icon": "table", "props": {"entity": "", "columns": [], "searchable": True, "pagination": True}},
            {"type": "form", "name": "Form", "icon": "edit-3", "props": {"entity": "", "fields": [], "mode": "create"}},
            {"type": "statcard", "name": "Stat Card", "icon": "bar-chart", "props": {"entity": "", "label": "Count", "icon": "database"}},
            {"type": "chart", "name": "Chart", "icon": "trending-up", "props": {"type": "bar", "title": "Chart"}},
            {"type": "fieldlist", "name": "Field List", "icon": "list", "props": {"entity": "", "fields": []}},
            {"type": "button", "name": "Button", "icon": "mouse-pointer", "props": {"label": "Button", "action": "", "variant": "primary"}},
            {"type": "grid", "name": "Grid", "icon": "grid", "props": {"columns": 2, "children": []}},
            {"type": "text", "name": "Text", "icon": "feather", "props": {"content": "Text content", "variant": "body"}},
            {"type": "image", "name": "Image", "icon": "image", "props": {"src": "", "alt": ""}},
            {"type": "container", "name": "Container", "icon": "square", "props": {"children": []}},
            {"type": "tabs", "name": "Tabs", "icon": "folder", "props": {"tabs": []}},
            {"type": "card", "name": "Card", "icon": "credit-card", "props": {"title": "", "content": ""}},
            {"type": "actions", "name": "Actions", "icon": "more-horizontal", "props": {"buttons": ["edit", "delete"]}},
        ]
