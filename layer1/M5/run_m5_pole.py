"""
run_m5_pole.py -- rerun M5 on the pole grids, start to finish, unattended.

Every step runs with LAYER1_POLE=1 and writes its own log to m5_out/pole_run/.  Pole outputs
carry the suffix _pole (test and check-13 json too), so nothing from the R_min = 0.2 runs is
overwritten.

    1  smoke          smoke_m5.py 4                     checks 1, 1b, 2, 3 at 61x62^2
    2  coarse_T10     reach_avoid.py 101 102 10         the coarse march that sets T_RA
    3  coarse_cut     reach_avoid.py cut ... T_RA       coarse fields at T_RA (criteria 3.2)
    4  coarse_V1      reach_avoid.py 101 102 T single   coarse V_1
    5  third_game     reach_avoid.py 51 52 T            third grid, for thin / fat
    6  third_V1       reach_avoid.py 51 52 T single
    7  early_tests    test_m5.py T; converse_m5.py T    coarse and third only (a preview)
    8  fine_game      reach_avoid.py 201 204 T          the long one
    9  fine_fields    test_m5.py T fields               check 8 and the other V_RA-only checks (a preview)
   10  fine_V1        reach_avoid.py 201 204 T single   the other long one
   11  final_tests    test_m5.py T                      checks 4-12, scored on the fine grid
   12  final_check13  converse_m5.py T                  check 13, scored on the fine grid

With --parallel-fine, steps 8-10 become one step that runs both fine solves at once (each to its
own log); worth it only with cores to spare (the solver already uses several).

T is the horizon the rule picks in step 2 (6 on the old grids).  Steps 11 and 12 are the
record; 7 and 9 are previews.

RESUMING.  A finished step is listed in m5_out/pole_run/done.txt and skipped next time, so after
an interruption start this again.  A solve whose outputs are all there (json, VRA, tRA and
VRAsnap) is skipped too; a json alone does not count.  A solve that fails stops the run (later
steps need it); a test that crashes is logged and the run goes on.

Usage:  python run_m5_pole.py [--parallel-fine]     everything
        python run_m5_pole.py --list                the steps and which are done
        python run_m5_pole.py --only final_tests    rerun named steps
For testing on small grids: --coarse 26x26 --fine 51x52 --third 14x14 --skip-smoke

Disk: about 2.5 GB, mostly the fine snapshot stacks (0.9 GB each).
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'm5_out')
LOGS = os.path.join(OUT, 'pole_run')
DONE = os.path.join(LOGS, 'done.txt')
T_MARCH = 10


# ---------------------------------------------------------------------------
# Bookkeeping
# ---------------------------------------------------------------------------

def stamp():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def done_steps():
    if not os.path.exists(DONE):
        return set()
    return {ln.split()[0] for ln in open(DONE) if ln.strip()}


def mark_done(name):
    with open(DONE, 'a') as f:
        f.write('%s  %s\n' % (name, stamp()))


def solve_tag(grid, T, kind='game'):
    return '%s_T%g%s_pole' % (grid, T, '' if kind == 'game' else '_' + kind)


def solve_complete(grid, T, kind='game'):
    """Every file the checks read is there (a json copied without its snapshot stack is not enough)."""
    tag = solve_tag(grid, T, kind)
    return all(os.path.exists(os.path.join(OUT, f % tag))
               for f in ('m5_%s.json', 'VRA_%s.npy', 'tRA_%s.npy', 'VRAsnap_%s.npz'))


def horizon_from_march(grid):
    """T_RA as reach_avoid.py's horizon rule chose it from the T = 10 coarse march (None if none)."""
    return json.load(open(os.path.join(OUT, 'm5_%s.json' % solve_tag(grid, T_MARCH))))['T_RA']


# ---------------------------------------------------------------------------
# The steps
# ---------------------------------------------------------------------------

def solve_cmd(grid, T, kind='game'):
    n_R, n_phi = grid.split('x')
    return ['reach_avoid.py', n_R, n_phi, '%g' % T] + ([] if kind == 'game' else [kind])


