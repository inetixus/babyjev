# Building BabyJev.exe (simple version)

You only do this once, on your Windows machine.

1. Install Python from [python.org](https://www.python.org/downloads/) if you have not already. During install, tick **"Add Python to PATH"**.
2. Download this repo (green **Code** button > **Download ZIP**), unzip it, or clone it.
3. Double-click **build_exe.bat**. It installs everything and builds the exe.
4. Look inside the new **dist** folder: that is **BabyJev.exe**.

Two small rules:

- **Keep config.json next to the exe.** The exe reads its settings (and dry-run switch) from config.json in the same folder.
- **First launch is slow**, a few seconds, because a one-file exe unpacks itself. Normal.

Run it like the scripts:

    dist\BabyJev.exe --self-test      # no game needed, sanity check
    dist\BabyJev.exe --dry-run       # live capture, logs decisions, never clicks

Windows SmartScreen may grumble the first time ("unknown publisher") because the exe is unsigned: click **More info** > **Run anyway**. That is normal for any self-built exe.

Note: if you change config.json or edit triggerbot.py, just run build_exe.bat again to rebuild.
