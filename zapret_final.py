#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zapret GUI Control - Финальная версия
EXE с встроенными файлами и распаковкой в AppData/Local/ZapretControl
"""

import os
import sys
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import tempfile
import shutil
import hashlib
import base64
import zlib

# Импортируем sys для проверки frozen
if getattr(sys, 'frozen', False):
    # Если мы запущены из EXE
    import PyInstaller.__main__ as pyi_main

class FileManager:
    """Управление файлами: распаковка, проверка, обновление"""
    
    @staticmethod
    def get_appdata_dir():
        """Получить папку в AppData/Local/ZapretControl"""
        appdata = os.getenv('LOCALAPPDATA')
        if not appdata:
            appdata = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Local')
        
        app_dir = os.path.join(appdata, 'ZapretControl')
        os.makedirs(app_dir, exist_ok=True)
        return app_dir
    
    @staticmethod
    def get_required_files():
        """Список необходимых файлов"""
        return [
            ("winws.exe", "Основной исполняемый файл zapret"),
            ("WinDivert.dll", "Библиотека драйвера WinDivert"),
            ("WinDivert64.sys", "Драйвер Windows")
        ]
    
    @staticmethod
    def check_files(app_dir):
        """Проверить наличие всех файлов в указанной папке"""
        missing = []
        for filename, description in FileManager.get_required_files():
            filepath = os.path.join(app_dir, filename)
            if not os.path.exists(filepath):
                missing.append((filename, description))
        
        return missing
    
    @staticmethod
    def extract_embedded_files(app_dir):
        """
        Распаковать встроенные файлы из EXE в AppData/Local/ZapretControl
        """
        print(f"Проверка файлов в: {app_dir}")
        
        # Проверяем наличие файлов
        missing = FileManager.check_files(app_dir)
        
        if not missing:
            print("Все файлы найдены")
            return True
        
        print(f"Не найдено файлов: {len(missing)}. Распаковываем...")
        
        # Если мы в EXE, распаковываем из ресурсов PyInstaller
        if getattr(sys, 'frozen', False):
            try:
                # PyInstaller создает временную папку с ресурсами
                # sys._MEIPASS содержит путь к временной папке с ресурсами
                base_path = sys._MEIPASS
                print(f"Ресурсы EXE в: {base_path}")
                
                # Распаковываем файлы
                extracted_count = 0
                for filename, description in FileManager.get_required_files():
                    src_path = os.path.join(base_path, filename)
                    dst_path = os.path.join(app_dir, filename)
                    
                    if os.path.exists(src_path):
                        try:
                            shutil.copy2(src_path, dst_path)
                            print(f"✓ Распакован: {filename}")
                            extracted_count += 1
                        except Exception as e:
                            print(f"✗ Ошибка распаковки {filename}: {e}")
                    else:
                        print(f"✗ Файл не найден в ресурсах: {filename}")
                
                if extracted_count > 0:
                    print(f"Распаковано файлов: {extracted_count}")
                    return True
                
            except Exception as e:
                print(f"Ошибка распаковки из EXE: {e}")
        
        return False

class ZapretControlGUI:
    """Главный класс GUI"""
    
    def __init__(self, root, app_dir):
        self.root = root
        self.app_dir = app_dir
        self.winws_process = None
        
        self.setup_window()
        self.create_gui()
        
        # Проверка файлов при запуске
        self.check_files_on_start()
    
    def setup_window(self):
        """Настройка окна"""
        self.root.title("Zapret GUI Control v1.0")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Центрирование окна
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def check_files_on_start(self):
        """Проверка файлов при запуске"""
        missing = FileManager.check_files(self.app_dir)
        
        if missing:
            files_list = "\n".join([f"• {name} - {desc}" for name, desc in missing])
            
            response = messagebox.showinfo(
                "Файлы не найдены",
                f"Для работы программы нужны файлы:\n\n{files_list}\n\n"
                f"Папка: {self.app_dir}\n\n"
                "Поместите файлы в указанную папку и перезапустите программу."
            )
            
            # Отключаем кнопку запуска если файлов нет
            if hasattr(self, 'toggle_button'):
                self.toggle_button.config(state='disabled')
    
    def create_gui(self):
        """Создание интерфейса"""
        # Notebook (вкладки)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладки
        self.create_control_tab()
        self.create_creators_tab()
        self.create_info_tab()
    
    def create_control_tab(self):
        """Вкладка управления"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Управление")
        
        # Заголовок
        ttk.Label(frame, text="Управление Zapret", 
                 font=("Arial", 14, "bold")).pack(pady=15)
        
        # Информация о папке
        path_text = f"Файлы в: {os.path.basename(self.app_dir)}"
        ttk.Label(frame, text=path_text, font=("Arial", 9)).pack(pady=5)
        
        # Проверка файлов
        self.check_files_button = ttk.Button(
            frame,
            text="Проверить файлы",
            command=self.verify_files,
            width=20
        )
        self.check_files_button.pack(pady=10)
        
        # Кнопка запуска/остановки
        self.toggle_button = ttk.Button(
            frame,
            text="Включить обход",
            command=self.toggle_zapret,
            width=20,
            state='normal'
        )
        self.toggle_button.pack(pady=10)
        
        # Статус
        self.status_label = tk.Label(
            frame,
            text="Статус: Выключен",
            font=("Arial", 12),
            width=20,
            relief=tk.RIDGE,
            padx=10,
            pady=5,
            bg="#f8d7da",
            fg="#721c24"
        )
        self.status_label.pack(pady=15)
        
        # Кнопка принудительного завершения
        self.kill_button = ttk.Button(
            frame,
            text="Принудительно завершить",
            command=self.force_kill,
            width=20
        )
        self.kill_button.pack(pady=10)
        
        # Информация о процессе
        self.process_info = ttk.Label(frame, text="", font=("Arial", 9))
        self.process_info.pack(pady=5)
    
    def create_creators_tab(self):
        """Вкладка создателей"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Создатели")
        
        ttk.Label(frame, text="Памятник создателей", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        creators = [
            "1. arutt",
            "2. arutt228", 
            "3. c00lkid(arutt)",
            "4. arutt228-bit",
            "5. мымра"
        ]
        
        for creator in creators:
            label = tk.Label(
                frame,
                text=creator,
                font=("Arial", 11),
                anchor=tk.W,
                justify=tk.LEFT
            )
            label.pack(pady=5, padx=50, fill=tk.X)
    
    def create_info_tab(self):
        """Вкладка информации"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Информация")
        
        ttk.Label(frame, text="Информация", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        # YouTube ссылка
        link_frame = ttk.Frame(frame)
        link_frame.pack(pady=15, padx=50, fill=tk.X)
        
        ttk.Label(link_frame, text="YouTube канал:", 
                 font=("Arial", 10)).pack(side=tk.LEFT)
        
        ttk.Button(
            link_frame,
            text="Перейти",
            command=lambda: webbrowser.open("https://www.youtube.com/@arutt228"),
            width=10
        ).pack(side=tk.RIGHT)
        
        # Версия
        ttk.Label(frame, text="Версия приложения: 1.0", 
                 font=("Arial", 10, "bold")).pack(pady=20)
        
        # Папка с файлами
        ttk.Label(frame, 
                 text=f"Папка с файлами:\n{self.app_dir}",
                 font=("Courier", 9)).pack(pady=10)
        
        # Кнопка открытия папки
        ttk.Button(
            frame,
            text="Открыть папку с файлами",
            command=self.open_app_folder,
            width=20
        ).pack(pady=10)
    
    def verify_files(self):
        """Проверить наличие файлов"""
        missing = FileManager.check_files(self.app_dir)
        
        if not missing:
            messagebox.showinfo("Проверка", "Все необходимые файлы найдены!")
            self.toggle_button.config(state='normal')
        else:
            files_list = "\n".join([f"• {name}" for name, _ in missing])
            messagebox.showwarning(
                "Файлы не найдены",
                f"Отсутствуют файлы:\n\n{files_list}\n\n"
                f"Папка: {self.app_dir}"
            )
            self.toggle_button.config(state='disabled')
    
    def open_app_folder(self):
        """Открыть папку с файлами"""
        try:
            os.startfile(self.app_dir)
        except:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{self.app_dir}")
    
    def toggle_zapret(self):
        """Включить/выключить"""
        if self.winws_process is None:
            self.start_winws()
        else:
            self.stop_winws()
    
    def start_winws(self):
        """Запуск winws.exe"""
        try:
            winws_path = os.path.join(self.app_dir, "winws.exe")
            
            if not os.path.exists(winws_path):
                messagebox.showerror("Ошибка", f"Файл не найден: {winws_path}")
                return
            
            # Создаем список доменов если нужно
            list_path = os.path.join(self.app_dir, "list-general.txt")
            if not os.path.exists(list_path):
                with open(list_path, "w", encoding="utf-8") as f:
                    f.write("# Список доменов для обхода\n")
            
            # Запуск
            creation_flags = 0x08000000  # CREATE_NO_WINDOW
            
            self.winws_process = subprocess.Popen(
                [winws_path, "--wf-raw=@list-general.txt"],
                creationflags=creation_flags,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.app_dir
            )
            
            self.toggle_button.config(text="Выключить обход")
            self.update_status("Работает", "#d4edda", "#155724")
            self.process_info.config(text=f"PID: {self.winws_process.pid}")
            
            if self.winws_process.poll() is not None:
                error_msg = f"Процесс завершился: код {self.winws_process.returncode}"
                messagebox.showerror("Ошибка", error_msg)
                self.winws_process = None
                self.update_status("Выключен", "#f8d7da", "#721c24")
            else:
                messagebox.showinfo("Запуск", "Zapret успешно запущен")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить: {str(e)}")
            self.winws_process = None
    
    def stop_winws(self):
        """Остановка"""
        if self.winws_process:
            try:
                self.winws_process.terminate()
                self.winws_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.kill_process_tree(self.winws_process.pid)
            
            self.winws_process = None
            self.toggle_button.config(text="Включить обход")
            self.update_status("Выключен", "#f8d7da", "#721c24")
            self.process_info.config(text="")
            messagebox.showinfo("Остановка", "Zapret остановлен")
    
    def force_kill(self):
        """Принудительное завершение"""
        if self.winws_process:
            self.kill_process_tree(self.winws_process.pid)
            self.winws_process = None
            self.toggle_button.config(text="Включить обход")
            self.update_status("Выключен", "#f8d7da", "#721c24")
            self.process_info.config(text="")
            messagebox.showinfo("Завершение", "Процесс завершен")
        else:
            # Завершаем все процессы winws.exe
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "winws.exe"],
                    creationflags=0x08000000,
                    check=False
                )
                messagebox.showinfo("Очистка", "Все процессы завершены")
            except:
                pass
    
    def kill_process_tree(self, pid):
        """Убить дерево процессов"""
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                creationflags=0x08000000,
                check=True
            )
        except:
            subprocess.run(
                ["taskkill", "/F", "/IM", "winws.exe"],
                creationflags=0x08000000,
                check=False
            )
    
    def update_status(self, text, bg, fg):
        """Обновить статус"""
        self.status_label.config(text=f"Статус: {text}", bg=bg, fg=fg)

# Функции для работы с правами администратора
def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапуск с правами администратора"""
    hwnd = 0
    lpverb = "runas"
    lpfile = sys.executable
    lpparameters = ' '.join([f'"{arg}"' for arg in sys.argv])
    nshow = 0
    
    result = ctypes.windll.shell32.ShellExecuteW(
        hwnd, lpverb, lpfile, lpparameters, None, nshow
    )
    
    if result <= 32:
        print(f"Ошибка запуска с правами администратора: код {result}")
        sys.exit(1)
    
    sys.exit(0)

def main():
    """Главная функция"""
    # Проверка ОС
    if sys.platform != "win32":
        messagebox.showerror("Ошибка", "Программа работает только на Windows")
        sys.exit(1)
    
    # Проверка прав администратора
    if not is_admin():
        print("Требуются права администратора...")
        run_as_admin()
        return
    
    # Получаем папку в AppData
    app_dir = FileManager.get_appdata_dir()
    print(f"Рабочая папка: {app_dir}")
    
    # Проверяем/распаковываем файлы
    FileManager.extract_embedded_files(app_dir)
    
    # Создаем GUI
    root = tk.Tk()
    try:
        app = ZapretControlGUI(root, app_dir)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка запуска: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()