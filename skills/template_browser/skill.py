#!/usr/bin/env python3
"""Template Browser — Browse and search 11,000+ website templates. 100% Free."""
import json, sys, os, glob

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")


class Skill:
    """Browse, search, and render 11,000+ website templates."""
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "list")
        if action == "list":
            return self._list(args)
        elif action == "search":
            return self._search(args)
        elif action == "get":
            return self._get(args)
        elif action == "count":
            return self._count()
        elif action == "categories":
            return self._categories()
        elif action == "render":
            return self._render(args)
        elif action == "preview":
            return self._preview(args)
        return {"error": f"unknown action: {action}"}

    def _list(self, args):
        category = args.get("category", "")
        page = args.get("page", 1)
        per_page = args.get("per_page", 20)
        if category:
            pattern = os.path.join(TEMPLATES_DIR, category, "tpl_*", "template.json")
        else:
            pattern = os.path.join(TEMPLATES_DIR, "*", "tpl_*", "template.json")
        files = sorted(glob.glob(pattern))
        total = len(files)
        start = (page - 1) * per_page
        end = start + per_page
        results = []
        for f in files[start:end]:
            with open(f) as fh:
                meta = json.load(fh)
            results.append({
                "name": meta["name"],
                "category": meta["category"],
                "tags": meta.get("tags", []),
                "path": os.path.relpath(os.path.dirname(f), TEMPLATES_DIR),
            })
        return {"templates": results, "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}

    def _search(self, args):
        query = args.get("q", "").lower()
        category = args.get("category", "")
        max_results = args.get("max", 50)
        pattern = os.path.join(TEMPLATES_DIR, category or "*", "tpl_*", "template.json")
        results = []
        for f in sorted(glob.glob(pattern)):
            with open(f) as fh:
                meta = json.load(fh)
            searchable = (meta["name"] + " " + " ".join(meta.get("tags", [])) + " " + meta["category"]).lower()
            if query in searchable:
                results.append({
                    "name": meta["name"],
                    "category": meta["category"],
                    "tags": meta.get("tags", []),
                    "path": os.path.relpath(os.path.dirname(f), TEMPLATES_DIR),
                })
                if len(results) >= max_results:
                    break
        return {"results": results, "count": len(results), "query": query}

    def _get(self, args):
        path = args.get("path", "")
        template_path = os.path.join(TEMPLATES_DIR, path, "index.html")
        if not os.path.exists(template_path):
            return {"error": "template not found"}
        with open(template_path) as f:
            html = f.read()
        meta_path = os.path.join(TEMPLATES_DIR, path, "template.json")
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
        return {"html": html, "meta": meta, "path": path}

    def _count(self):
        counts = {}
        total = 0
        for category in os.listdir(TEMPLATES_DIR):
            cat_dir = os.path.join(TEMPLATES_DIR, category)
            if os.path.isdir(cat_dir):
                count = len(glob.glob(os.path.join(cat_dir, "tpl_*", "index.html")))
                counts[category] = count
                total += count
        return {"categories": counts, "total": total}

    def _categories(self):
        cats = []
        for category in sorted(os.listdir(TEMPLATES_DIR)):
            cat_dir = os.path.join(TEMPLATES_DIR, category)
            if os.path.isdir(cat_dir):
                count = len(glob.glob(os.path.join(cat_dir, "tpl_*", "index.html")))
                cats.append({"name": category, "count": count})
        return {"categories": cats, "total_categories": len(cats)}

    def _render(self, args):
        path = args.get("path", "")
        data = args.get("data", {})
        template_path = os.path.join(TEMPLATES_DIR, path, "index.html")
        if not os.path.exists(template_path):
            return {"error": "template not found"}
        with open(template_path) as f:
            html = f.read()
        for key, value in data.items():
            html = html.replace(f"{{{{{key}}}}}", str(value))
            html = html.replace(f"{{{key}}}", str(value))
        return {"html": html, "path": path, "replacements": len(data)}

    def _preview(self, args):
        path = args.get("path", "")
        result = self._get({"path": path})
        if "error" in result:
            return result
        html = result["html"]
        preview = html.replace("<body>", "<body>\n<!-- EvolvixOS Template Preview -->")
        return {"preview": preview, "meta": result.get("meta", {})}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
