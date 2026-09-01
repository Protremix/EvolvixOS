/**
 * EvolvixOS JavaScript SDK
 * Self-hostable AI engineering platform — 435+ models, one API.
 *
 * @example
 * import { EvolvixOS } from 'evolvixos';
 * const client = new EvolvixOS('your-api-key', 'https://evolvixos.com');
 * const resp = await client.chat('Write a haiku about code');
 * console.log(resp.response);
 */

export class EvolvixOS {
  constructor(apiKey, baseUrl = 'https://evolvixos.com') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.entities = new Entities(this);
    this.agents = new Agents(this);
    this.functions = new Functions(this);
    this.workflows = new Workflows(this);
  }

  get headers() {
    return { Authorization: `Bearer ${this.apiKey}`, 'Content-Type': 'application/json' };
  }

  async _post(path, data) {
    const resp = await fetch(`${this.baseUrl}/platform/api${path}`, {
      method: 'POST', headers: this.headers, body: JSON.stringify(data)
    });
    if (!resp.ok) throw new Error(`API error: ${resp.status} ${await resp.text()}`);
    return resp.json();
  }

  async _get(path, params) {
    const url = new URL(`${this.baseUrl}/platform/api${path}`);
    if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    const resp = await fetch(url, { headers: this.headers });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
  }

  async chat(message, model = 'auto', system = null, temperature = 0.7, maxTokens = 1000) {
    const data = { message, model, temperature, max_tokens: maxTokens };
    if (system) data.system_prompt = system;
    return this._post('/playground', data);
  }

  async *stream(message, model = 'auto', system = null, temperature = 0.7, maxTokens = 1000) {
    const data = { message, model, temperature, max_tokens: maxTokens };
    if (system) data.system_prompt = system;
    const resp = await fetch(`${this.baseUrl}/platform/api/playground/stream`, {
      method: 'POST', headers: this.headers, body: JSON.stringify(data)
    });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const chunk = JSON.parse(line.slice(6));
          if (chunk.done) return;
          if (chunk.chunk) yield chunk.chunk;
        }
      }
    }
  }

  async models(category = null) {
    const params = category ? { category } : {};
    const data = await this._get('/models', params);
    return data.models || [];
  }

  async credits() { return this._get('/credits'); }
  async health() { return this._get('/health'); }
}

class Entities {
  constructor(client) { this.client = client; }
  async create(name, schema) { return this.client._post('/entities', { name, schema }); }
  async list() { const r = await this.client._get('/entities'); return r.entities || []; }
  records(name) { return new Records(this.client, name); }
}

class Records {
  constructor(client, entityName) { this.client = client; this.name = entityName; }
  async create(data) { return this.client._post(`/entities/${this.name}/records`, data); }
  async list(limit = 50, skip = 0) { return this.client._get(`/entities/${this.name}/records`, { limit, skip }); }
  async get(id) { return this.client._get(`/entities/${this.name}/records/${id}`); }
  async update(id, data) { return this.client._post(`/entities/${this.name}/records/${id}`, data); }
}

class Agents {
  constructor(client) { this.client = client; }
  async create(name, systemPrompt, model = 'auto') {
    return this.client._post('/agents', { name, system_prompt: systemPrompt, model });
  }
  async list() { const r = await this.client._get('/agents'); return r.agents || []; }
  async chat(name, message) { return this.client._post(`/agents/${name}/chat`, { message }); }
}

class Functions {
  constructor(client) { this.client = client; }
  async deploy(name, code) { return this.client._post('/functions', { name, code }); }
  async call(name, data = {}) { return this.client._post(`/fn/${name}`, data); }
  async list() { const r = await this.client._get('/functions'); return r.functions || []; }
}

class Workflows {
  constructor(client) { this.client = client; }
  async create(name, triggerType, definition, schedule = null) {
    const data = { name, trigger_type: triggerType, definition };
    if (schedule) data.schedule = schedule;
    return this.client._post('/workflows', data);
  }
  async list() { const r = await this.client._get('/workflows'); return r.workflows || []; }
}

export default EvolvixOS;
