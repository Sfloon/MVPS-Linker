import * as vscode from "vscode";
import * as cp from "child_process";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";

function findVexStubPath(): string {
  const home = os.homedir();
  const platform = process.platform;

  const globalStorageBase =
    platform === "win32"
      ? path.join(process.env.APPDATA || path.join(home, "AppData", "Roaming"), "Code", "User", "globalStorage")
      : platform === "darwin"
      ? path.join(home, "Library", "Application Support", "Code", "User", "globalStorage")
      : path.join(home, ".config", "Code", "User", "globalStorage");

  const sdkBase = path.join(globalStorageBase, "vexrobotics.vexcode", "sdk", "python", "V5");

  if (!fs.existsSync(sdkBase)) return "";

  const versions = fs.readdirSync(sdkBase).sort().reverse();
  if (versions.length === 0) return "";

  return path.join(sdkBase, versions[0], "vexv5", "stubs");
}

class MVPSLinkerViewProvider implements vscode.WebviewViewProvider {
  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(webviewView: vscode.WebviewView) {
    webviewView.webview.options = { enableScripts: true };

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

          button {
            border: none;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            border-radius: 4px;
            width: 100%;
            height: 36px;
            margin-bottom: 8px;
          }

          .primary-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
          }

          .primary-btn:hover { background: var(--vscode-button-hoverBackground); }

          .docs-btn {
            background: var(--vscode-editorWidget-background);
            color: var(--vscode-foreground);
            border: 1px solid var(--vscode-widget-border);
          }

          .docs-btn:hover { background: var(--vscode-editorHoverWidget-background); }


        </style>
      </head>
      <body>
        <button class="primary-btn" onclick="createTemplate()">Create Template</button>
        <button class="primary-btn" onclick="buildAndDownload()">Download</button>
        <button class="primary-btn" onclick="run()">Combine</button>
        <button class="docs-btn" onclick="openDocs()">Repository</button>

        <script>
          const vscode = acquireVsCodeApi();
          function run() { vscode.postMessage({ command: 'run' }); }
          function buildAndDownload() { vscode.postMessage({ command: 'buildAndDownload' }); }
          function createTemplate() { vscode.postMessage({ command: 'createTemplate' }); }
          function openDocs() { vscode.postMessage({ command: 'openDocs' }); }
        </script>
      </body>
      </html>
    `;

    webviewView.webview.onDidReceiveMessage((message) => {
      if (message.command === "run") {
        vscode.commands.executeCommand("mvps-linker.run");
      } else if (message.command === "buildAndDownload") {
        vscode.commands.executeCommand("mvps-linker.buildAndDownload");
      } else if (message.command === "createTemplate") {
        vscode.commands.executeCommand("mvps-linker.createTemplate");
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
      if (stdout.trim()) channel.appendLine(stdout.trim());
      if (stderr.trim()) channel.appendLine(stderr.trim());

      if (err) {
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
      if (stdout.trim()) channel.appendLine(stdout.trim());
      if (stderr.trim()) channel.appendLine(stderr.trim());

      if (err) {
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

  const templateCmd = vscode.commands.registerCommand("mvps-linker.createTemplate", async () => {
    const config = vscode.workspace.getConfiguration("mvps-linker");
    const customDir = config.get<string>("projectsDirectory")?.trim();
    const vexDir = path.join(os.homedir(), "Documents", "vex-vscode-projects");
    const docsDir = path.join(os.homedir(), "Documents");

    let parentDir: string;
    if (customDir) {
      if (fs.existsSync(customDir)) {
        parentDir = customDir;
      } else {
        const fallback = fs.existsSync(vexDir) ? vexDir
          : fs.existsSync(docsDir) ? docsDir
          : os.homedir();
        vscode.window.showWarningMessage(`MVPS: Projects directory '${customDir}' not found. Defaulting to '${fallback}'.`);
        parentDir = fallback;
      }
    } else {
      parentDir = fs.existsSync(vexDir) ? vexDir
        : fs.existsSync(docsDir) ? docsDir
        : os.homedir();
    }

    const name = await vscode.window.showInputBox({
      prompt: "Project name",
      placeHolder: "my-vex-project",
      validateInput: (v) => v.trim() ? null : "Name cannot be empty.",
    });
    if (!name) return;

    const root = path.join(parentDir, name.trim());

    if (fs.existsSync(root)) {
      vscode.window.showErrorMessage(`MVPS: Folder '${name}' already exists.`);
      return;
    }

    const stubPath = findVexStubPath();

    const vscodeDir = path.join(root, ".vscode");
    const codebaseDir = path.join(root, "codebase");
    const srcDir = path.join(root, "src");

    fs.mkdirSync(vscodeDir, { recursive: true });
    fs.mkdirSync(codebaseDir, { recursive: true });
    fs.mkdirSync(srcDir, { recursive: true });

    fs.writeFileSync(
      path.join(vscodeDir, "extensions.json"),
      JSON.stringify({ recommendations: ["ms-python.python"] }, null, "\t")
    );

    const settings: Record<string, string> = {
      "python.analysis.diagnosticMode": "workspace",
      "python.analysis.typeCheckingMode": "basic",
    };
    if (stubPath) {
      settings["python.analysis.stubPath"] = stubPath;
    }
    fs.writeFileSync(
      path.join(vscodeDir, "settings.json"),
      JSON.stringify(settings, null, "\t")
    );

    const now = new Date().toLocaleString("en-US");
    fs.writeFileSync(
      path.join(vscodeDir, "vex_project_settings.json"),
      JSON.stringify({
        extension: { version: "0.8.2026020401", json: 2 },
        project: {
          name: name.trim(),
          description: "",
          creationDate: now,
          platform: "V5",
          language: "python",
          slot: 1,
          sdkVersion: "V5_1_0_1_25",
          python: { main: "src/main.py" },
        },
      }, null, "\t")
    );

    const mainPy = path.join(codebaseDir, "main.py");
    if (!fs.existsSync(mainPy)) {
      fs.writeFileSync(mainPy, "");
    }

    vscode.commands.executeCommand("vscode.openFolder", vscode.Uri.file(root), { forceNewWindow: false });
  });

  context.subscriptions.push(runCmd, buildCmd, templateCmd);
}

export function deactivate() {}