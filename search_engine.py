# -*- coding: utf-8 -*-
"""Motor de busca incremental em arquivos TXT."""
import os
import re
import time
from pathlib import Path

class SearchCancelled(Exception):
    pass

def compile_keywords(raw, case_sensitive=False, whole_word=False, use_regex=False):
    words = [w.strip() for w in raw.split(",") if w.strip()]
    if not words:
        raise ValueError("Informe pelo menos uma palavra-chave.")
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = []
    for word in words:
        pattern = word if use_regex else re.escape(word)
        if whole_word:
            pattern = rf"\b(?:{pattern})\b"
        try:
            compiled.append((word, re.compile(pattern, flags)))
        except re.error as exc:
            raise ValueError(f"Regex inválida em '{word}': {exc}") from exc
    return compiled

def iter_txt_files(root, recursive, cancel_event):
    root = Path(root)
    if recursive:
        for current, dirs, names in os.walk(root):
            if cancel_event.is_set():
                raise SearchCancelled()
            dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
            for name in names:
                if name.lower().endswith(".txt"):
                    yield Path(current) / name
    else:
        with os.scandir(root) as entries:
            for entry in entries:
                if cancel_event.is_set():
                    raise SearchCancelled()
                if entry.is_file() and entry.name.lower().endswith(".txt"):
                    yield Path(entry.path)

def search_files(root, raw_keywords, recursive=True, case_sensitive=False,
                 whole_word=False, use_regex=False, cancel_event=None, logger=None,
                 result_callback=None, progress_callback=None):
    import threading
    cancel_event = cancel_event or threading.Event()
    started = time.perf_counter()
    patterns = compile_keywords(raw_keywords, case_sensitive, whole_word, use_regex)
    seen = hit_files = total_hits = errors = 0

    def log(level, msg):
        if logger:
            getattr(logger, level)(msg)

    log("info", f"Iniciando busca em: {root}")
    log("info", "Palavras-chave: " + ", ".join(k for k, _ in patterns))
    cancelled = False
    try:
        for path in iter_txt_files(root, recursive, cancel_event):
            if cancel_event.is_set():
                raise SearchCancelled()
            seen += 1
            per_file = 0
            try:
                # Tenta UTF-8; em caso de erro reabre em Latin-1.
                try:
                    f = path.open("r", encoding="utf-8-sig", errors="strict", newline="")
                    f.read(65536)
                    f.seek(0)
                except UnicodeDecodeError:
                    try: f.close()
                    except Exception: pass
                    log("warning", f"UTF-8 inválido; usando Latin-1: {path}")
                    f = path.open("r", encoding="latin-1", errors="replace", newline="")
                with f:
                    for line_no, line in enumerate(f, 1):
                        if cancel_event.is_set():
                            raise SearchCancelled()
                        matched = [word for word, pattern in patterns if pattern.search(line)]
                        if matched:
                            per_file += len(matched)
                            total_hits += len(matched)
                            record = {"file": str(path), "name": path.name, "line": line_no,
                                      "keywords": matched, "text": line.rstrip("\r\n")[:20000],
                                      "context": line.strip()[:240]}
                            if result_callback:
                                result_callback(record)
                if per_file:
                    hit_files += 1
                    log("success", f"{path.name}: {per_file} ocorrência(s)")
                if progress_callback:
                    progress_callback({"files_seen": seen, "files_with_hits": hit_files,
                                       "total_hits": total_hits, "current": str(path)})
            except SearchCancelled:
                raise
            except (OSError, UnicodeError, PermissionError) as exc:
                errors += 1
                log("error", f"Não foi possível ler {path}: {exc}")
            except Exception as exc:
                errors += 1
                log("error", f"Erro inesperado em {path}: {exc}")
    except SearchCancelled:
        cancelled = True
        log("warning", "Busca cancelada pelo usuário.")
    elapsed = time.perf_counter() - started
    summary = {"files_seen": seen, "files_with_hits": hit_files, "total_hits": total_hits,
               "errors": errors, "elapsed": elapsed, "cancelled": cancelled}
    log("warning" if cancelled else "success",
        f"Busca {'cancelada' if cancelled else 'concluída'} — {seen} arquivo(s), "
        f"{hit_files} com resultados, {total_hits} ocorrência(s), {errors} erro(s), {elapsed:.2f}s.")
    return summary
