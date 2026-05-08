<img width="128" height="128" alt="image" src="https://github.com/user-attachments/assets/9ac61b63-f594-4101-8551-2df7a3af475d" />


⚠️ This extension is in early stages of development and should be considered an experimental tech demo. While I will be actively using and improving it throughout the VEX season, I cannot guarantee full reliability, stability, or safety. It is not recommended for use in critical contexts. If you require a stable and fully tested tool, 
you may prefer to wait until a more mature release in a future season.

**Description**

The MVPS Linker (Multifile VEX Python Support) extension enables multifile Python projects for VEX V5 Robots. It directly interacts with the 
VEX extension, allowing the user to download multifile projects to the VEX brain with a single click. The extension essentially combines multiple 
scripts into one script, resolving naming conflicts and ensuring dependencies are handled correctly along the way.

**Installation**

1. Ensure VS Code and the VEX Extension is installed
1. Download "mvps-linker-0.0.1.vsix" from this repo
2. Drag the .vsix file into the extensions bar in VS Code
3. Click install when prompted

Note: You may need to navigate to the extension and accept the disclaimer from VS Code if it does not immediately appear in your sidebar.
   
**Usage**

Now that the extension is installed, ensure that the VEX extension is also running.

To create a VEX multifile Python project:
1. Create a default, empty template from the VEX extension
2. Create a folder inside the root directory named "codebase", "code", or "scripts"
3. Insert files inside that folder (files placed in other locations will not be linked)

When you are ready to download the code to the brain, click the "Download" button in the extension's UI. It should automatically
download to the brain. The "Combine" button is more for debugging than anything else.

<table>
<tr>
<td align="center">
<img width="164" alt="Screenshot 2026-05-07 at 9 38 02 PM" src="https://github.com/user-attachments/assets/c273f4bb-38e2-4664-a9c2-b4fcb1e29a9e" />
<br>
<em>Example file structure</em>
</td>
<td align="center">
<img width="164" alt="Screenshot 2026-05-07 at 9 38 26 PM" src="https://github.com/user-attachments/assets/0e72d946-a917-4317-b146-e0ab69629ee9" />
<br>
<em>UI of the extension</em>
</td>
</tr>
</table>

**Errors**

Possible errors in this process from the extension's mini-linter may include:

1. Cyclic require (two or more files require one another simultaneously)
2. Naming conflicts (Brain = Brain() will cause bugs)

Since these errors are common, they are especially accounted for in the code. Unrecognized errors the extension encounters will simply be printed as is. 
You can guarantee an error is from this particular extension because it will always be prefaced with "MVPS Error: ..." Otherwise, it's likely safe to assume 
the error was caused by some other party.

**How it Works**

The [main script](https://github.com/tatedel/MVPS-Linker/blob/main/scripts/linker.py) is a lightweight Python program that runs in accordance with the following flow chart:
Start → Find source directory → Scan Python files → Collect symbols/warnings → Build dependency graph → Topological sort → Circular dependency check → Flatten + rename modules → Combine transformed code → Write combined.py → Complete


**Planned Features**
1. Optional automatic circular dependency solver (low priority)
2. Caching unchanged scripts (high priority)
4. Built-in multifile project template (medium priority
5. Better error checking (medium priority)