def step(name, jobs, blocking, parallel=False):
    """jobs: list of (command, solve) with solve = (grid, T, kind) for a solve, None for a test."""
    return dict(name=name, jobs=jobs, blocking=blocking, parallel=parallel)


def steps(g, T, parallel_fine):
    """The step table.  T may be None until step 2 has run; the table is rebuilt once it is known."""
    c, f, t = g['coarse'], g['fine'], g['third']
    T = 6 if T is None else T
    if parallel_fine:
        fine = [step('fine_solves', [(solve_cmd(f, T), (f, T, 'game')),
                                     (solve_cmd(f, T, 'single'), (f, T, 'single'))], True, parallel=True)]
    else:
        fine = [step('fine_game', [(solve_cmd(f, T), (f, T, 'game'))], True),
                step('fine_fields', [(['test_m5.py', '%g' % T, 'fields'], None)], False),
                step('fine_V1', [(solve_cmd(f, T, 'single'), (f, T, 'single'))], True)]
    return ([step('smoke', [(['smoke_m5.py', '4'], None)], False),
             step('coarse_T10', [(solve_cmd(c, T_MARCH), (c, T_MARCH, 'game'))], True),
             step('coarse_cut', [(['reach_avoid.py', 'cut', solve_tag(c, T_MARCH), '%g' % T],
                                  (c, T, 'game'))], True),
             step('coarse_V1', [(solve_cmd(c, T, 'single'), (c, T, 'single'))], True),
             step('third_game', [(solve_cmd(t, T), (t, T, 'game'))], True),
             step('third_V1', [(solve_cmd(t, T, 'single'), (t, T, 'single'))], True),
             step('early_tests', [(['test_m5.py', '%g' % T], None), (['converse_m5.py', '%g' % T], None)],
                  False)]
            + fine +
            [step('final_tests', [(['test_m5.py', '%g' % T], None)], False),
             step('final_check13', [(['converse_m5.py', '%g' % T], None)], False)])


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

def child_env(g):
    env = dict(os.environ, LAYER1_POLE='1', PYTHONUNBUFFERED='1', PYTHONIOENCODING='utf-8')
    env.update(COARSE=g['coarse'], FINE=g['fine'], THIRD=g['third'])
    return env


