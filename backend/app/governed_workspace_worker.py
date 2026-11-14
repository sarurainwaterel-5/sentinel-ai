"""Explicit supervised bounded governed outbox worker; no provider calls."""
import argparse
import json
import os
import signal
import threading
import time

from app.governed_workspace_application import load_configuration,build_runtime


def run_worker(runtime,*,stop=None,clock=time.monotonic,once=False):
    stop=stop or threading.Event()
    settings=runtime.config.worker
    deadline=clock()+settings.max_seconds
    completed=errors=consecutive=0
    while not stop.is_set() and clock()<deadline and completed<settings.max_operations:
        remaining=deadline-clock()
        if remaining<=0:break
        try:
            result=runtime.reconciler.reconcile_once(timeout_seconds=min(3600,remaining),lease_seconds=settings.lease_seconds)
            if result is not None:completed+=1
            consecutive=0
        except Exception:
            # Never leak credentials, source bytes, DSNs or provider exceptions.
            errors+=1;consecutive+=1
            if consecutive>=5:return dict(status='blocked',completed_operations=completed,denied_operations=errors,production_enabled=False,provider_calls=0)
            result=None
        if once:break
        if result is None:stop.wait(min(settings.poll_seconds,max(0,deadline-clock())))
    return dict(status='stopped' if stop.is_set() else 'bounded_complete',completed_operations=completed,denied_operations=errors,production_enabled=False,provider_calls=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=os.environ.get('SENTINEL_GOVERNED_CONFIG'))
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    if not args.config:parser.error('Explicit --config or SENTINEL_GOVERNED_CONFIG required.')
    runtime=None
    try:
        runtime=build_runtime(load_configuration(args.config))
        stop=threading.Event()
        for signum in (signal.SIGINT,signal.SIGTERM):signal.signal(signum,lambda *_:stop.set())
        report=run_worker(runtime,stop=stop,once=args.once)
        print(json.dumps(report,sort_keys=True))
        return 2 if report['status']=='blocked' else 0
    except Exception:
        print(json.dumps(dict(status='startup_or_worker_failed',production_enabled=False,provider_calls=0)))
        return 2
    finally:
        if runtime is not None:runtime.close()


if __name__=='__main__':raise SystemExit(main())
