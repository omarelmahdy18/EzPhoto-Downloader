import csv
import io
import os
import re
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd
import requests
from PIL import Image

# Set dark theme and modern styling
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Reserved Windows file names
RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, max_length: int = 120) -> str:
    """Sanitize string to produce a safe Windows filename."""
    # Remove illegal characters: \ / : * ? " < > |
    clean = re.sub(r'[\\/*?:"<>|]', "_", name)
    # Remove ASCII control characters
    clean = re.sub(r"[\x00-\x1f\x7f]", "", clean)
    # Collapse multiple whitespace characters and strip trailing spaces and dots
    clean = re.sub(r"\s+", " ", clean).strip().rstrip(". ")
    
    if len(clean) > max_length:
        clean = clean[:max_length].rstrip(". ")
        
    # Check against reserved Windows names
    base_name = clean.split(".")[0].upper()
    if base_name in RESERVED_WINDOWS_NAMES:
        clean = f"_{clean}"
        
    return clean


class EzPhotoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("EzPhoto Downloader")
        self.geometry("740x660")
        self.minsize(620, 560)

        # Application state
        self.csv_path: str | None = None
        self.output_folder: str | None = None
        self.is_downloading: bool = False

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_controls_card()
        self._build_progress_card()
        self._build_log_card()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="EzPhoto Downloader",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Batch download product photos from CSV & convert to optimized JPEG",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="gray65",
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _build_controls_card(self):
        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # 1. Download Sample CSV
        self.btn_sample = ctk.CTkButton(
            card,
            text="Download Sample CSV",
            command=self.download_sample,
            width=200,
            height=36,
            fg_color="gray25",
            hover_color="gray35",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_sample.grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky="w")

        lbl_sample_hint = ctk.CTkLabel(
            card,
            text="Generate a template CSV with 'name' and 'url' columns",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            anchor="w",
        )
        lbl_sample_hint.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky="ew")

        # 2. Select CSV File
        self.btn_select_csv = ctk.CTkButton(
            card,
            text="Select CSV File",
            command=self.select_csv,
            width=200,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_select_csv.grid(row=1, column=0, padx=(16, 12), pady=8, sticky="w")

        self.lbl_csv = ctk.CTkLabel(
            card,
            text="No CSV file selected",
            font=ctk.CTkFont(size=12),
            text_color="#ff6b6b",
            anchor="w",
        )
        self.lbl_csv.grid(row=1, column=1, padx=(0, 16), pady=8, sticky="ew")

        # 3. Select Output Folder
        self.btn_select_folder = ctk.CTkButton(
            card,
            text="Select Output Folder",
            command=self.select_folder,
            width=200,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_select_folder.grid(row=2, column=0, padx=(16, 12), pady=8, sticky="w")

        self.lbl_folder = ctk.CTkLabel(
            card,
            text="No output folder selected",
            font=ctk.CTkFont(size=12),
            text_color="#ff6b6b",
            anchor="w",
        )
        self.lbl_folder.grid(row=2, column=1, padx=(0, 16), pady=8, sticky="ew")

        # 4. Start Download
        self.btn_start = ctk.CTkButton(
            card,
            text="Start Download",
            command=self.start_download,
            height=42,
            fg_color="#2ea043",
            hover_color="#238636",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.btn_start.grid(row=3, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="ew")

    def _build_progress_card(self):
        prog_frame = ctk.CTkFrame(self, corner_radius=12)
        prog_frame.grid(row=2, column=0, padx=20, pady=8, sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        status_row = ctk.CTkFrame(prog_frame, fg_color="transparent")
        status_row.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")
        status_row.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            status_row,
            text="Status: Idle",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self.lbl_status.grid(row=0, column=0, sticky="w")

        self.lbl_progress_pct = ctk.CTkLabel(
            status_row,
            text="0% (0 / 0)",
            font=ctk.CTkFont(size=12),
            text_color="gray65",
            anchor="e",
        )
        self.lbl_progress_pct.grid(row=0, column=1, sticky="e")

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=14, corner_radius=7)
        self.progress_bar.grid(row=1, column=0, padx=16, pady=(4, 14), sticky="ew")
        self.progress_bar.set(0)

    def _build_log_card(self):
        log_frame = ctk.CTkFrame(self, corner_radius=12)
        log_frame.grid(row=3, column=0, padx=20, pady=(8, 20), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        lbl_log_title = ctk.CTkLabel(
            log_frame,
            text="Activity Log",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        lbl_log_title.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.log_area = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
            state="disabled",
            wrap="word",
        )
        self.log_area.grid(row=1, column=0, padx=16, pady=(4, 16), sticky="nsew")

    # ---------------- Thread-Safe UI Helpers ---------------- #

    def log_message(self, message: str):
        """Append messages to the scrollable log area."""
        def _append():
            self.log_area.configure(state="normal")
            self.log_area.insert("end", message + "\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

        self.after(0, _append)

    def update_progress(self, current: int, total: int, status_text: str | None = None):
        """Update progress bar, percentage label, and status text."""
        def _update():
            ratio = (current / total) if total > 0 else 0.0
            self.progress_bar.set(ratio)
            pct = int(ratio * 100)
            self.lbl_progress_pct.configure(text=f"{pct}% ({current} / {total})")
            if status_text:
                self.lbl_status.configure(text=status_text)

        self.after(0, _update)

    def set_controls_state(self, enabled: bool):
        """Toggle buttons during download process."""
        def _toggle():
            state = "normal" if enabled else "disabled"
            self.btn_sample.configure(state=state)
            self.btn_select_csv.configure(state=state)
            self.btn_select_folder.configure(state=state)
            self.btn_start.configure(
                state=state,
                text="Start Download" if enabled else "Downloading...",
            )

        self.after(0, _toggle)

    # ---------------- Button Handlers ---------------- #

    def download_sample(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="sample_products.csv",
            title="Save Sample CSV",
            filetypes=[("CSV Files", "*.csv")],
        )
        if file_path:
            try:
                with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["name", "url"])
                    writer.writerow(["Sample Product 1", "https://picsum.photos/id/21/800/800"])
                    writer.writerow(["Sample Product 2", "https://picsum.photos/id/36/800/800"])
                messagebox.showinfo("Success", "Sample CSV saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save sample CSV:\n{e}")

    def select_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if path:
            self.csv_path = path
            self.lbl_csv.configure(text=path, text_color="#4ade80")

    def select_folder(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_folder = path
            self.lbl_folder.configure(text=path, text_color="#4ade80")

    def start_download(self):
        if self.is_downloading:
            return
        if not self.csv_path:
            messagebox.showwarning("Missing CSV", "Please select a source CSV file first.")
            return
        if not self.output_folder:
            messagebox.showwarning("Missing Folder", "Please select an output folder first.")
            return

        self.is_downloading = True
        self.set_controls_state(False)

        # Reset log and progress
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")
        self.update_progress(0, 0, "Status: Reading CSV file...")

        # Run process in a separate daemon thread
        threading.Thread(target=self.process_downloads, daemon=True).start()

    # ---------------- Image Processing & Download Logic ---------------- #

    @staticmethod
    def convert_and_save_jpeg(image_bytes: bytes, target_path: str):
        """Open any image format (WebP, RGBA, etc.), convert to RGB, save as .jpg."""
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Handle alpha channel / transparency by pasting on pure white background
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                rgba = img.convert("RGBA")
                white_bg = Image.new("RGB", rgba.size, (255, 255, 255))
                white_bg.paste(rgba, mask=rgba.split()[3])
                final_img = white_bg
            elif img.mode != "RGB":
                final_img = img.convert("RGB")
            else:
                final_img = img

            # Save as JPEG with quality 90
            final_img.save(target_path, format="JPEG", quality=90, optimize=True)

    def process_downloads(self):
        self.log_message(f"[INFO] Reading CSV: {self.csv_path}")
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            self.log_message(f"[ERROR] Failed to read CSV: {e}")
            self.update_progress(0, 0, "Status: Error reading CSV")
            self.is_downloading = False
            self.set_controls_state(True)
            return

        # Validate required columns
        if "name" not in df.columns or "url" not in df.columns:
            self.log_message("[ERROR] CSV must contain 'name' and 'url' columns.")
            self.update_progress(0, 0, "Status: Invalid CSV format")
            self.is_downloading = False
            self.set_controls_state(True)
            return

        total_rows = len(df)
        if total_rows == 0:
            self.log_message("[WARN] CSV file contains no rows.")
            self.update_progress(0, 0, "Status: Empty CSV")
            self.is_downloading = False
            self.set_controls_state(True)
            return

        self.update_progress(0, total_rows, f"Status: Processing 0 / {total_rows}")

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        })

        saved_count = 0
        skipped_count = 0
        failed_count = 0

        for idx, (_, row) in enumerate(df.iterrows(), start=1):
            row_num = idx + 1
            raw_name = row.get("name")
            raw_url = row.get("url")

            # Check for missing name or URL
            if pd.isna(raw_name) or str(raw_name).strip() == "":
                self.log_message(f"[SKIP] Row {row_num}: Missing product name.")
                skipped_count += 1
                self.update_progress(idx, total_rows, f"Status: Processing {idx} / {total_rows}")
                continue

            if pd.isna(raw_url) or str(raw_url).strip() == "":
                self.log_message(f"[SKIP] Row {row_num}: Missing image URL for '{raw_name}'.")
                skipped_count += 1
                self.update_progress(idx, total_rows, f"Status: Processing {idx} / {total_rows}")
                continue

            product_name = str(raw_name).strip()
            image_url = str(raw_url).strip()

            # Handle protocol-relative URLs
            if image_url.startswith("//"):
                image_url = f"https:{image_url}"

            sanitized_name = sanitize_filename(product_name)
            if not sanitized_name:
                self.log_message(f"[SKIP] Row {row_num}: Invalid product name '{product_name}'.")
                skipped_count += 1
                self.update_progress(idx, total_rows, f"Status: Processing {idx} / {total_rows}")
                continue

            # Conflict resolution: append counter if target file already exists
            filename = f"{sanitized_name}.jpg"
            target_path = os.path.join(self.output_folder, filename)
            counter = 1
            while os.path.exists(target_path):
                filename = f"{sanitized_name}_{counter}.jpg"
                target_path = os.path.join(self.output_folder, filename)
                counter += 1

            # Download & save image
            try:
                response = session.get(image_url, timeout=15)
                response.raise_for_status()

                self.convert_and_save_jpeg(response.content, target_path)

                self.log_message(f"[SUCCESS] Row {row_num}: Saved '{filename}'")
                saved_count += 1
            except Exception as e:
                self.log_message(f"[FAIL] Row {row_num}: Failed downloading '{product_name}' -> {e}")
                failed_count += 1

            self.update_progress(idx, total_rows, f"Status: Processing {idx} / {total_rows}")

        # Final summary
        summary = f"Done — Saved: {saved_count} | Skipped: {skipped_count} | Failed: {failed_count}"
        self.log_message("\n" + "=" * 54)
        self.log_message("DOWNLOAD SUMMARY")
        self.log_message(summary)
        self.log_message("=" * 54)

        self.update_progress(total_rows, total_rows, f"Status: {summary}")
        self.is_downloading = False
        self.set_controls_state(True)


if __name__ == "__main__":
    app = EzPhotoDownloaderApp()
    app.mainloop()

