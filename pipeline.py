#!/usr/bin/env python3
"""Pipeline: coleta → chunk → embed → salvar datasets PT."""

import argparse, json, sys
from pathlib import Path

def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200) -> list:
    """Divide texto em trechos com overlap."""
    if not text or len(text) < chunk_size // 2:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks

def do_chunk(args):
    """raw JSONL → chunks JSONL."""
    inp, out = Path(args.input), Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    cs, ov = args.chunk_size or 1800, args.overlap or 200
    total_docs = total_chunks = 0
    with open(inp, encoding='utf-8') as inf, open(out, 'w', encoding='utf-8') as outf:
        for line in inf:
            if not line.strip(): continue
            doc = json.loads(line)
            total_docs += 1
            texto = doc.get('texto', doc.get('text', ''))
            chunks = chunk_text(texto, cs, ov)
            for seq, chunk in enumerate(chunks):
                outf.write(json.dumps({
                    'doc_id': doc.get('id', f'doc_{total_docs}'),
                    'chunk_seq': seq, 'text': chunk,
                    'titulo': doc.get('titulo', ''), 'tipo': doc.get('tipo', '')
                }, ensure_ascii=False) + '\n')
                total_chunks += 1
    print(f"✅ {total_docs} docs → {total_chunks} chunks")

def do_full(args):
    """full: raw → chunks."""
    ds = Path(args.dataset)
    raw = ds / 'raw'
    proc = ds / 'processed'
    proc.mkdir(parents=True, exist_ok=True)
    print(f"📂 {ds}")
    for rf in sorted(raw.glob('*.jsonl')):
        cf = proc / f'{rf.stem}.chunks.jsonl'
        c = type('Args', (), {'input': str(rf), 'output': str(cf), 
                  'chunk_size': 1800, 'overlap': 200})()
        do_chunk(c)
    print(f"✅ Pronto pra commit!")

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest='cmd', required=True)
c = sub.add_parser('chunk')
c.add_argument('--input', required=True)
c.add_argument('--output', required=True)
c.add_argument('--chunk-size', type=int, default=1800)
c.add_argument('--overlap', type=int, default=200)
f = sub.add_parser('full')
f.add_argument('--dataset', required=True)
args = ap.parse_args()
if args.cmd == 'chunk': do_chunk(args)
elif args.cmd == 'full': do_full(args)
