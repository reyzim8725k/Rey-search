# -*- coding: utf-8 -*-
"""Interface profissional do Rey Search."""
import csv, json, os, queue, threading, time, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from logger import configure_logger
from search_engine import search_files, compile_keywords

BG="#131225"; PANEL="#211b38"; PANEL2="#2a2246"; DARK="#0d0b18"; PURPLE="#8b5cf6"; PURPLE2="#a855f7"
LIGHT="#ddd6fe"; WHITE="#f8fafc"; MUTED="#aaa3c2"; GREEN="#34d399"; YELLOW="#fbbf24"; RED="#fb7185"; CYAN="#22d3ee"

class ReySearchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rey Search"); self.geometry("1240x820"); self.minsize(1040,700); self.configure(bg=BG)
        self.results=[]; self.log_queue=queue.Queue(); self.logger=configure_logger(self.log_queue)
        self.cancel_event=threading.Event(); self.worker=None; self.running=False; self.started_at=None
        self.logo_image=None; self._load_branding(); self._styles(); self._build(); self.after(100,self._poll)
        self.logger.info("Rey Search iniciado."); self.protocol("WM_DELETE_WINDOW",self._close)

    def _load_branding(self):
        root=Path(__file__).resolve().parent; logo=root/"assets"/"rey-search-logo-small.png"; icon=root/"assets"/"rey-search.ico"
        if icon.exists():
            try: self.iconbitmap(str(icon))
            except Exception: pass
        if logo.exists():
            try: self.logo_image=tk.PhotoImage(file=str(logo))
            except Exception: pass

    def _styles(self):
        s=ttk.Style(self)
        try: s.theme_use("clam")
        except tk.TclError: pass
        s.configure("Treeview",background=DARK,foreground=WHITE,fieldbackground=DARK,rowheight=31,borderwidth=0,font=("Segoe UI",9))
        s.configure("Treeview.Heading",background=PANEL2,foreground=LIGHT,font=("Segoe UI",9,"bold"),relief="flat",padding=7)
        s.map("Treeview",background=[("selected","#5b3aa0")],foreground=[("selected",WHITE)])
        s.configure("TProgressbar",troughcolor=DARK,background=PURPLE2,bordercolor=DARK,lightcolor=PURPLE2,darkcolor=PURPLE2)

    def _btn(self,parent,text,command,kind="primary"):
        bg={"primary":PURPLE,"subtle":"#3a2d5c","danger":"#592536"}[kind]
        return tk.Button(parent,text=text,command=command,bg=bg,fg=WHITE,activebackground="#7c3aed" if kind=="primary" else bg,activeforeground=WHITE,relief="flat",bd=0,padx=14,pady=9,font=("Segoe UI",9,"bold"),cursor="hand2")

    def _card(self,parent,title,color):
        frame=tk.Frame(parent,bg=PANEL2,padx=14,pady=10); frame.pack(side="left",fill="both",expand=True,padx=4)
        tk.Label(frame,text=title,bg=PANEL2,fg=MUTED,font=("Segoe UI",8,"bold")).pack(anchor="w")
        value=tk.Label(frame,text="0",bg=PANEL2,fg=color,font=("Segoe UI",19,"bold")); value.pack(anchor="w",pady=(3,0))
        return value

    def _build(self):
        root=tk.Frame(self,bg=BG,padx=20,pady=16); root.pack(fill="both",expand=True)
        head=tk.Frame(root,bg=BG); head.pack(fill="x",pady=(0,15))
        if self.logo_image:
            tk.Label(head,image=self.logo_image,bg=BG).pack(side="left",padx=(0,12))
        else:
            tk.Label(head,text="⌕",bg=PURPLE,fg=WHITE,font=("Segoe UI",24,"bold"),width=3,pady=3).pack(side="left",padx=(0,12))
        titles=tk.Frame(head,bg=BG); titles.pack(side="left",fill="x",expand=True)
        tk.Label(titles,text="Rey Search",bg=BG,fg=WHITE,font=("Segoe UI",24,"bold")).pack(anchor="w")
        tk.Label(titles,text="BUSCA INTELIGENTE · RÁPIDA · ORGANIZADA",bg=BG,fg=LIGHT,font=("Segoe UI",9,"bold")).pack(anchor="w")
        self.status=tk.Label(head,text="● PRONTO",bg=BG,fg=GREEN,font=("Segoe UI",10,"bold")); self.status.pack(side="right")

        cfg=tk.Frame(root,bg=PANEL,padx=16,pady=14); cfg.pack(fill="x",pady=(0,12))
        tk.Label(cfg,text="PASTA DE BUSCA",bg=PANEL,fg=LIGHT,font=("Segoe UI",9,"bold")).grid(row=0,column=0,sticky="w",pady=(0,5))
        self.folder=tk.StringVar(); self.folder_entry=tk.Entry(cfg,textvariable=self.folder,bg=DARK,fg=WHITE,insertbackground=WHITE,relief="flat",font=("Segoe UI",10)); self.folder_entry.grid(row=1,column=0,sticky="ew",ipady=9,padx=(0,8)); self._btn(cfg,"Selecionar pasta",self._browse,"subtle").grid(row=1,column=1)
        tk.Label(cfg,text="PALAVRAS-CHAVE · separe várias por vírgula",bg=PANEL,fg=LIGHT,font=("Segoe UI",9,"bold")).grid(row=2,column=0,sticky="w",pady=(13,5))
        self.keywords=tk.StringVar(); tk.Entry(cfg,textvariable=self.keywords,bg=DARK,fg=WHITE,insertbackground=WHITE,relief="flat",font=("Segoe UI",10)).grid(row=3,column=0,columnspan=2,sticky="ew",ipady=9)
        opts=tk.Frame(cfg,bg=PANEL); opts.grid(row=4,column=0,columnspan=2,sticky="w",pady=(11,0))
        self.recursive=tk.BooleanVar(value=True); self.case=tk.BooleanVar(); self.whole=tk.BooleanVar(); self.regex=tk.BooleanVar()
        for label,var in [("Buscar em subpastas",self.recursive),("Diferenciar maiúsculas",self.case),("Palavra inteira",self.whole),("Usar regex",self.regex)]:
            tk.Checkbutton(opts,text=label,variable=var,bg=PANEL,fg=MUTED,activebackground=PANEL,activeforeground=WHITE,selectcolor=DARK,font=("Segoe UI",9),relief="flat").pack(side="left",padx=(0,16))
        cfg.columnconfigure(0,weight=1)

        actions=tk.Frame(root,bg=BG); actions.pack(fill="x",pady=(0,10)); self.start_btn=self._btn(actions,"🔍  INICIAR BUSCA",self._start); self.start_btn.pack(side="left",fill="x",expand=True,ipady=5,padx=(0,8)); self.stop_btn=self._btn(actions,"⏹  PARAR",self._stop,"danger"); self.stop_btn.pack(side="left",padx=(0,8),ipady=5); self.export_btn=self._btn(actions,"💾  Exportar resultados",self._export,"subtle"); self.export_btn.pack(side="left",ipady=5)
        self.progress=ttk.Progressbar(root,mode="indeterminate"); self.progress.pack(fill="x",pady=(0,4)); self.stats=tk.StringVar(value="Pronto para pesquisar"); tk.Label(root,textvariable=self.stats,bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",pady=(0,8))
        cards=tk.Frame(root,bg=BG); cards.pack(fill="x",pady=(0,12)); self.card_files=self._card(cards,"ARQUIVOS ANALISADOS",LIGHT); self.card_hits=self._card(cards,"OCORRÊNCIAS",PURPLE2); self.card_matched=self._card(cards,"COM RESULTADOS",CYAN); self.card_errors=self._card(cards,"ERROS",RED)

        split=tk.PanedWindow(root,orient="vertical",bg=BG,bd=0,sashwidth=7,showhandle=False); split.pack(fill="both",expand=True)
        rf=tk.Frame(split,bg=PANEL,padx=11,pady=10); lf=tk.Frame(split,bg=PANEL,padx=11,pady=10); split.add(rf,minsize=190); split.add(lf,minsize=110)
        rh=tk.Frame(rf,bg=PANEL); rh.pack(fill="x",pady=(0,7)); tk.Label(rh,text="RESULTADOS DA BUSCA",bg=PANEL,fg=WHITE,font=("Segoe UI",10,"bold")).pack(side="left"); self.count=tk.Label(rh,text="0 resultados",bg=PANEL,fg=LIGHT,font=("Segoe UI",9,"bold")); self.count.pack(side="right")
        cols=("file","line","keywords","text"); self.tree=ttk.Treeview(rf,columns=cols,show="headings",selectmode="browse")
        for col,label,width in [("file","Arquivo",280),("line","Linha",65),("keywords","Palavra-chave",150),("text","Conteúdo da linha",600)]: self.tree.heading(col,text=label); self.tree.column(col,width=width,minwidth=50,anchor="w")
        ys=ttk.Scrollbar(rf,orient="vertical",command=self.tree.yview); xs=ttk.Scrollbar(rf,orient="horizontal",command=self.tree.xview); self.tree.configure(yscrollcommand=ys.set,xscrollcommand=xs.set); self.tree.pack(side="left",fill="both",expand=True); ys.pack(side="right",fill="y"); xs.pack(side="bottom",fill="x"); self.tree.bind("<Double-1>",self._open_result)
        tk.Label(lf,text="LOGS EM TEMPO REAL",bg=PANEL,fg=WHITE,font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(0,6)); self.log_text=tk.Text(lf,height=7,bg=DARK,fg=MUTED,relief="flat",wrap="word",font=("Consolas",9),state="disabled"); ls=ttk.Scrollbar(lf,orient="vertical",command=self.log_text.yview); self.log_text.configure(yscrollcommand=ls.set); self.log_text.pack(side="left",fill="both",expand=True); ls.pack(side="right",fill="y")
        for tag,color in [("INFO",LIGHT),("WARNING",YELLOW),("ERROR",RED),("SUCCESS",GREEN),("DEBUG",MUTED)]: self.log_text.tag_configure(tag,foreground=color)

    def _browse(self):
        path=filedialog.askdirectory(title="Selecione a pasta de busca")
        if path: self.folder.set(path); self.logger.info(f"Pasta selecionada: {path}")

    def _start(self):
        if self.running:return
        root=self.folder.get().strip(); keywords=self.keywords.get().strip()
        if not root or not Path(root).is_dir(): return messagebox.showwarning("Pasta inválida","Escolha uma pasta existente para pesquisar.")
        if not keywords: return messagebox.showwarning("Palavra-chave ausente","Digite uma ou mais palavras-chave.")
        try: compile_keywords(keywords,self.case.get(),self.whole.get(),self.regex.get())
        except ValueError as exc: return messagebox.showerror("Palavra-chave inválida",str(exc))
        self.results.clear()
        for item in self.tree.get_children(): self.tree.delete(item)
        for label in (self.card_files,self.card_hits,self.card_matched,self.card_errors): label.configure(text="0")
        self.cancel_event.clear(); self.running=True; self.started_at=time.perf_counter(); self.start_btn.configure(state="disabled"); self.status.configure(text="● BUSCANDO",fg=YELLOW); self.progress.start(10); self.logger.info("Preparando nova busca.")
        args=(root,keywords,self.recursive.get(),self.case.get(),self.whole.get(),self.regex.get()); self.worker=threading.Thread(target=self._worker,args=args,daemon=True); self.worker.start()

    def _worker(self,root,keywords,recursive,case,whole,regex):
        try:
            summary=search_files(root,keywords,recursive,case,whole,regex,self.cancel_event,self.logger,result_callback=lambda r:self.log_queue.put({"type":"result","record":r}),progress_callback=lambda s:self.log_queue.put({"type":"progress","stats":s})); self.log_queue.put({"type":"finished","summary":summary})
        except Exception as exc: self.logger.exception("Falha ao executar busca: %s",exc); self.log_queue.put({"type":"fatal","message":str(exc)})

    def _stop(self):
        if self.running: self.cancel_event.set(); self.logger.warning("Cancelamento solicitado.")

    def _poll(self):
        try:
            while True:
                ev=self.log_queue.get_nowait()
                if "level" in ev:self._append_log(ev["level"],ev["message"])
                elif ev.get("type")=="result":
                    r=ev["record"]; self.results.append(r); self.tree.insert("","end",values=(r["file"],r["line"],", ".join(r["keywords"]),r["text"])); self.count.configure(text=f"{len(self.results)} resultado(s)")
                elif ev.get("type")=="progress":
                    s=ev["stats"]; elapsed=time.perf_counter()-self.started_at if self.started_at else 0; self.stats.set(f"Arquivos: {s['files_seen']}  |  Ocorrências: {s['total_hits']}  |  Tempo: {elapsed:.1f}s"); self.card_files.configure(text=str(s["files_seen"])); self.card_hits.configure(text=str(s["total_hits"])); self.card_matched.configure(text=str(s["files_with_hits"]))
                elif ev.get("type")=="finished":self._finish(ev["summary"])
                elif ev.get("type")=="fatal":self._finish(None); messagebox.showerror("Erro na busca",ev["message"])
        except queue.Empty: pass
        self.after(100,self._poll)

    def _append_log(self,level,message):
        self.log_text.configure(state="normal"); tag=level if level in ("INFO","WARNING","ERROR","SUCCESS","DEBUG") else "INFO"; self.log_text.insert("end",message+"\n",tag); self.log_text.see("end"); self.log_text.configure(state="disabled")

    def _finish(self,s):
        self.running=False; self.progress.stop(); self.start_btn.configure(state="normal"); self.status.configure(text="● PRONTO",fg=GREEN)
        if s:
            self.stats.set(f"Arquivos: {s['files_seen']}  |  Com resultados: {s['files_with_hits']}  |  Ocorrências: {s['total_hits']}  |  Tempo: {s['elapsed']:.2f}s"); self.card_files.configure(text=str(s["files_seen"])); self.card_hits.configure(text=str(s["total_hits"])); self.card_matched.configure(text=str(s["files_with_hits"])); self.card_errors.configure(text=str(s["errors"]))

    def _open_result(self,_event=None):
        selection=self.tree.selection()
        if not selection:return
        path=Path(self.tree.item(selection[0],"values")[0])
        if path.exists():
            try: os.startfile(str(path))
            except Exception as exc: messagebox.showerror("Não foi possível abrir",str(exc))
        else: messagebox.showwarning("Arquivo não encontrado","O arquivo pode ter sido movido ou excluído.")

    def _export(self):
        if not self.results:return messagebox.showinfo("Sem resultados","Execute uma busca antes de exportar.")
        filename=filedialog.asksaveasfilename(title="Exportar resultados",defaultextension=".txt",filetypes=[("Texto","*.txt"),("CSV","*.csv"),("JSON","*.json")],initialfile=f"reysearch_resultados_{datetime.now():%Y%m%d_%H%M%S}.txt")
        if not filename:return
        path=Path(filename)
        try:
            if path.suffix.lower()==".json":path.write_text(json.dumps(self.results,ensure_ascii=False,indent=2),encoding="utf-8")
            elif path.suffix.lower()==".csv":
                with path.open("w",newline="",encoding="utf-8-sig") as f:
                    writer=csv.DictWriter(f,fieldnames=["file","name","line","keywords","text","context"]); writer.writeheader(); [writer.writerow({**r,"keywords":", ".join(r["keywords"])}) for r in self.results]
            else:
                with path.open("w",encoding="utf-8") as f:
                    f.write(f"REY SEARCH — RESULTADOS\nExportado em: {datetime.now():%Y-%m-%d %H:%M:%S}\n"+"="*90+"\n\n"); [f.write(f"Arquivo: {r['file']}\nLinha: {r['line']}\nPalavras: {', '.join(r['keywords'])}\nConteúdo: {r['text']}\n"+"-"*90+"\n") for r in self.results]
            self.logger.info(f"Resultados exportados: {path}"); messagebox.showinfo("Exportação concluída",f"Arquivo salvo em:\n{path}")
        except OSError as exc:self.logger.error(f"Falha ao exportar: {exc}"); messagebox.showerror("Erro na exportação",str(exc))

    def _close(self):
        if self.running and not messagebox.askyesno("Busca em andamento","Deseja cancelar a busca e sair?"):return
        self.cancel_event.set(); self.destroy()
