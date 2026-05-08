<img width="128" height="128" alt="image" src="https://github.com/user-attachments/assets/9ac61b63-f594-4101-8551-2df7a3af475d" />


⚠️ This extension is in early stages of development and should be considered experimental. While I will be actively using and improving it throughout the VEX season, 
I cannot guarantee full reliability, stability, or safety. It is not recommended for use in critical contexts. If you require a stable and fully tested tool, 
you may prefer to wait until a more mature release in a future season.

**Description**

The MVPS Linker (Multifile VEX Python Support) extension enables multifile Python projects for VEX V5 Robots. It directly interacts with the 
VEX extension, allowing the user to download multifile projects to the VEX brain with a single click. The extension essentially combines multiple 
scripts into one script, resolving naming conflicts and ensuring dependencies are handled correctly along the way.

**Installation**

1. Download "mvps-linker-0.0.1.vsix" from this repo
2. Drag the .vsix file into the extensions bar in VS Code
3. Click install when prompted
4. You're done! :)

Note: You may need to navigate to the extension and accept the disclaimer from VS Code if it does not immediately appear in your sidebar.
   
**Usage**

Now that the extension is installed, ensure that the VEX extension is also running.

To create a VEX multifile Python project:
1. Create a default, empty template from the VEX extension
2. Create a folder inside the root directory named "codebase", "code", or "scripts"
3. Insert files inside that folder (files placed in other locations will not be linked)

When you are ready to download the code to the brain, click the "Combine" and then "Download" buttons in the extension's UI. It should automatically
download to the brain. Possible errors in this process from the extension's mini-linter may include:

1. Cyclic require (two or more files require one another simultaneously)
2. Naming conflicts (Brain = Brain() will cause bugs)

**Planned Features**
1. Optional circular dependency solver
