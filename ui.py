# -*- coding: utf-8 -*-
"""Interface gráfica Tkinter do Rey Search."""
import csv, json, logging, queue, threading, time, os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from logger import configure_logger
from search_engine import search_files

BG="#1e1e2e"; PANEL="#272239"; DARK="#171522"; PURPLE="#8b5cf6"
LIGHT="#c4b5fd"; WHITE="#f8fafc"; MUTED="#a6a0bb"; GREEN="#4ade80"
YELLOW="#fbbf24"; RED="#fb7185"

class ReySearchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rey Search")
        self.geometry("1120x760"); self.minsize(900,650); self.configure(bg=BG)
        self.update_idletasks()
        self.geometry(f"1120x760+{(self.winfo_screenwidth()-1120)//2}+{(self.winfo_screenheight()-760)//2}")
        self.results=[]; self.log_queue=queue.Queue(); self.logger=configure_logger(self.log_queue)
        self.cancel_event=threading.Event(); self.worker=None; self.running=False; self.started_at=None
        self._styles(); self._build()
        self.after(100,self._poll)
        self.logger.info("Rey Search iniciado.")
        self.protocol("WM_DELETE_WINDOW",self._close)

    def _styles(self):
        s=ttk.Style(self)
        try:s.theme_use("clam")
        except tk.TclError:pass
        s.configure("Treeview",background=DARK,foreground=WHITE,fieldbackground=DARK,rowheight=27,borderwidth=0)
        s.configure("Treeview.Heading",background=PANEL,foreground=LIGHT,font=("Segoe UI",9,"bold"),relief="flat")
        s.map("Treeview",background=[("selected","#553c88")],foreground=[("selected",WHITE)])
        s.configure("TProgressbar",troughcolor=DARK,background=PURPLE,bordercolor=DARK,lightcolor=PURPLE,darkcolor=PURPLE)

    def _btn(self,parent,text,command,kind="primary"):
        bg={"primary":PURPLE,"subtle":"#3b2b55","danger":"#54232e"}[kind]
        return tk.Button(parent,text=text,command=command,bg=bg,fg=WHITE,activebackground=bg,
                         activeforeground=WHITE,relief="flat",bd=0,padx=13,pady=9,
                         font=("Segoe UI",9,"bold"),cursor="hand2")

    def _build(self):
        root=tk.Frame(self,bg=BG,padx=18,pady=14); root.pack(fill="both",expand=True)
        head=tk.Frame(root,bg=BG); head.pack(fill="x",pady=(0,12))
        tk.Label(head,text="RS",bg=PURPLE,fg=WHITE,font=("Segoe UI",17,"bold"),width=3,pady=5).pack(side="left",padx=(0,12))
        titles=tk.Frame(head,bg=BG); titles.pack(side="left",fill="x",expand=True)
        tk.Label(titles,text="Rey Search",bg=BG,fg=WHITE,font=("Segoe UI",21,"bold")).pack(anchor="w")
        tk.Label(titles,text="BUSCA INTELIGENTE EM ARQUIVOS TXT",bg=BG,fg=LIGHT,font=("Segoe UI",9,"bold")).pack(anchor="w")
        self.status=tk.Label(head,text="● PRONTO",bg=BG,fg=GREEN,font=("Segoe UI",10,"bold")); self.status.pack(side="right")

        cfg=tk.Frame(root,bg=PANEL,padx=14,pady=12); cfg.pack(fill="x",pady=(0,12))
        tk.Label(cfg,text="Pasta de busca",bg=PANEL,fg=WHITE,font=("Segoe UI",10,"bold")).grid(row=0,column=0,sticky="w",pady=(0,5))
        self.folder=tk.StringVar()
        self.folder_entry=tk.Entry(cfg,textvariable=self.folder,bg=DARK,fg=WHITE,insertbackground=WHITE,relief="flat",font=("Segoe UI",10))
        self.folder_entry.grid(row=1,column=0,sticky="ew",ipady=8,padx=(0,8))
        self._btn(cfg,"Procurar pasta",self._browse,"subtle").grid(row=1,column=1)
        tk.Label(cfg,text="Palavra-chave(s) — separe várias por vírgula",bg=PANEL,fg=WHITE,font=("Segoe UI",10,"bold")).grid(row=2,column=0,sticky="w",pady=(12,5))
        self.keywords=tk.StringVar()
        tk.Entry(cfg,textvariable=self.keywords,bg=DARK,fg=WHITE,insertbackground=WHITE,relief="flat",font=("Segoe UI",10)).grid(row=3,column=0,columnspan=2,sticky="ew",ipady=8)
        opts=tk.Frame(cfg,bg=PANEL);opts.grid(row=4,column=0,columnspan=2,sticky="w",pady=(10,0))
        self.recursive=tk.BooleanVar(value=True);self.case=tk.BooleanVar();self.whole=tk.BooleanVar();self.regex=tk.BooleanVar()
        for label,var in [("Buscar em subpastas",self.recursive),("Diferenciar maiúsculas",self.case),("Palavra inteira",self.whole),("Usar regex",self.regex)]:
            tk.Checkbutton(opts,text=label,variable=var,bg=PANEL,fg=MUTED,activebackground=PANEL,activeforeground=WHITE,selectcolor=DARK,font=("Segoe UI",9),relief="flat").pack(side="left",padx=(0,14))
        cfg.columnconfigure(0,weight=1)

        actions=tk.Frame(root,bg=BG);actions.pack(fill="x",pady=(0,10))
        self.start_btn=self._btn(actions,"🔍  INICIAR BUSCA",self._start);self.start_btn.pack(side="left",fill="x",expand=True,ipady=5,padx=(0,8))
        self.stop_btn=self._btn(actions,"⏹  PARAR",self._stop,"danger");self.stop_btn.pack(side="left",padx=(0,8),ipady=5)
        self.export_btn=self._btn(actions,"💾  Exportar resultados",self._export,"subtle");self.export_btn.pack(side="left",ipady=5)
        pf=tk.Frame(root,bg=BG);pf.pack(fill="x",pady=(0,10))
        self.progress=ttk.Progressbar(pf,mode="indeterminate");self.progress.pack(fill="x")
        self.stats=tk.StringVar(value="Arquivos: 0  |  Ocorrências: 0  |  Tempo: 0,0s")
        tk.Label(pf,textvariable=self.stats,bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",pady=(4,0))

        split=tk.PanedWindow(root,orient="vertical",bg=BG,bd=0,sashwidth=7,showhandle=False);split.pack(fill="both",expand=True)
        rf=tk.Frame(split,bg=PANEL,padx=10,pady=10);lf=tk.Frame(split,bg=PANEL,padx=10,pady=10)
        split.add(rf,minsize=180);split.add(lf,minsize=115)
        rh=tk.Frame(rf,bg=PANEL);rh.pack(fill="x",pady=(0,7))
        tk.Label(rh,text="RESULTADOS",bg=PANEL,fg=WHITE,font=("Segoe UI",10,"bold")).pack(side="left")
        self.count=tk.Label(rh,text="0 resultados",bg=PANEL,fg=LIGHT,font=("Segoe UI",9,"bold"));self.count.pack(side="right")
        cols=("file","line","keywords","text")
        self.tree=ttk.Treeview(rf,columns=cols,show="headings",selectmode="browse")
        for col,label,width in [("file","Arquivo",220),("line","Linha",60),("keywords","Palavra-chave",130),("text","Conteúdo da linha",520)]:
            self.tree.heading(col,text=label);self.tree.column(col,width=width,minwidth=50,anchor="w")
        ys=ttk.Scrollbar(rf,orient="vertical",command=self.tree.yview);xs=ttk.Scrollbar(rf,orient="horizontal",command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set,xscrollcommand=xs.set)
        self.tree.pack(side="left",fill="both",expand=True);ys.pack(side="right",fill="y");xs.pack(side="bottom",fill="x")
        self.tree.bind("<Double-1>",self._open_result)
        tk.Label(lf,text="LOGS EM TEMPO REAL",bg=PANEL,fg=WHITE,font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6))
        self.log_text=tk.Text(lf,height=7,bg=DARK,fg=MUTED,relief="flat",wrap="word",font=("Consolas",9),state="disabled")
        ls=ttk.Scrollbar(lf,orient="vertical",command=self.log_text.yview);self.log_text.configure(yscrollcommand=ls.set)
        self.log_text.pack(side="left",fill="both",expand=True);ls.pack(side="right",fill="y")
        for tag,color in [("INFO",LIGHT),("WARNING",YELLOW),("ERROR",RED),("SUCCESS",GREEN),("DEBUG",MUTED)]:
            self.log_text.tag_configure(tag,foreground=color)

    def _browse(self):
        path=filedialog.askdirectory(title="Selecione a pasta de busca")
        if path:self.folder.set(path);self.logger.info(f"Pasta selecionada: {path}")

    def _start(self):
        if self.running:return
        root=self.folder.get().strip();keywords=self.keywords.get().strip()
        if not root or not Path(root).is_dir():
            messagebox.showwarning("Pasta inválida","Escolha uma pasta existente para pesquisar.");return
        if not keywords:
            messagebox.showwarning("Palavra-chave ausente","Digite uma ou mais palavras-chave.");return
        # Valida regex antes de iniciar a thread.
        from search_engine import compile_keywords
        try:compile_keywords(keywords,self.case.get(),self.whole.get(),self.regex.get())
        except ValueError as exc:messagebox.showerror("Palavra-chave inválida",str(exc));return
        self.results.clear()
        for item in self.tree.get_children():self.tree.delete(item)
        self.cancel_event.clear();self.running=True;self.started_at=time.perf_counter()
        self.start_btn.configure(state="disabled");self.status.configure(text="● BUSCANDO",fg=YELLOW);self.progress.start(10)
        self.logger.info("Preparando nova busca.")
        args=(root,keywords,self.recursive.get(),self.case.get(),self.whole.get(),self.regex.get())
        self.worker=threading.Thread(target=self._worker,args=args,daemon=True);self.worker.start()

    def _worker(self,root,keywords,recursive,case,whole,regex):
        try:
            summary=search_files(root,keywords,recursive,case,whole,regex,self.cancel_event,self.logger,
                result_callback=lambda r:self.log_queue.put({"type":"result","record":r}),
                progress_callback=lambda s:self.log_queue.put({"type":"progress","stats":s}))
            self.log_queue.put({"type":"finished","summary":summary})
        except Exception as exc:
            self.logger.exception("Falha ao executar busca: %s",exc)
            self.log_queue.put({"type":"fatal","message":str(exc)})

    def _stop(self):
        if self.running:
            self.cancel_event.set();self.logger.warning("Cancelamento solicitado.")

    def _poll(self):
        try:
            while True:
                ev=self.log_queue.get_nowait()
                if "level" in ev:self._append_log(ev["level"],ev["message"])
                elif ev.get("type")=="result":
                    r=ev["record"];self.results.append(r)
                    self.tree.insert("","end",values=(r["file"],r["line"],", ".join(r["keywords"]),r["text"]))
                    self.count.configure(text=f"{len(self.results)} resultado(s)")
                elif ev.get("type")=="progress":
                    s=ev["stats"];elapsed=time.perf_counter()-self.started_at if self.started_at else 0
                    self.stats.set(f"Arquivos: {s['files_seen']}  |  Ocorrências: {s['total_hits']}  |  Tempo: {elapsed:.1f}s")
                elif ev.get("type")=="finished":self._finish(ev["summary"])
                elif ev.get("type")=="fatal":
                    self._finish(None);messagebox.showerror("Erro na busca",ev["message"])
        except queue.Empty:pass
        self.after(100,self._poll)

    def _append_log(self,level,message):
        self.log_text.configure(state="normal")
        tag=level if level in ("INFO","WARNING","ERROR","SUCCESS","DEBUG") else "INFO"
        self.log_text.insert("end",message+"\n",tag);self.log_text.see("end");self.log_text.configure(state="disabled")

    def _finish(self,s):
        self.running=False;self.progress.stop();self.start_btn.configure(state="normal");self.status.configure(text="● PRONTO",fg=GREEN)
        if s:self.stats.set(f"Arquivos: {s['files_seen']}  |  Com resultados: {s['files_with_hits']}  |  Ocorrências: {s['total_hits']}  |  Tempo: {s['elapsed']:.2f}s")

    def _open_result(self,_event=None):
        selection=self.tree.selection()
        if not selection:return
        path=Path(self.tree.item(selection[0],"values")[0])
        if path.exists():
            try:os.startfile(str(path))
            except Exception as exc:messagebox.showerror("Não foi possível abrir",str(exc))
        else:messagebox.showwarning("Arquivo não encontrado","O arquivo pode ter sido movido ou excluído.")

    def _export(self):
        if not self.results:messagebox.showinfo("Sem resultados","Execute uma busca antes de exportar.");return
        filename=filedialog.asksaveasfilename(title="Exportar resultados",defaultextension=".txt",
            filetypes=[("Texto","*.txt"),("CSV","*.csv"),("JSON","*.json")],
            initialfile=f"reysearch_resultados_{datetime.now():%Y%m%d_%H%M%S}.txt")
        if not filename:return
        path=Path(filename)
        try:
            if path.suffix.lower()==".json":path.write_text(json.dumps(self.results,ensure_ascii=False,indent=2),encoding="utf-8")
            elif path.suffix.lower()==".csv":
                with path.open("w",newline="",encoding="utf-8-sig") as f:
                    writer=csv.DictWriter(f,fieldnames=["file","name","line","keywords","text","context"]);writer.writeheader()
                    for r in self.results:writer.writerow({**r,"keywords":", ".join(r["keywords"])})
            else:
                with path.open("w",encoding="utf-8") as f:
                    f.write(f"REY SEARCH — RESULTADOS\nExportado em: {datetime.now():%Y-%m-%d %H:%M:%S}\n"+"="*90+"\n\n")
                    for r in self.results:
                        f.write(f"Arquivo: {r['file']}\nLinha: {r['line']}\nPalavras: {', '.join(r['keywords'])}\nConteúdo: {r['text']}\n"+"-"*90+"\n")
            self.logger.info(f"Resultados exportados: {path}");messagebox.showinfo("Exportação concluída",f"Arquivo salvo em:\n{path}")
        except OSError as exc:self.logger.error(f"Falha ao exportar: {exc}");messagebox.showerror("Erro na exportação",str(exc))

    def _close(self):
        if self.running and not messagebox.askyesno("Busca em andamento","Deseja cancelar a busca e sair?"):return
        self.cancel_event.set();self.destroy()
