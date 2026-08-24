"""One-click app templates for EvolvixOS platform."""
import json
from pagegen import PageGenerator

TEMPLATES = {
    "crm": {
        "id": "crm",
        "name": "CRM App",
        "icon": "📊",
        "description": "Contacts, deals, pipeline tracking",
        "color": "from-purple-600 to-pink-600",
        "entities": {
            "Contact": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "company": {"type": "string"},
                    "status": {"type": "string", "enum": ["lead", "active", "inactive"]},
                    "notes": {"type": "string"}
                },
                "required": ["name"]
            },
            "Deal": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "amount": {"type": "number"},
                    "stage": {"type": "string", "enum": ["prospecting", "qualification", "proposal", "negotiation", "won", "lost"]},
                    "contact_id": {"type": "integer", "relation": {"target": "Contact", "display": "name"}},
                    "close_date": {"type": "string"},
                    "notes": {"type": "string"}
                },
                "required": ["title"]
            },
            "Activity": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["call", "email", "meeting", "task"]},
                    "description": {"type": "string"},
                    "contact_id": {"type": "integer", "relation": {"target": "Contact", "display": "name"}},
                    "deal_id": {"type": "integer", "relation": {"target": "Deal", "display": "title"}},
                    "due_date": {"type": "string"},
                    "completed": {"type": "boolean"}
                }
            }
        }
    },
    "ecommerce": {
        "id": "ecommerce",
        "name": "E-Commerce",
        "icon": "🛍️",
        "description": "Products, orders, cart management",
        "color": "from-blue-600 to-cyan-600",
        "entities": {
            "Product": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "description": {"type": "string"},
                    "stock": {"type": "integer"},
                    "category": {"type": "string"},
                    "image_url": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "draft", "discontinued"]}
                },
                "required": ["name", "price"]
            },
            "Order": {
                "type": "object",
                "properties": {
                    "order_number": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "customer_email": {"type": "string"},
                    "total": {"type": "number"},
                    "status": {"type": "string", "enum": ["pending", "processing", "shipped", "delivered", "cancelled"]},
                    "shipping_address": {"type": "string"},
                    "notes": {"type": "string"}
                },
                "required": ["order_number"]
            },
            "OrderItem": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "relation": {"target": "Order", "display": "order_number"}},
                    "product_id": {"type": "integer", "relation": {"target": "Product", "display": "name"}},
                    "quantity": {"type": "integer"},
                    "price": {"type": "number"}
                },
                "required": ["quantity"]
            },
            "Customer": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "address": {"type": "string"},
                    "total_orders": {"type": "integer"},
                    "total_spent": {"type": "number"}
                },
                "required": ["name", "email"]
            }
        }
    },
    "tasks": {
        "id": "tasks",
        "name": "Task Manager",
        "icon": "✅",
        "description": "Tasks, projects, team collaboration",
        "color": "from-green-600 to-emerald-600",
        "entities": {
            "Project": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["planning", "active", "on_hold", "completed"]},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "color": {"type": "string"}
                },
                "required": ["name"]
            },
            "Task": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "project_id": {"type": "integer", "relation": {"target": "Project", "display": "name"}},
                    "assignee": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "review", "done"]},
                    "due_date": {"type": "string"},
                    "completed": {"type": "boolean"}
                },
                "required": ["title"]
            },
            "TeamMember": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "role": {"type": "string"},
                    "avatar_url": {"type": "string"}
                },
                "required": ["name"]
            }
        }
    },
    "blog": {
        "id": "blog",
        "name": "Blog Platform",
        "icon": "✍️",
        "description": "Posts, authors, comments",
        "color": "from-orange-600 to-amber-600",
        "entities": {
            "Author": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "bio": {"type": "string"},
                    "email": {"type": "string"},
                    "avatar_url": {"type": "string"}
                },
                "required": ["name"]
            },
            "Post": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "slug": {"type": "string"},
                    "content": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "author_id": {"type": "integer", "relation": {"target": "Author", "display": "name"}},
                    "status": {"type": "string", "enum": ["draft", "published", "archived"]},
                    "tags": {"type": "string"},
                    "featured_image": {"type": "string"},
                    "published_date": {"type": "string"}
                },
                "required": ["title"]
            },
            "Comment": {
                "type": "object",
                "properties": {
                    "post_id": {"type": "integer", "relation": {"target": "Post", "display": "title"}},
                    "author_name": {"type": "string"},
                    "author_email": {"type": "string"},
                    "content": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "approved", "spam"]},
                    "parent_id": {"type": "integer"}
                },
                "required": ["content"]
            },
            "Category": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "slug": {"type": "string"},
                    "description": {"type": "string"},
                    "parent_id": {"type": "integer"}
                },
                "required": ["name"]
            }
        }
    }
}


def get_template_list():
    """Return template metadata for frontend display."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "icon": t["icon"],
            "description": t["description"],
            "color": t["color"],
            "entity_count": len(t["entities"])
        }
        for t in TEMPLATES.values()
    ]


def get_template(template_id):
    """Get full template definition."""
    return TEMPLATES.get(template_id)


async def instantiate_template(db, template_id, app_name, user_id=None):
    """Create an app from a template: creates app, entities, and pages."""
    from entities.manager import EntityManager
    from apps import AppsManager

    template = TEMPLATES.get(template_id)
    if not template:
        raise ValueError(f"Template '{template_id}' not found")

    # 1. Create the app
    app = await AppsManager.create_app(
        db, app_name or template["name"],
        f"Created from {template['name']} template",
        user_id, []
    )
    app_id = app["id"]

    # 2. Create entities for this app
    entity_names = []
    for entity_name, schema in template["entities"].items():
        try:
            await EntityManager.create_entity(db, entity_name, schema, user_id, app_id)
            entity_names.append(entity_name)
        except ValueError as e:
            # Entity might already exist — skip
            pass

    # 3. Generate pages using PageGenerator
    pg = PageGenerator()
    entity_list = [{"name": n, "schema": s} for n, s in template["entities"].items()]
    pages = [pg.generate_dashboard_page(entity_list)]
    for e in entity_list:
        pages.extend(pg.generate_pages_for_entity(e["name"], e))

    # 4. Save pages to the app
    for page in pages:
        await AppsManager.create_page(
            db, app_id,
            page.get("name", "Untitled"),
            page.get("layout", []),
            page.get("type", "custom"),
            page.get("is_home", False),
            user_id
        )

    # 5. Auto-publish
    await AppsManager.publish_app(db, app_id)

    return {
        "app": app,
        "entities_created": entity_names,
        "pages_created": len(pages),
        "template": template["name"],
        "url": f"/app/{app.get('slug', app_id)}"
    }
