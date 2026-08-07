const vscode = require('vscode');
const { execSync } = require('child_process');

function activate(context) {
    // Deploy Contract
    context.subscriptions.push(vscode.commands.registerCommand('verdis.deploy', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('Open a Solidity file first');
            return;
        }
        const contractPath = editor.document.uri.fsPath;
        const contractName = require('path').basename(contractPath, '.sol');

        const privateKey = await vscode.window.showInputBox({
            prompt: 'Enter your Verdis private key',
            password: true,
            placeHolder: '0x...'
        });
        if (!privateKey) return;

        const rpcUrl = vscode.workspace.getConfiguration('verdis').get('rpcUrl');
        const chainId = vscode.workspace.getConfiguration('verdis').get('chainId');

        try {
            const output = execSync(
                `forge create ${contractPath}:${contractName} --rpc-url ${rpcUrl} --private-key ${privateKey} --chain-id ${chainId}`,
                { encoding: 'utf8', cwd: vscode.workspace.rootPath }
            );
            vscode.window.showInformationMessage(`Deployed: ${output.split('\n').find(l => l.includes('Deployed to')) || 'Check output'}`);
            const outputChannel = vscode.window.createOutputChannel('Verdis Deploy');
            outputChannel.append(output);
            outputChannel.show();
        } catch (err) {
            vscode.window.showErrorMessage(`Deploy failed: ${err.message}`);
        }
    }));

    // Compile Contract
    context.subscriptions.push(vscode.commands.registerCommand('verdis.compile', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        try {
            const output = execSync(`npx solc ${editor.document.uri.fsPath}`, { encoding: 'utf8' });
            const outputChannel = vscode.window.createOutputChannel('Verdis Compile');
            outputChannel.append(output);
            outputChannel.show();
        } catch (err) {
            vscode.window.showErrorMessage(`Compile failed: ${err.message}`);
        }
    }));

    // Check Chain Health
    context.subscriptions.push(vscode.commands.registerCommand('verdis.checkHealth', async () => {
        const rpcUrl = vscode.workspace.getConfiguration('verdis').get('rpcUrl');
        try {
            const output = execSync(
                `curl -s -X POST ${rpcUrl} -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"system_health","id":1}'`,
                { encoding: 'utf8' }
            );
            const health = JSON.parse(output);
            vscode.window.showInformationMessage(
                `Verdis: ${health.result?.peers || 0} peers, block #${health.result?.bestNumber || '?'}`
            );
        } catch (err) {
            vscode.window.showErrorMessage(`Cannot reach Verdis: ${err.message}`);
        }
    }));

    // Get Balance
    context.subscriptions.push(vscode.commands.registerCommand('verdis.getBalance', async () => {
        const address = await vscode.window.showInputBox({ prompt: 'Enter Verdis address', placeHolder: '0x...' });
        if (!address) return;
        const rpcUrl = vscode.workspace.getConfiguration('verdis').get('rpcUrl');
        try {
            const output = execSync(
                `curl -s -X POST ${rpcUrl} -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"system_accountNextIndex","params":["${address}"],"id":1}'`,
                { encoding: 'utf8' }
            );
            vscode.window.showInformationMessage(`Account exists on Verdis (nonce: ${JSON.parse(output).result})`);
        } catch (err) {
            vscode.window.showErrorMessage(`Error: ${err.message}`);
        }
    }));

    // Open in Verdiscan
    context.subscriptions.push(vscode.commands.registerCommand('verdis.openExplorer', async () => {
        const explorerUrl = vscode.workspace.getConfiguration('verdis').get('explorerUrl');
        const address = await vscode.window.showInputBox({ prompt: 'Enter address or tx hash' });
        if (address) {
            vscode.env.openExternal(vscode.Uri.parse(`${explorerUrl}/address/${address}`));
        }
    }));

    // Run AegisOS Audit
    context.subscriptions.push(vscode.commands.registerCommand('verdis.runAudit', async () => {
        const aegisUrl = vscode.workspace.getConfiguration('verdis').get('aegisOSUrl');
        vscode.window.showInformationMessage(`Triggering AegisOS audit at ${aegisUrl}...`);
        try {
            execSync(`curl -s -X POST ${aegisUrl}/api/v1/pipelines -H "Content-Type: application/json" -d '{"name":"VSCode Audit","template":"security_patch"}'`,
                { encoding: 'utf8' });
            vscode.window.showInformationMessage('Audit triggered! Check AegisOS dashboard for results.');
        } catch (err) {
            vscode.window.showWarningMessage(`AegisOS not reachable at ${aegisUrl}. Is it running?`);
        }
    }));
}

function deactivate() {}

module.exports = { activate, deactivate };
