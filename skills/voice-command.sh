#!/bin/bash
# Process voice commands like a smart assistant
# Usage: ./voice-command.sh "transcribed voice command"

COMMAND="$1"
echo "🎙️ Voice Command: $COMMAND"
echo ""

# Route the command to the right action
python3 -c "
import json
import subprocess
import os

command = '''$COMMAND'''.lower()

# Simple intent detection
if any(w in command for w in ['check', 'status', 'health', 'monitor']):
    print('Running system health check...')
    result = subprocess.run(['curl', '-s', '--max-time', '5', 'http://127.0.0.1:5010/api/health'], 
                          capture_output=True, text=True)
    data = json.loads(result.stdout)
    print(f'Status: {data[\"status\"]}')
    print(f'Ollama: {data[\"ollama\"]}')
    print(f'ComfyUI: {data[\"comfyui\"]}')
    print(f'Art Engine: {data[\"art_engine\"]}')
    print(f'Mr James: v{data[\"james_version\"]} with {data[\"tools_available\"]} tools')

elif any(w in command for w in ['restart', 'reload', 'restart service']):
    if 'nginx' in command:
        result = subprocess.run(['systemctl', 'restart', 'nginx'], capture_output=True, text=True)
        print('Nginx restarted!' if result.returncode == 0 else f'Error: {result.stderr}')
    elif 'docker' in command:
        result = subprocess.run(['systemctl', 'restart', 'docker'], capture_output=True, text=True)
        print('Docker restarted!' if result.returncode == 0 else f'Error: {result.stderr}')
    else:
        print('Which service should I restart?')

elif any(w in command for w in ['create', 'generate', 'make', 'build']):
    if 'image' in command or 'logo' in command:
        print('Generating image...')
        result = subprocess.run(['curl', '-s', '--max-time', '5', 'http://127.0.0.1:5010/api/generate/image',
                                '-X', 'POST', '-H', 'Content-Type: application/json',
                                '-d', json.dumps({'prompt': command, 'steps': 15})],
                               capture_output=True, text=True)
        data = json.loads(result.stdout)
        print(f'Image generation started! Job ID: {data.get(\"job_id\", \"unknown\")}')
    elif 'video' in command:
        print('Starting video generation...')
        result = subprocess.run(['/opt/evolvixos/skills/create-media.sh', command],
                               capture_output=True, text=True, timeout=120)
        print(result.stdout)
    else:
        print(f'I can help create that. Processing: {command}')

elif any(w in command for w in ['search', 'find', 'lookup', 'what is']):
    print(f'Searching for: {command}')
    # Use web search tool
    import urllib.request
    url = f'https://api.duckduckgo.com/?q={urllib.parse.quote(command)}&format=json&no_html=1'
    req = urllib.request.Request(url, headers={'User-Agent': 'MrJames/6.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    if data.get('AbstractText'):
        print(data['AbstractText'])
    else:
        for topic in data.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and topic.get('Text'):
                print(f'- {topic[\"Text\"]}')

elif any(w in command for w in ['docker', 'container', 'compose']):
    result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\\t{{.Status}}'],
                          capture_output=True, text=True)
    print('Running containers:')
    print(result.stdout or 'No containers running')

elif any(w in command for w in ['crypto', 'bitcoin', 'eth', 'token', 'price']):
    result = subprocess.run(['/opt/evolvixos/skills/crypto-blockchain.sh', command],
                           capture_output=True, text=True, timeout=30)
    print(result.stdout)

elif any(w in command for w in ['hello', 'hi', 'hey', 'morning', 'evening']):
    print('Hey! I am Mr James, your EvolvixOS agent. What can I do for you?')

elif any(w in command for w in ['help', 'what can you do']):
    print('''I can help you with:
- System management: check status, restart services, manage Docker
- Media creation: generate images, videos, voiceovers
- Crypto analysis: check prices, DeFi protocols, market data
- Web search: look up anything
- Code: write and run Python, bash, HTML/CSS
- Design: create logos, brand assets, social media graphics

Just tell me what you need!''')

else:
    print(f'I heard: \"{command}\"')
    print('Processing your request...')
    # Forward to agent
    result = subprocess.run(['curl', '-s', '--max-time', '30', 'http://127.0.0.1:5010/api/agent',
                           '-X', 'POST', '-H', 'Content-Type: application/json',
                           '-d', json.dumps({'prompt': command, 'type': 'auto'})],
                          capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        print(data.get('response', 'No response')[:500])
    except:
        print('Could not process that request')
" 2>&1
