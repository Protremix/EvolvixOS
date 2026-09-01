const vscode = require('vscode');
const https = require('https');
const http = require('http');

function activate(context) {
  // Chat command
  context.subscriptions.push(
    vscode.commands.registerCommand('evolvixos.chat', async () => {
      const apiKey = context.globalState.get('apiKey');
      if (!apiKey) {
        vscode.window.showWarningMessage('Set your EvolvixOS API key first (EvolvixOS: Set API Key)');
        return;
      }

      const prompt = await vscode.window.showInputBox({
        prompt: 'Ask EvolvixOS anything',
        placeHolder: 'e.g. Explain async/await in Python'
      });
      if (!prompt) return;

      const config = vscode.workspace.getConfiguration('evolvixos');
      const baseUrl = config.get('baseUrl', 'https://evolvixos.com');
      const model = config.get('defaultModel', 'auto');

      const panel = vscode.window.createWebviewPanel(
        'evolvixosChat', 'EvolvixOS Chat', vscode.ViewColumn.Beside,
        { enableScripts: true }
      );

      panel.webview.html = `<html><body style="font-family:sans-serif;padding:20px">
        <h3>Querying ${model}...</h3>
        <p><i>${prompt}</i></p>
        <hr><div id="resp">Loading...</div>
      </body></html>`;

      try {
        const resp = await apiCall(baseUrl, '/platform/api/playground', {
          message: prompt, model, max_tokens: 1000
        }, apiKey);
        panel.webview.html = `<html><body style="font-family:sans-serif;padding:20px;white-space:pre-wrap">
          <h3>EvolvixOS</h3>
          <p style="color:#666"><i>${prompt}</i></p>
          <hr>
          <div>${resp.response}</div>
          <p style="color:#999;font-size:12px;margin-top:12px">via ${resp.model} (${resp.provider})</p>
        </body></html>`;
      } catch (e) {
        panel.webview.html = `<html><body><p style="color:red">Error: ${e.message}</p></body></html>`;
      }
    })
  );

  // Stream command
  context.subscriptions.push(
    vscode.commands.registerCommand('evolvixos.stream', async () => {
      const apiKey = context.globalState.get('apiKey');
      if (!apiKey) {
        vscode.window.showWarningMessage('Set your EvolvixOS API key first');
        return;
      }

      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage('Open a file first to use selected code');
        return;
      }

      const selectedText = editor.document.getText(editor.selection);
      const prompt = await vscode.window.showInputBox({
        prompt: 'Ask about the selected code',
        placeHolder: selectedText ? 'e.g. Review this code for bugs' : 'Type your question',
        value: selectedText ? 'Review this code for bugs' : ''
      });
      if (!prompt) return;

      const config = vscode.workspace.getConfiguration('evolvixos');
      const baseUrl = config.get('baseUrl', 'https://evolvixos.com');
      const message = selectedText ? `${prompt}\n\n\`${selectedText}\`` : prompt;

      const channel = vscode.window.createOutputChannel('EvolvixOS');
      channel.show();
      channel.appendLine(`Query: ${message}\n`);

      try {
        const resp = await apiCall(baseUrl, '/platform/api/playground', {
          message, model: config.get('defaultModel', 'auto'), max_tokens: 1000
        }, apiKey);
        channel.appendLine(resp.response);
        channel.appendLine(`\n--- via ${resp.model} (${resp.provider}) ---`);
      } catch (e) {
        channel.appendLine(`Error: ${e.message}`);
      }
    })
  );

  // Set API key command
  context.subscriptions.push(
    vscode.commands.registerCommand('evolvixos.setApiKey', async () => {
      const key = await vscode.window.showInputBox({
        prompt: 'Enter your EvolvixOS API key',
        password: true,
        placeHolder: 'evx_...'
      });
      if (key) {
        context.globalState.update('apiKey', key);
        vscode.window.showInformationMessage('EvolvixOS API key saved');
      }
    })
  );
}

function deactivate() {}

function apiCall(baseUrl, path, data, apiKey) {
  return new Promise((resolve, reject) => {
    const url = new URL(baseUrl + path);
    const lib = url.protocol === 'https:' ? https : http;
    const body = JSON.stringify(data);
    const req = lib.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'Content-Length': Buffer.byteLength(body)
      }
    }, (resp) => {
      let data = '';
      resp.on('data', (chunk) => data += chunk);
      resp.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error('Invalid response: ' + data.substring(0, 200))); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

module.exports = { activate, deactivate };
