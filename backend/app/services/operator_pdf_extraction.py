"""Bounded, resumable embedded-text PDF extraction for explicit operator intake.

No OCR, catalog mutation, semantic approval, or ordinary upload-policy changes.
Run: python -m app.services.operator_pdf_extraction SOURCE PRIVATE_DIRECTORY
"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import tempfile

MAX_SOURCE = 1024**3
MAX_PAGE = 256*1024
MAX_TEXT = 8*1024**2
MAX_PAGES = 10000
BATCH = 16
TIMEOUT = 60


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def _private(path):
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
        raise ValueError('private_directory_required')


def _write(path,data):
    fd,name=tempfile.mkstemp(dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(name,path)
        directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(name): os.unlink(name)


def _read(path,limit):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>limit:
            raise ValueError('invalid_file_bound')
        value=stream.read(limit+1)
        if len(value)>limit: raise ValueError('file_bound_exceeded')
        return value


def _limits():
    resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_PAGE,MAX_PAGE))
    resource.setrlimit(resource.RLIMIT_CPU,(TIMEOUT,TIMEOUT))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def _run(source,directory,start,stop):
    subprocess.run([sys.executable,'-m','app.services.operator_pdf_extraction','--worker',str(source),str(directory),str(start),str(stop)],
                   check=True,timeout=TIMEOUT,stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,preexec_fn=_limits)


def extract(source,directory):
    source=Path(source).absolute(); directory=Path(directory).absolute()
    _private(directory)
    original=_read(source,MAX_SOURCE)
    if not original or not original.startswith(b'%PDF-'): raise ValueError('pdf_required')
    source_hash=_sha(original); length=len(original)
    policy={'version':'sentinel-operator-pdf-embedded-v1',
            'implementation_sha256':_sha(Path(__file__).read_bytes()),
            'pypdf_version':importlib.metadata.version('pypdf'),
            'batch_pages':BATCH,'batch_timeout_seconds':TIMEOUT,
            'max_page_utf8_bytes':MAX_PAGE,'max_text_utf8_bytes':MAX_TEXT,
            'max_source_bytes':MAX_SOURCE,'max_pages':MAX_PAGES,
            'separator_utf8_hex':'0a0a','ocr':False}
    binding={'source_sha256':source_hash,'byte_length':length,'policy':policy,
             'extraction_policy_sha256':_sha(_json(policy))}
    bindfile=directory/'binding.json'
    if bindfile.exists():
        if _read(bindfile,65536)!=_json(binding): raise ValueError('checkpoint_binding_changed')
    else:
        if any(directory.iterdir()): raise ValueError('unbound_checkpoint_directory_not_empty')
        _write(bindfile,_json(binding))
    snapshot=directory/'source.pdf'
    if snapshot.exists():
        if _sha(_read(snapshot,MAX_SOURCE))!=source_hash: raise ValueError('snapshot_changed')
    else: _write(snapshot,original)
    del original
    with tempfile.TemporaryDirectory(dir=directory) as temp:
        work=Path(temp)
        _run(snapshot,work,-1,-1)
        count=int(_read(work/'count',32))
    if not 0<count<=MAX_PAGES: raise ValueError('page_count_exceeded')
    rows=[]; texts=[]; total=0
    for start in range(0,count,BATCH):
        stop=min(start+BATCH,count)
        missing=[]
        for index in range(start,stop):
            page=directory/f'page-{index:05d}.json'
            if not page.exists(): missing.append(index)
        if missing:
            with tempfile.TemporaryDirectory(dir=directory) as temp:
                work=Path(temp); _run(snapshot,work,start,stop)
                for index in missing:
                    raw=_read(work/f'{index}.txt',MAX_PAGE); raw.decode('utf-8',errors='strict')
                    _write(directory/f'page-{index:05d}.json',_json({'page':index,'source_sha256':source_hash,
                        'extraction_policy_sha256':binding['extraction_policy_sha256'],
                        'text':raw.decode(),'byte_length':len(raw),'sha256':_sha(raw)}))
        for index in range(start,stop):
            row=json.loads(_read(directory/f'page-{index:05d}.json',MAX_PAGE*7))
            raw=row['text'].encode('utf-8')
            if (row['page']!=index or row['source_sha256']!=source_hash
                    or row['extraction_policy_sha256']!=binding['extraction_policy_sha256']
                    or row['byte_length']!=len(raw) or row['sha256']!=_sha(raw) or len(raw)>MAX_PAGE):
                raise ValueError('page_checkpoint_invalid')
            total+=len(raw)+(2 if index else 0)
            if total>MAX_TEXT: raise ValueError('aggregate_text_exceeded')
            texts.append(raw); rows.append({k:row[k] for k in ('page','byte_length','sha256')})
    if (_sha(_read(source,MAX_SOURCE))!=source_hash
            or _sha(_read(snapshot,MAX_SOURCE))!=source_hash): raise ValueError('source_changed')
    text=b'\n\n'.join(texts)
    manifest={**binding,'status':'complete','page_count':count,'pages':rows,
              'text_sha256':_sha(text),'text_byte_length':len(text),
              'limitation':'Embedded text only; no OCR or transcription/semantic acceptance.'}
    _write(directory/'text.txt',text)
    _write(directory/'manifest.complete.json',_json(manifest))
    return manifest


def _worker(source,directory,start,stop):
    from pypdf import PdfReader
    # Parent validates original identity before and after the entire extraction.
    with open(source,'rb') as stream:
        reader=PdfReader(stream)
        if reader.is_encrypted: raise ValueError('encrypted_pdf')
        count=len(reader.pages)
        if not 0<count<=MAX_PAGES: raise ValueError('page_count_exceeded')
        if start==-1:
            (directory/'count').write_text(str(count)); return
        for index in range(start,stop):
            raw=(reader.pages[index].extract_text() or '').encode('utf-8')
            if len(raw)>MAX_PAGE: raise ValueError('page_text_exceeded')
            (directory/f'{index}.txt').write_bytes(raw)


if __name__=='__main__':
    if len(sys.argv)==6 and sys.argv[1]=='--worker':
        _worker(Path(sys.argv[2]),Path(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]))
    elif len(sys.argv)==3:
        result=extract(sys.argv[1],sys.argv[2])
        print(json.dumps({k:result[k] for k in ('status','page_count','text_sha256','text_byte_length','extraction_policy_sha256')}))
    else: raise SystemExit('usage: operator_pdf_extraction SOURCE PRIVATE_DIRECTORY')
