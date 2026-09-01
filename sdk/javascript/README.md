# EvolvixOS JavaScript SDK

JavaScript/Node.js client for the EvolvixOS AI engineering platform.

## Install

```bash
npm install evolvixos
```

## Quick Start

```javascript
import { EvolvixOS } from 'evolvixos';

const client = new EvolvixOS('your-api-key', 'https://evolvixos.com');

// Chat with any of 435+ models
const resp = await client.chat('Write a haiku about code', 'auto');
console.log(resp.response);

// Stream responses
for await (const chunk of client.stream('Tell me a story')) {
  process.stdout.write(chunk);
}

// List models
const models = await client.models();
console.log(`${models.length} models available`);

// Create entities
await client.entities.create('Task', {
  title: { type: 'string' },
  status: { type: 'string', enum: ['todo', 'doing', 'done'] }
});

// Create records
await client.entities.records('Task').create({ title: 'Ship it', status: 'doing' });

// Create AI agents
await client.agents.create('reviewer', 'You are a code reviewer');
const review = await client.agents.chat('reviewer', 'Review my code');
console.log(review.response);

// Deploy backend functions
await client.functions.deploy('getWeather', 'def handler(input): return {temp: 22}');
const weather = await client.functions.call('getWeather', { city: 'Madrid' });
```

License: MIT
