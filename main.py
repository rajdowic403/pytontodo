import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import init_db, get_connection

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacja TODO")
        self.root.geometry("800x600")
        
        # Inicjalizacja bazy danych
        init_db()
        
        self.create_widgets()
        self.load_categories()
        self.load_tasks()
        
    def create_widgets(self):
        # Główny kontener
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel filtrów
        filter_frame = ttk.LabelFrame(main_frame, text="Filtry")
        filter_frame.pack(fill=tk.X, pady=5)
        
        self.category_var = tk.StringVar()
        self.category_filter = ttk.Combobox(filter_frame, textvariable=self.category_var, state="readonly")
        self.category_filter.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.show_completed = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Pokaż ukończone", variable=self.show_completed,
                       command=self.load_tasks).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Odśwież", command=self.refresh).pack(side=tk.RIGHT, padx=5)
        
        # Lista zadań
        self.tasks_list = ttk.Treeview(main_frame, columns=("title", "category", "status", "created"), show="headings")
        self.tasks_list.heading("title", text="Zadanie")
        self.tasks_list.heading("category", text="Kategoria")
        self.tasks_list.heading("status", text="Status")
        self.tasks_list.heading("created", text="Data dodania")
        
        self.tasks_list.column("title", width=200)
        self.tasks_list.column("category", width=150)
        self.tasks_list.column("status", width=100)
        self.tasks_list.column("created", width=150)
        
        self.tasks_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tasks_list.bind("<Double-1>", self.edit_task)
        
        # Panel przycisków
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Dodaj zadanie", command=self.add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edytuj zadanie", command=self.edit_selected_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Usuń zadanie", command=self.delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Oznacz jako wykonane", command=self.toggle_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Dodaj kategorię", command=self.add_category).pack(side=tk.RIGHT, padx=5)
    
    def refresh(self):
        self.load_categories()
        self.load_tasks()
    
    def load_categories(self):
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM categories ORDER BY name")
                categories = ["Wszystkie kategorie"] + [row[0] for row in cursor.fetchall()]
                
                current_value = self.category_var.get()
                self.category_filter['values'] = categories
                
                if current_value in categories:
                    self.category_var.set(current_value)
                else:
                    self.category_var.set("Wszystkie kategorie")
                
                self.category_filter.bind("<<ComboboxSelected>>", lambda e: self.load_tasks())
                
            except SystemError as e:
                messagebox.showerror("Błąd", f"Nie można załadować kategorii: {e}")
            finally:
                conn.close()
    
    def load_tasks(self):
        self.tasks_list.delete(*self.tasks_list.get_children())
        
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                query = """
                SELECT t.id, t.title, c.name as category, t.is_completed, 
                       DATE_FORMAT(t.created_at, '%%Y-%%m-%%d %%H:%%i') as created_date
                FROM tasks t 
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE %s OR t.is_completed = %s
                """
                params = [True, self.show_completed.get()]
                
                if self.category_var.get() != "Wszystkie kategorie":
                    query += " AND c.name = %s"
                    params.append(self.category_var.get())
                
                query += " ORDER BY t.created_at DESC"
                
                cursor.execute(query, params)
                
                for task in cursor.fetchall():
                    status = "✔️" if task['is_completed'] else "❌"
                    self.tasks_list.insert("", tk.END, 
                                         values=(task['title'], task['category'], status, task['created_date']), 
                                         iid=task['id'])
                
            except SystemError as e:
                messagebox.showerror("Błąd", f"Nie można załadować zadań: {e}")
            finally:
                conn.close()
    
    def add_task(self):
        def save_task():
            title = title_entry.get().strip()
            description = desc_entry.get("1.0", tk.END).strip()
            category = category_var.get()
            
            if not title:
                messagebox.showerror("Błąd", "Tytuł jest wymagany")
                return
            
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM categories WHERE name = %s", (category,))
                    category_id = cursor.fetchone()[0]
                    
                    cursor.execute("""
                    INSERT INTO tasks (title, description, category_id)
                    VALUES (%s, %s, %s)
                    """, (title, description, category_id))
                    
                    conn.commit()
                    self.load_tasks()
                    add_window.destroy()
                except SystemError as e:
                    conn.rollback()
                    messagebox.showerror("Błąd", f"Nie można dodać zadania: {e}")
                finally:
                    conn.close()
        
        add_window = tk.Toplevel(self.root)
        add_window.title("Dodaj nowe zadanie")
        add_window.grab_set()
        
        ttk.Label(add_window, text="Tytuł:").pack(pady=5)
        title_entry = ttk.Entry(add_window, width=50)
        title_entry.pack(pady=5)
        
        ttk.Label(add_window, text="Opis:").pack(pady=5)
        desc_entry = tk.Text(add_window, width=50, height=10)
        desc_entry.pack(pady=5)
        
        ttk.Label(add_window, text="Kategoria:").pack(pady=5)
        category_var = tk.StringVar()
        
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM categories ORDER BY name")
                categories = [row[0] for row in cursor.fetchall()]
                
                if not categories:
                    messagebox.showwarning("Uwaga", "Brak kategorii. Najpierw dodaj kategorię.")
                    add_window.destroy()
                    self.add_category()
                    return
                
                category_combobox = ttk.Combobox(add_window, textvariable=category_var, 
                                               values=categories, state="readonly")
                category_combobox.current(0)
                category_combobox.pack(pady=5)
                
                ttk.Button(add_window, text="Zapisz", command=save_task).pack(pady=10)
                
            except SystemError as e:
                messagebox.showerror("Błąd", f"Nie można załadować kategorii: {e}")
            finally:
                conn.close()
    
    def edit_selected_task(self):
        selected = self.tasks_list.selection()
        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz zadanie do edycji")
            return
        self.edit_task(None)
    
    def edit_task(self, event):
        selected = self.tasks_list.selection()
        if not selected:
            return
        
        task_id = selected[0]
        
        def save_changes():
            title = title_entry.get().strip()
            description = desc_entry.get("1.0", tk.END).strip()
            category = category_var.get()
            
            if not title:
                messagebox.showerror("Błąd", "Tytuł jest wymagany")
                return
            
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM categories WHERE name = %s", (category,))
                    category_id = cursor.fetchone()[0]
                    
                    cursor.execute("""
                    UPDATE tasks SET title = %s, description = %s, category_id = %s
                    WHERE id = %s
                    """, (title, description, category_id, task_id))
                    
                    conn.commit()
                    self.load_tasks()
                    edit_window.destroy()
                except SystemError as e:
                    conn.rollback()
                    messagebox.showerror("Błąd", f"Nie można zaktualizować zadania: {e}")
                finally:
                    conn.close()
        
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                SELECT t.title, t.description, c.name as category 
                FROM tasks t LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.id = %s
                """, (task_id,))
                task = cursor.fetchone()
                
                edit_window = tk.Toplevel(self.root)
                edit_window.title("Edytuj zadanie")
                edit_window.grab_set()
                
                ttk.Label(edit_window, text="Tytuł:").pack(pady=5)
                title_entry = ttk.Entry(edit_window, width=50)
                title_entry.insert(0, task['title'])
                title_entry.pack(pady=5)
                
                ttk.Label(edit_window, text="Opis:").pack(pady=5)
                desc_entry = tk.Text(edit_window, width=50, height=10)
                desc_entry.insert("1.0", task['description'])
                desc_entry.pack(pady=5)
                
                ttk.Label(edit_window, text="Kategoria:").pack(pady=5)
                category_var = tk.StringVar(value=task['category'])
                
                cursor.execute("SELECT name FROM categories ORDER BY name")
                categories = [row[0] for row in cursor.fetchall()]
                category_combobox = ttk.Combobox(edit_window, textvariable=category_var, 
                                               values=categories, state="readonly")
                category_combobox.pack(pady=5)
                
                ttk.Button(edit_window, text="Zapisz zmiany", command=save_changes).pack(pady=10)
                
            except SystemError as e:
                messagebox.showerror("Błąd", f"Nie można załadować danych zadania: {e}")
            finally:
                conn.close()
    
    def delete_task(self):
        selected = self.tasks_list.selection()
        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz zadanie do usunięcia")
            return
        
        if not messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć wybrane zadanie?"):
            return
        
        task_id = selected[0]
        
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
                conn.commit()
                self.load_tasks()
            except SystemError as e:
                conn.rollback()
                messagebox.showerror("Błąd", f"Nie można usunąć zadania: {e}")
            finally:
                conn.close()
    
    def toggle_task(self):
        selected = self.tasks_list.selection()
        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz zadanie do zmiany statusu")
            return
        
        task_id = selected[0]
        
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT is_completed FROM tasks WHERE id = %s", (task_id,))
                current_status = cursor.fetchone()[0]
                
                cursor.execute("UPDATE tasks SET is_completed = %s WHERE id = %s", (not current_status, task_id))
                conn.commit()
                self.load_tasks()
            except SystemError as e:
                conn.rollback()
                messagebox.showerror("Błąd", f"Nie można zmienić statusu zadania: {e}")
            finally:
                conn.close()
    
    def add_category(self):
        category = simpledialog.askstring("Nowa kategoria", "Podaj nazwę nowej kategorii:")
        if not category:
            return
        
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category,))
                conn.commit()
                self.load_categories()
            except SystemError as e:
                messagebox.showerror("Błąd", f"Nie można dodać kategorii: {e}")
                conn.rollback()
            finally:
                conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()