def launch(cmd, log, env):
    head = '[%s] %s\n' % (stamp(), ' '.join(cmd))
    log.write(head)
    log.flush()
    sys.stdout.write(head)
    return subprocess.Popen([sys.executable, '-u'] + cmd, cwd=HERE, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')


def finish(p, log, t0, label=''):
    code = p.wait()
    tail = '[%s] %sexit %d after %.1f min\n' % (stamp(), label, code, (time.time() - t0) / 60)
    log.write(tail)
    log.flush()
    sys.stdout.write(tail)
    return code


def run_one(cmd, log_path, env):
    """One command, its output echoed to the console and to its log.  Returns the exit code."""
    t0 = time.time()
    with open(log_path, 'a', encoding='utf-8') as log:
        p = launch(cmd, log, env)
        for line in p.stdout:
            log.write(line)
            log.flush()
            sys.stdout.write(line)
        return finish(p, log, t0)


def run_together(cmds, log_paths, env):
    """Several commands at once, each to its own log only (on the console they would interleave)."""
    t0 = time.time()
    logs = [open(lp, 'a', encoding='utf-8') for lp in log_paths]
    procs = [launch(c, lg, env) for c, lg in zip(cmds, logs)]
    codes = [None] * len(procs)

    def pump(k):
        for line in procs[k].stdout:
            logs[k].write(line)
            logs[k].flush()
        codes[k] = finish(procs[k], logs[k], t0, label='%s: ' % ' '.join(cmds[k]))

    threads = [threading.Thread(target=pump, args=(k,)) for k in range(len(procs))]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    for lg in logs:
        lg.close()
    return codes


def run_step(i, st, env):
    """Run the jobs of one step whose solves are not already complete.  Returns their exit codes."""
    jobs = [(cmd, sv) for cmd, sv in st['jobs'] if sv is None or not solve_complete(*sv)]
    if len(jobs) < len(st['jobs']):
        print('-- %s: %d solve(s) already complete, skipped' % (st['name'], len(st['jobs']) - len(jobs)))
    if not jobs:
        return []
    base = os.path.join(LOGS, '%02d_%s' % (i, st['name']))
    print('-' * 96)
    if st['parallel'] and len(jobs) > 1:
        paths = ['%s_%s.log' % (base, solve_tag(*sv)) for _, sv in jobs]
        print('-- step %d: %s, %d at once   (logs %s)'
              % (i, st['name'], len(jobs), ', '.join(os.path.relpath(p, HERE) for p in paths)))
        return run_together([cmd for cmd, _ in jobs], paths, env)
    print('-- step %d: %s   (log %s)' % (i, st['name'], os.path.relpath(base + '.log', HERE)))
    return [run_one(cmd, base + '.log', env) for cmd, _ in jobs]


def main():
    ap = argparse.ArgumentParser(description='Rerun M5 on the pole grids.')
    ap.add_argument('--coarse', default='101x102')
    ap.add_argument('--fine', default='201x204')
    ap.add_argument('--third', default='51x52')
    ap.add_argument('--parallel-fine', action='store_true', help='run the two fine solves at once')
    ap.add_argument('--skip-smoke', action='store_true')
    ap.add_argument('--only', nargs='+', help='run just these steps (by name), even if done')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    g = dict(coarse=a.coarse, fine=a.fine, third=a.third)
    for grid in g.values():
        if int(grid.split('x')[1]) % 2:
            sys.exit('%s: the pole map needs an even n_phi' % grid)
    os.makedirs(LOGS, exist_ok=True)
    env = child_env(g)
    done = done_steps()
    T = horizon_from_march(a.coarse) if solve_complete(a.coarse, T_MARCH) else None
    names = [st['name'] for st in steps(g, T, a.parallel_fine)]
    if a.only and not set(a.only) <= set(names):
        sys.exit('unknown step(s) %s; the steps are %s' % (sorted(set(a.only) - set(names)), names))

    if a.list:
        for i, st in enumerate(steps(g, T, a.parallel_fine), 1):
            print('%2d  %-14s %-5s %s' % (i, st['name'], 'done' if st['name'] in done else '',
                                          ' ; '.join(' '.join(cmd) for cmd, _ in st['jobs'])))
        print('T_RA: %s' % ('%g' % T if T is not None else 'set by step 2'))
        return

    print('=' * 96)
    print('M5 on the pole grids   coarse %s  fine %s  third %s%s   started %s'
          % (a.coarse, a.fine, a.third, '   (fine solves in parallel)' if a.parallel_fine else '', stamp()))
    print('=' * 96)
    summary = []
    for i, name in enumerate(names, 1):
        st = steps(g, T, a.parallel_fine)[i - 1]          # rebuilt each time: T is known after step 2
        if i > 2 and T is None:
            print('!! no T_RA: step 2 has not run, or its horizon rule found none in the T = %d march.'
                  % T_MARCH)
            break
        if (a.only and name not in a.only) or (name == 'smoke' and a.skip_smoke):
            pass
        elif name in done and not a.only:
            summary.append((name, 'done earlier'))
        else:
            codes = run_step(i, st, env)
            ok = all(c == 0 for c in codes)
            summary.append((name, ('ok' if codes else 'already solved') if ok else 'FAILED (exit %s)' % codes))
            if ok:
                mark_done(name)
            elif st['blocking']:
                print('!! %s failed; the steps after it need it, so the run stops here.' % name)
                break
        if name == 'coarse_T10' and solve_complete(a.coarse, T_MARCH):
            T = horizon_from_march(a.coarse)
            print('-- T_RA = %s (horizon rule, criteria 3.2, from the T = %d coarse march)' % (T, T_MARCH))
    print('=' * 96)
    for name, state in summary:
        print('   %-14s %s' % (name, state))
    print('finished %s' % stamp())
    print('=' * 96)


if __name__ == '__main__':
    main()
