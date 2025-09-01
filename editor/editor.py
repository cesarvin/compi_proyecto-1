import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests 

class CodeEditor(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        
        self.line_numbers = tk.Canvas(self, width=40, bg='#f0f0f0', highlightthickness=0)
        self.line_numbers.pack(side="left", fill="y")

        self.text_area = tk.Text(self, undo=True, wrap="none", *args, **kwargs)
        self.text_area.pack(side="right", fill="both", expand=True)

        self.text_area.config(yscrollcommand=self.text_scroll)
        
        self.text_area.bind("<<Modified>>", self.text_change)
        self.text_area.bind("<Configure>", self.text_change)
        self.text_area.bind("<KeyRelease>", self.text_change)
        self.text_area.bind("<MouseWheel>", self.text_change)

        self.udpate_lines = True

    def text_scroll(self, *args):
        self.line_numbers.yview("moveto", args[0])
        self.text_change()

    def text_change(self, event=None):
        self.udpate_lines = True
        self.after(50, self.redraw_lines)

    def redraw_lines(self):
        if not self.udpate_lines:
            return
        
        self.line_numbers.delete("all")

        first_visible = int(self.text_area.index("@0,0").split('.')[0])
        last_visible = int(self.text_area.index(f"@0,{self.text_area.winfo_height()}").split('.')[0]) + 1
        
        for i in range(first_visible, last_visible + 1):
            line_info = self.text_area.dlineinfo(f"{i}.0")
            if line_info:
                y_pos = line_info[1]
                self.line_numbers.create_text(38, y_pos, anchor="ne", text=str(i), fill="grey")
        
        self.udpate_lines = False

    def insert(self, *args, **kwargs):
        return self.text_area.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.text_area.delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.text_area.get(*args, **kwargs)

def compile():
    
    codigo = editor_text.get("1.0", "end-1c")
    
    if not codigo.strip():
        messagebox.showinfo("Compilar", "No hay código para analizar")
        return

    url = "http://localhost:8000/compilador"
    
    tab_to_select = output_frame 
    
    try:
        data = {"code": codigo}
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        output_text.config(state="normal")
        output_text.delete("1.0", tk.END)

        info_text.config(state="normal")
        info_text.delete("1.0", tk.END)
        
        compilation_success = result.get('compilado', False)
        message = result.get('result', 'No hay resultados')
        errors = result.get('errors', [])
        symbol_table = result.get('symbol_table', [])
        type_table = result.get('type_table', {})

        output_text.insert(tk.END, f"Resultado del analisis: {message}\n")
        output_text.insert(tk.END, ("-" * 50) + "\n\n")
        
        if not compilation_success and errors:
            output_text.insert(tk.END, "Existen los siguientes errores:\n")
            for error in errors:
                line = error.get('line', '?')
                col = error.get('column', '?')
                msg = error.get('message', '?')
                output_text.insert(tk.END, f"  - [Línea {line}, pos {col}]: {msg}\n")
            tab_to_select = output_frame 
            
        if compilation_success:
            has_info = False
            if symbol_table:
                has_info = True
                info_text.insert(tk.END, "=" * 43 + " SYMBOL TABLE " + "=" * 43 + "\n")
                header = f"{'ID':<15} {'TIPO':<50} {'ROL':<15} {'ÁMBITO':<10}\n"
                info_text.insert(tk.END, header)
                info_text.insert(tk.END, ("-" * 100) + "\n")
                
                for i, scope in enumerate(symbol_table, 1):
                    for symbol in scope.values():
                        sid = str(symbol.get('id', '-'))
                        stype = str(symbol.get('data_type', '-'))
                        srole = str(symbol.get('role', '-'))
                        sscope = str(symbol.get('scope', '-'))
                        info_text.insert(tk.END, f"{sid:<15} {stype:<50} {srole:<15} {sscope:<10}\n")
                info_text.insert(tk.END, "\n")

            if type_table:
                has_info = True
                info_text.insert(tk.END, "=" * 43 + " TYPE TABLE " + "=" * 43 + "\n")
                header = f"{'NOMBRE':<15} {'HEREDA DE':<15} {'ATRIBUTOS'}\n"
                info_text.insert(tk.END, header)
                info_text.insert(tk.END, ("-" * 100) + "\n")
                for name, type_info in type_table.items():
                    inherits = str(type_info.get('inherits', 'None'))
                    attrs = str(type_info.get('attributes', 'N/A'))
                    info_text.insert(tk.END, f"  {str(name):<15} {inherits:<15} {attrs}\n")

            if has_info:
                tab_to_select = info_frame

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor.\n\nError: {e}")
    except Exception as e:
        messagebox.showerror("Error Inesperado", f"Ocurrió un error.\n\nError: {e}")
    finally:
        output_text.config(state="disabled")
        info_text.config(state="disabled")
        bottom_notebook.select(tab_to_select)


def clear():
    if not messagebox.askokcancel("Limpiar", "Eliminar el código actual ¿Continuar?"):
        return
        
    editor_text.delete("1.0", tk.END)
    
    output_text.config(state="normal")
    output_text.delete("1.0", tk.END)
    output_text.config(state="disabled")
    
    info_text.config(state="normal")
    info_text.delete("1.0", tk.END)
    info_text.config(state="disabled")

def open_file():
    filepath = filedialog.askopenfilename(
        title="Abrir códigos",
        filetypes=[("Archivos CPS", "*.cps"), ("Todos los Archivos", "*.*")]
    )
    if not filepath:
        return
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            editor_text.delete("1.0", tk.END)
            editor_text.insert("1.0", content)
    except Exception as e:
        messagebox.showerror("Error", f"Error al leer el archivo.\nError: {e}")


# ---------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------
root = tk.Tk()
root.title("Editor Compiscript")
root.geometry("1200x1080")

top_frame = tk.Frame(root)
top_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

button_frame = tk.Frame(top_frame)
button_frame.pack(fill="x", pady=(0, 5))

tk.Button(button_frame, text="Abrir", command=open_file).pack(side="left", padx=2)
tk.Button(button_frame, text="Limpiar", command=clear).pack(side="left", padx=2)
tk.Button(button_frame, text="Compilar", command=compile, bg="#a0e0a0", fg="black").pack(side="left", padx=2)

editor_text = CodeEditor(top_frame)
editor_text.pack(fill="both", expand=True)

bottom_notebook = ttk.Notebook(root)
bottom_notebook.pack(side="bottom", fill="both", expand=True, padx=5, pady=(0, 5))

output_frame = ttk.Frame(bottom_notebook)
bottom_notebook.add(output_frame, text='Output')
output_text = tk.Text(output_frame, height=8)
output_text.pack(fill="both", expand=True)
output_text.config(state="disabled", bg="#e0e0e0")

info_frame = ttk.Frame(bottom_notebook)
bottom_notebook.add(info_frame, text='Información')
info_text = tk.Text(info_frame, height=8)
info_text.pack(fill="both", expand=True)
info_text.config(state="disabled", bg="#e0e0e0")

root.mainloop()