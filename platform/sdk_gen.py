"""SDK Generator — Auto-generate JavaScript/TypeScript SDK from entity schemas."""
import json

class SDKGenerator:
    @staticmethod
    def generate_js(entities: list, base_url: str = "https://evolvixos.com/platform/api") -> str:
        lines = [
            "// EvolvixOS Auto-Generated SDK",
            f"// Generated from {len(entities)} entities",
            "// DO NOT EDIT - regenerate from platform UI",
            "",
            f"const API_BASE = '{base_url}';",
            "",
            "class EvolvixSDK {",
            "  constructor(token = null) {",
            "    this.token = token;",
            "    this.headers = { 'Content-Type': 'application/json' };",
            "    if (token) this.headers['Authorization'] = 'Bearer ' + token;",
            "  }",
            "  async _fetch(path, options = {}) {",
            "    const resp = await fetch(API_BASE + path, { ...options, headers: { ...this.headers, ...(options.headers || {}) } });",
            "    if (!resp.ok) { const err = await resp.json().catch(() => ({})); throw new Error(err.detail || err.message || resp.statusText); }",
            "    return resp.json();",
            "  }",
        ]
        for entity in entities:
            name = entity.get("name", entity.get("entity_name", ""))
            if not name:
                continue
            schema = entity.get("schema", {})
            props = schema.get("properties", {})
            lines.extend([
                f"  get {name}() {{",
                "    const self = this;",
                "    return {",
                f"      async list(params={{}}) {{ return self._fetch('/api/entities/{name}/records' + (Object.keys(params).length ? '?' + new URLSearchParams(params).toString() : '')); }},",
                f"      async get(id) {{ return self._fetch('/api/entities/{name}/records/' + id); }},",
                f"      async create(data) {{ return self._fetch('/api/entities/{name}/records', {{ method:'POST', body: JSON.stringify(data) }}); }},",
                f"      async update(id, data) {{ return self._fetch('/api/entities/{name}/records/' + id, {{ method:'PUT', body: JSON.stringify(data) }}); }},",
                f"      async delete(id) {{ return self._fetch('/api/entities/{name}/records/' + id, {{ method:'DELETE' }}); }},",
                f"      async filter(filters) {{ return self._fetch('/api/entities/{name}/filter', {{ method:'POST', body: JSON.stringify(filters) }}); }},",
                f"      async aggregate(pipeline) {{ return self._fetch('/api/entities/{name}/aggregate', {{ method:'POST', body: JSON.stringify({{ pipeline }}) }}); }},",
                f"      schema: {json.dumps(schema, indent=6)},",
                "    };",
                "  },",
            ])
        lines.extend([
            "  async callFunction(name, data={}) { return this._fetch('/api/fn/' + name, { method:'POST', body: JSON.stringify(data) }); },",
            "  async uploadFile(file) {",
            "    const fd = new FormData(); fd.append('file', file);",
            "    const r = await fetch(API_BASE + '/api/files/upload', { method:'POST', headers: this.token ? {Authorization:'Bearer '+this.token} : {}, body: fd });",
            "    return r.json();",
            "  },",
            "}",
            "if (typeof module !== 'undefined') module.exports = { EvolvixSDK };",
            "if (typeof window !== 'undefined') window.EvolvixSDK = EvolvixSDK;",
        ])
        return "\n".join(lines)

    @staticmethod
    def generate_ts(entities: list, base_url: str = "https://evolvixos.com/platform/api") -> str:
        lines = [f"const API_BASE = '{base_url}';", ""]
        for entity in entities:
            name = entity.get("name", "")
            schema = entity.get("schema", {})
            props = schema.get("properties", {})
            lines.append(f"export interface {name} {{")
            lines.append("  id: string; created_date: string; updated_date: string; created_by: string;")
            for field, ftype in props.items():
                ts = {"string":"string","integer":"number","number":"number","boolean":"boolean","array":"any[]","object":"any","file":"string","image":"string"}.get(ftype.get("type","string"), "any")
                lines.append(f"  {field}?: {ts};")
            lines.append("}\n")
        lines.extend([
            "export class EvolvixSDK {",
            "  private headers: Record<string, string>;",
            "  constructor(token: string | null = null) {",
            "    this.headers = { 'Content-Type': 'application/json' };",
            "    if (token) this.headers['Authorization'] = 'Bearer ' + token;",
            "  }",
        ])
        for entity in entities:
            name = entity.get("name", "")
            lines.extend([
                f"  async list{name}s(): Promise<{name}[]> {{ return this._fetch('/api/entities/{name}/records'); }}",
                f"  async get{name}(id: string): Promise<{name}> {{ return this._fetch('/api/entities/{name}/records/' + id); }}",
                f"  async create{name}(data: Partial<{name}>): Promise<{name}> {{ return this._fetch('/api/entities/{name}/records', {{ method:'POST', body: JSON.stringify(data) }}); }}",
                f"  async update{name}(id: string, data: Partial<{name}>): Promise<{name}> {{ return this._fetch('/api/entities/{name}/records/' + id, {{ method:'PUT', body: JSON.stringify(data) }}); }}",
                f"  async delete{name}(id: string): Promise<void> {{ return this._fetch('/api/entities/{name}/records/' + id, {{ method:'DELETE' }}); }}",
            ])
        lines.extend([
            "  private async _fetch(path: string, options: RequestInit = {}): Promise<any> {",
            "    const r = await fetch(API_BASE + path, { ...options, headers: { ...this.headers, ...(options.headers as any) } });",
            "    if (!r.ok) throw new Error((await r.json()).detail || r.statusText);",
            "    return r.json();",
            "  }",
            "}",
        ])
        return "\n".join(lines)
