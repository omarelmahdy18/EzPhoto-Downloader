# Product Image Downloader

A modern, fast, and user-friendly Windows desktop application for bulk-downloading product images from a CSV file and automatically converting them into clean, standardized `.jpg` files. Built with Python and **CustomTkinter**.

---

## ✨ Key Features

- **Modern Desktop UI:** Clean, responsive interface built with `CustomTkinter` featuring Dark, Light, and System appearance modes.
- **One-Click Sample CSV:** Generate a ready-to-fill CSV template (`name`, `url`) directly from the app.
- **Bulk CSV Processing:** Powered by `pandas` to quickly read and process hundreds or thousands of product rows.
- **Universal JPEG Conversion:** Automatically converts any source image format (`WebP`, `PNG`, `RGBA`, `CMYK`, `GIF`, etc.) into high-quality standard `JPEG` (`.jpg`) using `Pillow`, compositing transparent backgrounds cleanly onto white.
- **Windows-Safe Filename Sanitization:** Strips invalid path characters (`\ / * ? : " < > |`), trailing spaces/dots, and protects against reserved Windows device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`).
- **Smart Duplicate Protection:** Never overwrites existing files—automatically appends an incremental suffix (e.g., `product_1.jpg`, `product_2.jpg`) when duplicate product names occur.
- **Protocol-Relative URL Support:** Automatically prepends `https:` to URLs starting with `//`.
- **Non-Blocking Background Threading:** Downloads run in a dedicated background thread with a real-time progress bar and live scrolling activity log so the UI stays smooth and responsive.

---

## 🚀 How to Use (For Regular Users)

You do **not** need Python or any programming tools installed to use this application.

1. **Download the App:**
   - Go to the [**Releases**](../../releases) page of this repository.
   - Under the latest release, download **`Product Image Downloader.exe`**.
2. **Launch the App:**
   - Double-click `Product Image Downloader.exe` to open the application. *(Note: If Windows SmartScreen appears, click **More info** → **Run anyway**).*
3. **Prepare Your CSV:**
   - Click **"Download Sample CSV"** to save a template file, or prepare your own CSV containing two columns: `name` and `url`.
4. **Select Files & Download:**
   - Click **"Select CSV File"** and choose your filled `.csv` file.
   - Click **"Select Output Folder"** and choose where your downloaded images should be saved.
   - Click **"Start Download"** and watch the progress bar and activity log as your images are downloaded and converted!

---

## 🛠️ For Developers

If you want to run the project from source, modify the code, or build the standalone `.exe` yourself, follow the steps below.

### Prerequisites
- **Python 3.10+** installed on Windows.
- **Git** installed.

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/product-image-downloader.git
cd product-image-downloader
```

### 2. Create a Virtual Environment & Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Application from Source
```powershell
python main.py
```

### 4. Build the Standalone Windows `.exe` (PyInstaller)
Because `CustomTkinter` bundles internal theme `.json` files and font assets, include the `--collect-all customtkinter` flag when compiling with PyInstaller:

```powershell
pyinstaller --noconfirm --onefile --windowed --icon="app.ico" --name="Product Image Downloader" --collect-all customtkinter main.py
```
*(If you do not have an `app.ico` file, simply omit `--icon="app.ico"`).*

Once finished, your standalone executable will be located inside the **`dist/`** folder:
```text
dist/Product Image Downloader.exe
```

---

## 📄 CSV Format Example

| name | url |
| :--- | :--- |
| Classic Black T-Shirt | `https://example.com/images/black-shirt.webp` |
| Wireless Headphones | `//cdn.example.com/audio/headphones.png` |

