
![Gemini_Generated_Image_k01nzvk01nzvk01n](https://github.com/user-attachments/assets/aab4d4f6-f896-4087-af49-d3d0447e6dbc)



# Laser GRBL Controller for macOS



This project provides a desktop application for macOS to control GRBL-compatible CNC machines and laser engravers. Built with Python and PyQt6, it offers a user-friendly interface for serial communication, G-code sending, jogging, and even converting images to G-code for engraving.

# Features


Serial Port Connection: Easily connect and disconnect from available serial ports.

GRBL Status Monitoring: Displays real-time GRBL status (Idle, Run, Hold, etc.) and current Work Position (WPos).

Jogging Controls: Intuitive buttons for moving the X, Y, and Z axes with configurable step sizes.

Set Origin: Quickly set the current machine position as the work coordinate origin (0,0,0).

Laser & Feed Rate Control: Sliders to adjust laser power (S) and feed rate (F) on the fly.

Image to G-code Conversion: Convert grayscale images (PNG, JPG, BMP, GIF) into G-code paths suitable for laser engraving, with customizable resolution and laser intensity threshold.

G-code Console: Send custom G-code commands and view GRBL's responses in a dedicated console.

G-code Path Preview: Visualizes the generated or loaded G-code paths, including laser travel (G00) and engraving (G01) moves, along with an optional image overlay.

Dark Theme: A modern, eye-pleasing dark user interface.

Optimized Layout: Responsive design with a scrollable control panel for efficient use on various screen sizes.


# Screenshots


<img width="1705" alt="Στιγμιότυπο οθόνης 2025-07-09, 21 54 46" src="https://github.com/user-attachments/assets/8661bce1-297d-43bf-89f9-9ca75576b2e6" />


# How to Run the Application


To run this application, you need to have Python installed on your macOS system. It's recommended to use a virtual environment to manage project dependencies.

Step 1: Install Python (if you don't have it)
macOS comes with Python pre-installed, but it might be an older version (e.g., Python 2.x). For this application, Python 3.x is required.

You can install Python 3 using Homebrew, a popular package manager for macOS.

Install Homebrew (if you don't have it):
Open your Terminal (Applications/Utilities/Terminal.app) and paste the following command. Press Enter and follow the on-screen instructions.



/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
You might be asked to enter your password. This command will also install Xcode Command Line Tools if they are not already present.

Install Python 3 using Homebrew:
Once Homebrew is installed, run this command in your Terminal:



brew install python
This will install the latest stable version of Python 3. You can verify the installation by running:



python3 --version
It should show a version like Python 3.x.x.

Step 2: Clone the Repository
Navigate to the directory where you want to save the project in your Terminal, then clone the repository:



git clone https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller
cd LaserGRBL-MacOS-Controller


Step 3: Create a Virtual Environment (Recommended)
It's best practice to create a virtual environment to isolate the project's dependencies from your system's global Python packages. This prevents conflicts and keeps your project clean.



python3 -m venv venv
This command creates a new directory named venv inside your project folder, which will contain the virtual environment.

Step 4: Activate the Virtual Environment
Before installing dependencies or running the application, you need to activate the virtual environment:



source venv/bin/activate
You will notice (venv) appear at the beginning of your Terminal prompt, indicating that the virtual environment is active.

Step 5: Install Dependencies
With the virtual environment activated, install the required Python packages:



pip install PyQt6 PyQt6-Qt PySerial Pillow
This command will download and install PyQt6, PySerial, and Pillow (PIL) into your virtual environment.

Step 6: Run the Application
Finally, execute the main Python script to launch the application:



python LaserGRBLMacOS.py


When you are done working with the application, you can deactivate the virtual environment by simply typing:



deactivate
# Contributing
We welcome contributions! If you have suggestions, bug reports, or want to contribute code, please feel free to:

Open an issue on GitHub.

Fork the repository and submit a pull request.

# License
This project is licensed under the MIT License - see the LICENSE file for details.


# Please Note

You need to already have your Arduino Uno board or any board you using updated with the GRBL firmware.More info https://howtomechatronics.com/tutorials/how-to-setup-grbl-control-cnc-machine-with-arduino/ (The instructions are not mine).
The project is open source,you can try your own stuff and make every changes you want.


# Inspiration

https://www.youtube.com/watch?v=td4DWtMY7SQ
Looking this video i was looking to make the same simple CNC Machine using an Arduino Uno Board and an CNC Shield board.I am currently using both Windows and Macbook,the video shows that you can use the open source software LaserGRBL https://github.com/arkypita/LaserGRBL that is only for Windows.I was looking to make a open source software like this also for MacOS user(like me) so you don't have to switch operating system for this project.More updates soon.
