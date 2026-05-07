<img width="128" height="128" alt="image" src="https://github.com/user-attachments/assets/9ac61b63-f594-4101-8551-2df7a3af475d" />


**Description**

  The MVPS Linker (Multifile VEX Python Support) extension enables multifile Python projects for VEX V5 Robots, developed by team 8373P.
It directly interacts with the VEX extension, allowing the user to download multifile projects to the VEX brain with a single click.
The extension essentially combines multiple scripts into one script, resolving naming conflicts and ensuring dependencies are handled 
correctly along the way.

**Installation**

1. Download "mvps-linker-0.0.1.vsix" from this repo
2. Run the following command in your terminal:
```bash
code --install-extension mvps-linker-0.0.1.vsix
```
3. Reopen VS Code
   
**Usage**

Now that the extension is installed, ensure that the VEX extension is also running.

To create a VEX multifile Python project:
1. Create a default, empty template from the VEX extension
2. Create a folder inside the root directory named "codebase", "code", or "scripts"
3. Insert files inside that folder

When you are ready to download the code to the brain, click the "Combine" and then "Download" buttons in the extension's UI. It should automatically
download to the brain. Possible errors in this process (on this extension's end, not VEX) may include:

1. Cyclic require (two or more files require one another simultaneously)
2. Naming conflicts (Brain = Brain() will cause bugs)
