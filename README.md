<img width="128" height="128" alt="image" src="https://github.com/user-attachments/assets/9ac61b63-f594-4101-8551-2df7a3af475d" />

**Disclaimer**
---

⚠️ This extension is in early stages of development and should be considered an experimental demo. While I will be actively using and improving it throughout the VEX season, I cannot guarantee full reliability, stability, or safety. It is not recommended for use in critical contexts. If you require a stable and fully tested tool, you may prefer to wait until a more mature release in a future season.

**Description**
---

The MVPS Linker (Multifile VEX Python Support) extension enables multifile Python projects for VEX V5 Robots. It directly interacts with the VEX extension, allowing the user to download multifile projects to the VEX brain with a single click. The extension essentially combines multiple scripts into a single script, resolving naming conflicts and ensuring dependencies are handled correctly.

**Installation**
---

- Ensure VS Code, the VEX Extension, and Python 3.9 or newer are installed
- Download the raw code of the "mvps-linker-0.0.3.vsix" file from this repo
- Drag the file into the extensions bar in VS Code
- Click install if prompted

*Note: You may need to navigate to the extension and accept the disclaimer from VS Code if it does not immediately appear in your sidebar.*
   
**Usage**
---

Now that the extension is installed, ensure that the VEX extension is also running.

To create a VEX multifile Python project:
- Create a default, empty Python template from the VEX extension
- Create a folder inside the root directory named "codebase", "code", or "scripts"
- Insert files that you would like to be linked inside that folder

When you are ready to download the code to the brain, click the "Download" button in the extension's UI. It should automatically download to the brain. Currently, the "Combine" button is primarily for debugging and does not cache the product.

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
---

The current way to debug is to upload to the brain, find the line where the error occurred in the linked file, locate that line's file of origin, and then use the error's type to try to solve it. I plan to add a fully functional (optional) linter in the future to avoid this detour. Here are the two scenarios the extension catches pre-link so far (although this will be fully rewritten soon):

- Cyclic require (two or more files importing one another simultaneously)
- Naming conflicts (Brain = Brain() will cause bugs)

Unrecognized errors the extension encounters while linking will be printed as is. You can guarantee an error is from this particular extension if it is prefaced with "MVPS Error: ..." Otherwise, it's likely safe to assume another party caused the error.

**Planned Features**
---
- Optional automatic circular dependency solver (low priority)
- Caching unchanged scripts (low priority)
- Built-in multifile project template (medium priority)
- Optional Linter (high priority) 
