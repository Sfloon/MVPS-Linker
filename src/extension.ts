import * as vscode from "vscode";
import * as cp from "child_process";
import * as path from "path";

class MVPSLinkerViewProvider implements vscode.WebviewViewProvider {
  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(webviewView: vscode.WebviewView) {
    console.log("MVPS Linker webview resolving");

    webviewView.webview.options = {
      enableScripts: true,
    };

    webviewView.webview.html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">

        <style>
          body {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: flex-start;
            margin: 0;
            padding: 12px;
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background: var(--vscode-sideBar-background);
          }

          h2 {
            font-size: 16px;
            margin: 0 0 12px 0;
          }

          button {
            border: none;
            padding: 8px 16px;
            font-size: 13px;
            cursor: pointer;
            border-radius: 0px;
            width: 100%;
            height: 36px;
            margin-bottom: 8px;
          }

          .primary-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
          }

          .primary-btn:hover {
            background: var(--vscode-button-hoverBackground);
          }

          .docs-btn {
            background: var(--vscode-editorWidget-background);
            color: var(--vscode-foreground);
            border: 1px solid var(--vscode-widget-border);
          }

          .docs-btn:hover {
            background: var(--vscode-editorHoverWidget-background);
          }
        </style>
      </head>

      <body>
        <h2>MVPS Linker</h2>

        <button class="primary-btn" onclick="run()">Combine</button>
        <button class="primary-btn" onclick="buildAndDownload()">Download</button>
        <button class="docs-btn" onclick="openDocs()">Repository</button>

        <script>
          const vscode = acquireVsCodeApi();

          function run() {
            vscode.postMessage({ command: 'run' });
          }

          function buildAndDownload() {
            vscode.postMessage({ command: 'buildAndDownload' });
          }

          function openDocs() {
            vscode.postMessage({ command: 'openDocs' });
          }
        </script>
      </body>
      </html>
    `;

    webviewView.webview.onDidReceiveMessage((message) => {
      if (message.command === "run") {
        vscode.commands.executeCommand("mvps-linker.run");
      } else if (message.command === "buildAndDownload") {
        vscode.commands.executeCommand("mvps-linker.buildAndDownload");
      } else if (message.command === "openDocs") {
        vscode.env.openExternal(vscode.Uri.parse("https://github.com/tatedel/MVPS-Linker"));
      }
    });
  }
}

export function activate(context: vscode.ExtensionContext) {
  const provider = new MVPSLinkerViewProvider(context.extensionUri);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("mvps-linker.view", provider)
  );

  const runCmd = vscode.commands.registerCommand("mvps-linker.run", async () => {
    const workspaceFolders = vscode.workspace.workspaceFolders;

    if (!workspaceFolders) {
      vscode.window.showErrorMessage("MVPS Linker: Open a workspace folder first.");
      return;
    }

    const workspaceRoot = workspaceFolders[0].uri.fsPath;
    const scriptPath = path.join(context.extensionPath, "scripts", "linker.py");

    const config = vscode.workspace.getConfiguration("mvps-linker");
    const pythonPath: string = config.get("pythonPath") || "python3";

    const channel = vscode.window.createOutputChannel("MVPS Linker");
    channel.show();
    channel.appendLine(`MVPS: Running in: ${workspaceRoot}`);

    cp.execFile(pythonPath, [scriptPath], { cwd: workspaceRoot }, (err, stdout, stderr) => {
      if (stdout) {channel.appendLine(stdout);};
      if (stderr) {channel.appendLine(stderr);};

      if (err) {
        channel.appendLine(`MVPS Error: ${err.message}`);
        vscode.window.showErrorMessage("MVPS Linker failed. See Output > MVPS Linker.");
      } else {
        channel.appendLine("MVPS: Combined program written.");
        vscode.window.showInformationMessage("MVPS: Combined program written.");
      }
    });
  });

  const buildCmd = vscode.commands.registerCommand("mvps-linker.buildAndDownload", async () => {
    const workspaceFolders = vscode.workspace.workspaceFolders;

    if (!workspaceFolders) {
      vscode.window.showErrorMessage("MVPS: Open a workspace folder first.");
      return;
    }

    const workspaceRoot = workspaceFolders[0].uri.fsPath;
    const scriptPath = path.join(context.extensionPath, "scripts", "linker.py");

    const config = vscode.workspace.getConfiguration("mvps-linker");
    const pythonPath: string = config.get("pythonPath") || "python3";

    const channel = vscode.window.createOutputChannel("MVPS Linker");
    channel.show();
    channel.appendLine("MVPS: Running linker...");

    cp.execFile(pythonPath, [scriptPath], { cwd: workspaceRoot }, (err, stdout, stderr) => {
      if (stdout) {channel.appendLine(stdout);};
      if (stderr) {channel.appendLine(stderr);};

      if (err) {
        channel.appendLine(`MVPS Error: ${err.message}`);
        vscode.window.showErrorMessage("MVPS Linker failed. See Output > MVPS Linker.");
      } else {
        channel.appendLine("MVPS: combined.py written. Downloading...");

        vscode.commands.executeCommand("vexrobotics.vexcode.system.download").then(() => {
          channel.appendLine("MVPS: Done.");
          vscode.window.showInformationMessage("MVPS: Downloaded.");
        });
      }
    });
  });

  context.subscriptions.push(runCmd);
  context.subscriptions.push(buildCmd);
}

export function deactivate() {}