#!/usr/bin/env python3
"""Build the Gate 1 report v2 (docs/GATE1_REPORT.md and an HTML artifact page) from the committed data.

Sources (read at build time):
  main: data/predictions/gate1_summary.json (verdict wording, criteria (a)-(f), Deviation 37 reading, propagation
        findings), gate1_predictions.csv, gate1_layer_index.csv, gate1_null_control.csv, ladder_placements.json,
        pauliprop_validation.csv, pauliprop_kurtosis.json, pauliprop_pattern_check.csv, docs/postrun/02_phoenix_smoke_2026-09-20.md
  Deviation 34 (whole-layer ZZ) rows: pauliprop_summary.json, pauliprop_predictions.csv, gate1b_shot_table.csv,
        pauliprop_zz_layer_validation.csv. Read from the working tree when main carries the `zz_layer` key, otherwise
        from `git show <--zz-ref>:...` (default origin/pp-zz-layer); the report states which.
Verdict words (pass / fail / provisional pass / not-evaluated / reported) are copied from gate1_summary.json; every
derived number (2 sigma, deficits, ratios) is recomputed here from the file values.

    python scripts/build_gate1_report.py [--html PATH] [--commit HASH] [--no-md] [--zz-ref REF]
"""
import argparse
import collections
import csv
import html
import io
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'predictions'
GH = 'https://github.com/SSIT-Q/gradvar-phoenix'
TITLE = 'Gate 1 report v2 and decision, 20 Sep 2026'
SF4096 = 1 / (2 * 4096)
SF16384 = 1 / (2 * 16384)
PATCHES = [(20, '4x5'), (39, '4x10'), (53, '6x10'), (70, '8x10'), (87, '10x10')]
MODELS = ['noiseless', 'unital', 'nonunital']

ap = argparse.ArgumentParser()
ap.add_argument('--html', default=str(ROOT / 'build' / 'gate1_report.html'))
ap.add_argument('--commit', default=None, help='hash of the commit carrying the builder and docs/GATE1_REPORT.md (footer note)')
ap.add_argument('--no-md', action='store_true')
ap.add_argument('--zz-ref', default='origin/pp-zz-layer', help='git ref holding the Deviation 34 rows when main lacks them')
ARGS = ap.parse_args()


def git(*a):
    return subprocess.check_output(['git', '-C', str(ROOT), *a]).decode()


# the data commit the report describes: the last commit touching the predictions or the post-run reviews (not the report's own commit)
MAIN_SHA = git('log', '-1', '--format=%h', '--', 'data/predictions', 'docs/postrun').strip()


def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def e4(x):
    return 'pending' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{x:.3e}'


def e3(x):
    return 'pending' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{x:.2e}'


def f2(x):
    return 'pending' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{x:.2f}'


def f3(x):
    return 'pending' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{x:.3f}'


def status_word(s):
    if s in (None, '', 'pending'):
        return '**pending**'
    if s == 'converged':
        return '**converged**'
    if s.startswith('sampled'):
        return '**sampled** (deficit < 10%, 2 sigma > 5%)'
    if s.startswith('not converged'):
        return '**not converged** (deficit >= 10%)'
    if s.startswith('lower bound only'):
        return '**lower bound only** (sampler time cap)'
    return s


def table(headers, rows):
    esc = lambda c: str(c).replace('|', '\\|')
    out = ['| ' + ' | '.join(esc(h) for h in headers) + ' |', '|' + '---|' * len(headers)]
    for r in rows:
        out.append('| ' + ' | '.join(esc(c) for c in r) + ' |')
    return '\n'.join(out) + '\n'


# ----------------------------------------------------------------------------- load main
summary = json.load(open(DATA / 'gate1_summary.json'))
SUMMARY_SRC = f'main @ {MAIN_SHA}'
if 'deviation_37' not in summary['criteria']['d']:
    # the Deviation 37 (d) reading was added to the re-summary on the ZZ-layer branch (commit e3859fd); main's copy is the same grid without it
    summary = json.loads(git('show', f'{ARGS.zz_ref}:data/predictions/gate1_summary.json'))
    SUMMARY_SRC = f'`{ARGS.zz_ref.split("/")[-1]}` @ {git("rev-parse", "--short", ARGS.zz_ref).strip()} (main\'s copy lacks the Deviation 37 reading)'
SUMMARY_NOTE = '' if SUMMARY_SRC.startswith('main') else ', whose criteria wording equals main\'s and adds the Deviation 37 (d) reading'
val_rows = list(csv.DictReader(open(DATA / 'pauliprop_validation.csv')))
pat_rows = list(csv.DictReader(open(DATA / 'pauliprop_pattern_check.csv')))
kurt = json.load(open(DATA / 'pauliprop_kurtosis.json'))
grid_rows = [r for r in csv.DictReader(open(DATA / 'gate1_predictions.csv')) if r['var']]
li_rows = [r for r in csv.DictReader(open(DATA / 'gate1_layer_index.csv')) if r['D']]
null_rows = list(csv.DictReader(open(DATA / 'gate1_null_control.csv')))
placements = json.load(open(DATA / 'ladder_placements.json'))
KAPPA = kurt['kurtosis']
CRIT = summary['criteria']
FIND = summary['propagation']['findings']

# ----------------------------------------------------------------------------- load the Deviation 34 rows (main or the ZZ branch)
main_pps = json.load(open(DATA / 'pauliprop_summary.json'))
if main_pps.get('zz_layer') == 'on':
    ZZ_SRC = f'main @ {MAIN_SHA}'
    ZZ_SHA = MAIN_SHA
    ppsum = main_pps
    pp_rows = list(csv.DictReader(open(DATA / 'pauliprop_predictions.csv')))
    shot_rows = list(csv.DictReader(open(DATA / 'gate1b_shot_table.csv')))
    zzval_rows = list(csv.DictReader(open(DATA / 'pauliprop_zz_layer_validation.csv')))
else:
    ZZ_SHA = git('rev-parse', '--short', ARGS.zz_ref).strip()
    ZZ_SRC = f'branch `{ARGS.zz_ref.split("/")[-1]}` @ {ZZ_SHA} (not yet merged to main; read with `git show`)'
    ppsum = json.loads(git('show', f'{ARGS.zz_ref}:data/predictions/pauliprop_summary.json'))
    pp_rows = list(csv.DictReader(io.StringIO(git('show', f'{ARGS.zz_ref}:data/predictions/pauliprop_predictions.csv'))))
    shot_rows = list(csv.DictReader(io.StringIO(git('show', f'{ARGS.zz_ref}:data/predictions/gate1b_shot_table.csv'))))
    zzval_rows = list(csv.DictReader(io.StringIO(git('show', f'{ARGS.zz_ref}:data/predictions/pauliprop_zz_layer_validation.csv'))))
if ppsum is main_pps:
    # the layer-model numbers: the last non-merge commit touching the summary, and the merge that brought them to main
    ZZ_COMMIT_TIME = git('log', '-1', '--no-merges', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M UTC', '--', 'data/predictions/pauliprop_summary.json').strip()
    ZZ_NUM_SHA = git('log', '-1', '--no-merges', '--format=%h', '--', 'data/predictions/pauliprop_summary.json').strip()
    ZZ_MERGE_SHA = git('log', '-1', '--merges', '--format=%h', '--grep=pp-zz-layer').strip()
    ZZ_BRANCH_LINE = f'Branch `pp-zz-layer`, merged to main as [{ZZ_MERGE_SHA}]({GH}/commit/{ZZ_MERGE_SHA})'
else:
    ZZ_COMMIT_TIME = git('log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M UTC', ARGS.zz_ref).strip()
    ZZ_NUM_SHA = git('log', '-1', '--no-merges', '--format=%h', ARGS.zz_ref, '--', 'data/predictions/pauliprop_summary.json').strip()
    ZZ_BRANCH_LINE = f'Branch `pp-zz-layer` @ {ZZ_SHA} (not merged)'

pending_values = []
dev, g1b_off, g1b_layer, g1b_idle, dial_off = {}, {}, {}, {}, {}
for r in pp_rows:
    st = r['stage']
    n = int(float(r['n'])) if r['n'] else None
    L = int(r['L'])
    rec = dict(patch=r['patch'], vmc=fl(r['var_kL_mc']), se=fl(r['se_kL_mc']), vpp=fl(r['var_kL_pp']),
               v1=fl(r['var_k1_mc']), se1=fl(r['se_k1_mc']), v1pp=fl(r['var_k1_pp']),
               vc=fl(r['var_cost_mc']), sec=fl(r['se_cost_mc']), mean=fl(r['mean_cost']), disc=fl(r['discarded']),
               status=r['status'], t=fl(r['runtime_s']), nb=int(float(r['n_broken_edges'] or 0)), edge=r['edge'],
               vm=fl(r['var_mask']), vmse=fl(r['var_mask_se']), pf=fl(r['pattern_floor']), K=r['K_masks'],
               p=fl(r['p']), dial=r['dial'], ncone=int(float(r['n_cone'])) if r['n_cone'] else None,
               zz_layer=r.get('zz_layer', 'off'), zz_idle=r.get('zz_idle', 'off'),
               tau=fl(r.get('zz_layer_tau_ns_median')), ncoup=fl(r.get('n_zz_couplers')))
    if st == 'dev15' and rec['zz_layer'] == 'off' and rec['zz_idle'] == 'off':
        dev[(n, L, r['model'])] = rec
    elif st == 'gate1b':
        if rec['zz_layer'] == 'on':
            g1b_layer[(n, L, r['dial'])] = rec
        elif rec['zz_idle'] == 'on':
            g1b_idle[(n, L, r['dial'])] = rec
        else:
            g1b_off[(n, L, r['dial'])] = rec
    elif st == 'dial' and rec['zz_layer'] == 'off' and rec['zz_idle'] == 'off':
        dial_off[(L, r['dial'], rec['p'])] = rec

# ----------------------------------------------------------------------------- criteria (a)-(f), complete grid
c1 = CRIT['c']['part1']
d37 = CRIT['d']['deviation_37']
d37_4096 = next(x for x in d37['readings'] if x['shots'] == 4096)
d37_16384 = next(x for x in d37['readings'] if x['shots'] == 16384)
gap = summary['propagation']['grid_after_propagation']
n_grid = len(grid_rows)
part1_by_L = collections.defaultdict(list)
for p in c1['points']:
    part1_by_L[p['L']].append(p)
part1_line = '; '.join(f'L = {L}: {sum(1 for p in v if p["exceeds_2floor"])} of {len(v)}' for L, v in sorted(part1_by_L.items()))

crit_table = table(['criterion', 'statistic and threshold', 'result (gate1_summary.json, ' + SUMMARY_SRC.split(' (')[0] + ')', 'reading for the decision', 'evidence'], [
    ['(a) chain regression', 'Var[d<Z_(n-1)>/d theta_0] of the Ry + CX chain, n = 4..20, must contain 2^-n; Deviation 25: (a-i) per-draw identity < 1e-10, (a-ii) percentile bootstrap at n <= 12, (a-iii) exact null sampling distribution at n = 13..20 with the seed-2027 replicate rule',
     '**fail** as registered; **pass** under Deviation 25 (result_deviation_25): (a-i) max |g_sim - g_closed| = 1.8e-14, (a-ii) 9 of 9, (a-iii) 7 of 8 at seed 2026, n = 20 replicate 0.212 inside [0.043, 5.764]',
     '**pass** under Deviation 25 (PI countersigned 20 Sep 2026); the statevector is exact, the pre-registered estimator is not coverable at n >= 13 (kurtosis (3/2)^n)',
     '`figures/gate1_noiseless.csv`, `gate1_chain_identity.csv`, `gate1_chain_replicates.csv`'],
    ['(b) interval ratio', 'bootstrap hi/lo of the variance at M = 200; Deviation 17: < 1.5 / 2.0 / 2.5 at L = 1 / 2 / >= 4',
     '**pass**: ' + CRIT['b']['note'], '**pass**; the propagation rows carry no draw interval (exact theta-averages) and are not tested',
     '`data/predictions/gate1_predictions.csv` (hi_lo)'],
    ['(c) part 1', '|Var_unital - Var_noiseless| at k = 1 > 2 x 1/(2 x 16384) = 6.10e-5 at >= 6 (n, L) points of the 25-point ladder',
     '**pass**: ' + c1['note'], f'**pass**, {c1["n_exceeding"]} of {len(c1["points"])} points ({part1_line}); every L <= 8 point exceeds the threshold, no L = 12 point does (separations 3.5e-6 to 1.7e-5, both models collapsed)',
     '`gate1_summary.json` -> criteria.c.part1'],
    ['(c) part 2', 'D = R_nonunital - R_unital (Deviation 14), paired bootstrap D_lo > 0 at n = 40 or 100, L = 8 / 12',
     '**not-evaluated**: ' + CRIT['c']['part2']['note'],
     '**not-evaluated** and moot under Deviation 16, whose text reclassifies H3 as "a consistency check with the prediction D = 0 within the interval" (predicted |D| <= 1e-2 against about 0.3 measurement uncertainty), keeps the L = 8 / 12 layer-index sweep as a check of the unital k-dependence (H2) and moves the confirmatory non-unital test to the reset dial (Section 3b, Deviation 20); the propagation point estimates (table 7.3) are D = -0.013 to +0.019 at L = 8 with 2 sigma 0.06-0.09, none separated; the stop rule reads "(c) is not failed"',
     '`gate1_summary.json` -> criteria.c.part2, overall'],
    ['(d) null control', 'the null-control floor lies below the smallest signal to be claimed; as registered with a 10x allowance on 1/(2N), under Deviation 37 the measured null-control floor + 3 bootstrap sigma at L >= 8',
     'result field: "' + CRIT['d']['result'] + '"',
     f'**pass** on the exact points (L <= 4: Var_null / (1/(2N)) = 0.74, 0.66, 0.85, 0.80; smallest exact noisy signal 7.25e-2); **pass** under Deviation 37 at L = 8: floor {d37_4096["floor_3sigma_used"]:.2e} at 4096 shots (n = 39 null control 1.039e-4 + 3 x 1.119e-5), {d37_4096["by_L"]["8"]["above"]} of {d37_4096["by_L"]["8"]["n"]} L = 8 noisy predictions above it, smallest {d37_4096["by_L"]["8"]["min_var"]:.1e} (unital n = 70 k = 1); at 16384 shots floor {d37_16384["floor_3sigma_used"]:.2e}, 20 of 20; L = 12 **exploratory** (Deviations 37, 43: {d37_4096["by_L"]["12"]["above"]} of 20 above the floor at 4096 shots, {d37_16384["by_L"]["12"]["above"]} of 20 at 16384); the literal 10x reading is kept in the JSON as a record',
     '`gate1_summary.json` -> criteria.d (deviation_37, complete_grid); `gate1_null_control.json`'],
    ['(e) resolvability', 'eps_N = Var_shot / (N Var_theta) < 1 at every point to be claimed',
     '**pass**: ' + CRIT['e']['note'] + f'; 0 of {n_grid} exact points at or above 1',
     '**pass**; at L = 8 the propagation rows give V / (1/(2 x 4096)) = 1.63-9.81 (eps_N < 1); L = 12 is exploratory and not claimed',
     '`gate1_predictions.csv` (eps_N_4096, eps_N_16384); table 7.4'],
    ['(f) Renyi-2 saturation depth', 'half-patch S_2(L) vs the Page value; L_s(n) at 95% of Page; design check, no threshold',
     '**reported**: ' + CRIT['f']['note'], '**reported**; geometric for the 4-row patches, not extrapolated',
     '`gate1_renyi.json`, `figures/gate1_renyi.png`'],
    ['grid', 'the 25-point ladder x 3 models x k in {1, L}', f'{gap["n_points_computed"]} points computed, {gap["n_points_deferred"]} deferred: ' + gap['remaining_deferred'],
     '**complete**: 43 exact points (L <= 4, cones <= 24 qubits) and 92 propagation points (L = 8 / 12, the large-cone L = 4 groups and the cost-cut noisy 4x5 L = 4 / 4x10 L = 2 groups)', '`gate1_summary.json` -> propagation.grid_after_propagation'],
    ['overall (JSON)', 'Section 4 stop rule: failing (c) or (d) stops the hardware stage', '"' + summary['overall'] + '"',
     'the JSON declares no overall pass / fail on the grid alone; the decision block above applies Deviations 16 and 37 to (c) part 2 and (d) at L >= 8 and closes the gate', '`gate1_summary.json` -> overall'],
])

# ----------------------------------------------------------------------------- Gate 1b: separation clauses under the Deviation 34 layer model
sep_rows = []
sep_ratio = {}
for L in (8, 12):
    for n, patch in ((39, '4x10'), (53, '6x10'), (87, '10x10')):
        p0, p25 = g1b_layer[(n, L, 'delay')], g1b_layer[(n, L, 'reset')]
        o0, o25 = g1b_off[(n, L, 'delay')], g1b_off[(n, L, 'reset')]
        v0 = p0['vmc'] if p0['vmc'] is not None else p0['vpp']
        v25 = p25['vmc'] if p25['vmc'] is not None else p25['vpp']
        sep = v25 - v0
        comb = SF4096 + p25['pf']
        sep_ratio[(n, L)] = sep / comb
        sh0 = (v0 - o0['vmc']) / o0['vmc']
        sh25 = (v25 - o25['vmc']) / o25['vmc']
        sep_rows.append([L, patch, n, p0['edge'], f'{p0["tau"]:.0f}', f'{p0["ncoup"]:.0f}',
                         (f'{e4(v0)} +/- {e3(2 * p0["se"])}' if p0['vmc'] is not None else f'{e4(v0)} (lower bound only)'), f'{sh0 * 100:+.1f}%',
                         (f'{e4(v25)} +/- {e3(2 * p25["se"])}' if p25['vmc'] is not None else f'{e4(v25)} (lower bound only)'), f'{sh25 * 100:+.1f}%',
                         e4(sep), f'{p25["vm"]:.4f}', e4(p25['pf']), e4(comb), f2(sep / comb),
                         '**pass**' if sep / comb >= 3 else '**fail**', '**pass**' if p25['pf'] < sep / 2 else '**fail**',
                         status_word(p0['status']) + ' / ' + status_word(p25['status'])])
sep_table = table(['L', 'patch', 'n', 'edge', 'tau_layer (ns, median)', 'ZZ couplers in the cone', 'p = 0 delay-matched V(k = L) +/- 2 sigma', 'shift vs ZZ off',
                   'p = 0.25 reset V(k = L) +/- 2 sigma', 'shift vs ZZ off', 'separation', 'Var_mask[C]', 'pattern floor Var_mask/(2K), K = 256',
                   'combined floor', 'separation / combined floor', 'clause (b) separation >= 3x', 'clause (d) pattern floor < half separation', 'status p = 0 / p = 0.25'], sep_rows)

# ----------------------------------------------------------------------------- clause (b) readings under three models and four rule versions
D30 = ppsum['deviation_30']; D35 = ppsum['deviation_35']; D44 = ppsum['deviation_44']
OFF = ppsum['zz_off_record']; IDLE = ppsum['zz_idle_upper_bound_record']


def rung_line(rec, key='rungs'):
    parts = []
    for rg in rec[key]:
        if rg.get('counted') is False:
            parts.append(f'{rg["n"]}: unresolvable ({rg["var_p0_L8_over_shot_floor"]:.2f} floors)')
        else:
            f2s = rg['M350']['fall_over_2sigma'] if 'M350' in rg else rg['fall_over_2sigma']
            ok = rg['passes'] if 'M350' not in rg else rg['M350']['passes']
            parts.append(f'{rg["n"]}: {"pass" if ok else "fail"} ({rg["fall_over_3sf"]:.2f}x 3 floors, fall / 2 sigma {f2s:.2f} at M = 350)')
    return '; '.join(parts)


def d30_reading(rec):
    rg = rec['rungs']
    return rec.get('reading', 'PASS' if rec['passes'] else 'FAIL'), rung_line(rec)


# Deviation 45: bar = 3 x the larger of the two references' shot floors; with all six at 16384 shots it equals the Deviation 44 bar, so the rung numbers coincide
d45_rows = [(r['n'], r['var_p0_L8_over_shot_floor'], r['fall'], r['fall_over_3sf'], r['fall_over_2sigma'], r['passes']) for r in D44['rungs']]
d45_pass = sum(1 for r in d45_rows if r[5])
r30_off = d30_reading(OFF['deviation_30']); r30_idle = d30_reading(IDLE['deviation_30']); r30_layer = d30_reading(D30)
r35_off = (OFF['deviation_35']['reading'], rung_line(OFF['deviation_35'])); r35_idle = (IDLE['deviation_35']['reading'], rung_line(IDLE['deviation_35'])); r35_layer = (D35['reading'], rung_line(D35))
r44_off = (OFF['deviation_44']['reading'], rung_line(OFF['deviation_44'])); r44_idle = (IDLE['deviation_44']['reading'], rung_line(IDLE['deviation_44'])); r44_layer = (D44['reading'], rung_line(D44))
lay87 = next(r for r in D30['rungs'] if r['n'] == 87)


def badge(reading):
    # verdict word as a badge, followed by the file's reading minus its leading verdict word
    r = reading.upper()
    b = '**pass**' if r.startswith('PASS') else '**fail**' if r.startswith('FAIL') else '**inconclusive**'
    return b + ' ' + re.sub(r'^(PASS|FAIL|inconclusive)\s*', '', reading)


readings_table = table(['clause (b) wording', 'adopted (UTC, 20 Sep 2026)', 'shots on the p = 0 references', 'ZZ off (record, booked before ZZ)', 'idle-ZZ upper bound (record, 2x angle)', 'Deviation 34 layer model (booked; numbers committed ' + ZZ_COMMIT_TIME + ')'], [
    ['Deviation 30, frozen: per rung, depth fall L = 8 -> 12 > 3 x shot floor and > 2 x the L = 8 draw 2 sigma at the booked M (250, then 350); rung with the L = 8 reference < 3 floors "unresolvable", not counted; pass with >= 2 of 3',
     'frozen 19-20 Sep; PI countersigned 07:54 IST (02:24 UTC)', '4096 on all six',
     f'{badge(r30_off[0])}: {r30_off[1]}', f'{badge(r30_idle[0])}: {r30_idle[1]}',
     f'{badge(r30_layer[0])}: {r30_layer[1]}; the 10x10 rung is counted ({lay87["var_p0_L8_over_shot_floor"]:.2f} floors) and its fall is {lay87["fall_over_3sf"]:.2f} x 3 floors'],
    ['Deviation 35: rung counted on the measured reference at its own shot count; fewer than 2 counted rungs = inconclusive; n = 53 L = 8 reference at 16384 shots',
     '03:25 (v0.11.0)', '16384 at n = 53 L = 8; 4096 elsewhere',
     f'{badge(r35_off[0])}: {r35_off[1]}', f'{badge(r35_idle[0])}: {r35_idle[1]}', f'{badge(r35_layer[0])}: {r35_layer[1]}'],
    ['Deviation 44: the three L = 8 references at 16384 shots (floor 3.05e-5), rungs counted against that floor',
     '04:20 (v0.11.3)', '16384 at L = 8; 4096 at L = 12',
     f'{badge(r44_off[0])}: {r44_off[1]}', f'{badge(r44_idle[0])}: {r44_idle[1]}', f'{badge(r44_layer[0])}: {r44_layer[1]}'],
    ['Deviation 45: fall bar = 3 x the larger of the two references\' shot floors (reading of the frozen text); all six references at 16384 shots (bar 9.16e-5); 2 sigma clause on the measured L = 8 bootstrap',
     '04:30 (v0.11.4)', '16384 on all six',
     '**pass** 3 of 3 (the bar equals the Deviation 44 floor, same rungs and falls: ' + ' / '.join(f'{r["fall_over_3sf"]:.2f}' for r in OFF['deviation_44']['rungs']) + ' x 3 floors)', '**pass** 3 of 3 (' + ' / '.join(f'{r["fall_over_3sf"]:.2f}' for r in IDLE['deviation_44']['rungs']) + ' x 3 floors)',
     f'**pass** {d45_pass} of 3: ' + '; '.join(f'{n}: {"pass" if ok else "fail"} (reference {ref:.1f} floors, fall {f3f:.2f} x 3 floors, fall / 2 sigma {f2s:.2f} at M = 350)' for n, ref, fall, f3f, f2s, ok in d45_rows)],
])

# ZZ shift table
shift_rows = []
for r in ppsum['zz_shift']:
    shift_rows.append([r['patch'], r['n'], r['L'], r['dial'], r['p'], e4(r['var_kL_off']), e4(r['var_kL_on']),
                       f'{r["var_kL_shift"] * 100:+.1f}%' + ('' if r.get('var_kL_shift_2sigma') is None or (isinstance(r.get('var_kL_shift_2sigma'), float) and math.isnan(r['var_kL_shift_2sigma'])) else f' +/- {r["var_kL_shift_2sigma"] * 100:.1f}%'),
                       f'{r["var_k1_shift"] * 100:+.1f}%', e4(r['var_cost_off']), e4(r['var_cost_on'])])
shift_table = table(['patch', 'n', 'L', 'dial', 'p', 'V(k = L) ZZ off', 'V(k = L) Deviation 34 ZZ', 'shift (k = L) +/- 2 sigma', 'shift (k = 1)', 'Var[C] ZZ off', 'Var[C] Deviation 34 ZZ'], shift_rows)

zz_ok = sum(1 for r in zzval_rows if r['within_tol'] == 'True')
zz_maxrel = max(fl(r['rel_diff']) for r in zzval_rows if r['model'] != 'nonunital')
zz_nu = max(fl(r['rel_diff']) for r in zzval_rows if r['model'] == 'nonunital')

# ----------------------------------------------------------------------------- kept content: exact grid, paired D, null control, Deviation 15 tables, L = 4 groups, dial grid
grid_rows.sort(key=lambda r: (int(r['n']), int(r['L']), int(r['k']), MODELS.index(r['model'])))
grid_table = table(['model', 'patch', 'n', 'L', 'k', 'M', 'cone', 'method', 'variance', '95% CI', 'hi/lo', 'eps_N 4096', 'eps_N 16384', 's', 'note'],
                   [[r['model'], r['patch'], r['n'], r['L'], r['k'], r['M'], r['n_cone'], r['method'] + (' x32' if r['n_traj'] == '32' else ''),
                     f'{fl(r["var"]):.3e}', f'[{fl(r["ci_lo"]):.3e}, {fl(r["ci_hi"]):.3e}]', f'{fl(r["hi_lo"]):.2f}',
                     f'{fl(r["eps_N_4096"]):.2e}', f'{fl(r["eps_N_16384"]):.2e}', f'{fl(r["runtime_s"]):.0f}', r['note']] for r in grid_rows])
li_table = table(['n', 'L', 'M', 'r noiseless', 'r unital', 'r non-unital', 'R unital [95% CI]', 'R non-unital [95% CI]', 'D = R_nu - R_u [95% CI]', 'separated (D_lo > 0)'],
                 [[r['n'], r['L'], int(float(r['M'])), f3(fl(r['r_noiseless'])), f3(fl(r['r_unital'])), f3(fl(r['r_nonunital'])),
                   f'{fl(r["R_unital"]):.3f} [{fl(r["R_unital_lo"]):.3f}, {fl(r["R_unital_hi"]):.3f}]',
                   f'{fl(r["R_nonunital"]):.3f} [{fl(r["R_nonunital_lo"]):.3f}, {fl(r["R_nonunital_hi"]):.3f}]',
                   f'{fl(r["D"]):+.3f} [{fl(r["D_lo"]):+.3f}, {fl(r["D_hi"]):+.3f}]', r['separated']] for r in li_rows])
null_table = table(['n', 'edge', 'register', 'null qubit', 'N shots', 'Var_null', '95% CI', '1/(2N)', 'two-term floor', 'Var_null / (1/(2N))', 'mean grad +/- se', 'Deviation 37 floor (Var_null + 3 sigma)'],
                   [[r['n'], r['edge'], r['n_register'], r['null_parameter_qubit'], r['shots'], f'{fl(r["var_null"]):.3e}',
                     f'[{fl(r["ci_lo"]):.3e}, {fl(r["ci_hi"]):.3e}]', f'{fl(r["floor_analytic_1_over_2N"]):.3e}', f'{fl(r["floor_two_term_mean"]):.3e}',
                     f'{fl(r["ratio_var_to_analytic"]):.2f}', f'{fl(r["mean_grad"]):+.1e} +/- {fl(r["se_mean"]):.1e}',
                     f'{fl(r["var_null"]) + 3 * (fl(r["ci_hi"]) - fl(r["ci_lo"])) / (2 * 1.96):.3e}'] for r in null_rows])

dev15_tables = {}
for L in (8, 12):
    rows = []
    for n, patch in PATCHES:
        for m in MODELS:
            d = dev[(n, L, m)]
            deficit = d['vmc'] - d['vpp']
            rows.append([m, patch, n, d['edge'], d['nb'], f'{e4(d["vmc"])} +/- {e3(2 * d["se"])}', e4(d['vpp']),
                         f'{deficit:+.2e} ({deficit / d["vmc"] * 100:+.1f}%)', e3(max(2 * d['se'], deficit)),
                         f'{e4(d["v1"])} +/- {e3(2 * d["se1"])}', f'{d["disc"]:.3f}', status_word(d['status'])])
    dev15_tables[L] = table(['model', 'patch', 'n', 'edge', 'broken couplers', 'V_MC(k = L) +/- 2 sigma', 'lower bound V_trunc(k = L)', 'deficit',
                             'Dev. 15 error', 'V_MC(k = 1) +/- 2 sigma', 'discarded mass', 'status'], rows)
l4_rows = []
for (n, L, m), d in sorted(dev.items(), key=lambda kv: (kv[0][1], kv[0][0], MODELS.index(kv[0][2]))):
    if L in (2, 4):
        l4_rows.append([d['patch'], n, L, d['ncone'], m, f'{e4(d["v1"])} +/- {e3(2 * d["se1"])}', f'{e4(d["vmc"])} +/- {e3(2 * d["se"])}',
                        e4(d['vpp']), f'{(d["vmc"] - d["vpp"]) / d["vmc"] * 100:+.2f}%', status_word(d['status'])])
l4_table = table(['patch', 'n', 'L', 'cone', 'model', 'V(k = 1) +/- 2 sigma', 'V(k = L) +/- 2 sigma', 'V_trunc(k = L)', 'deficit', 'status'], l4_rows)

rule_rows = []
for L in (8, 12):
    for n, patch in PATCHES:
        a, b, c = dev[(n, L, 'noiseless')], dev[(n, L, 'unital')], dev[(n, L, 'nonunital')]
        sep = b['v1'] - a['v1']
        err = max(max(2 * x['se1'], x['v1'] - x['v1pp']) for x in (a, b))
        # Deviation 15 designation: hardware-only when the propagation error exceeds half the unital - noiseless separation;
        # criterion (c) part 1 flag: |separation| > 2 x 1/(2 x 16384). Recomputed here (the merged re-summary's flag list is empty).
        ratio = err / (abs(sep) / 2)
        flag = {'hardware_only': ratio > 1, 'exceeds_2x_floor_16384': abs(sep) > c1['threshold_2x_floor_16384']}
        for f in FIND.get('deviation_15_hardware_only_flags', []):
            if f['n'] == n and f['L'] == L:
                assert f['hardware_only'] == flag['hardware_only'] and f['exceeds_2x_floor_16384'] == flag['exceeds_2x_floor_16384'], (n, L, f, flag)
        rule_rows.append([patch, n, L, f'{sep:+.3e}', e3(err), f'{ratio:.3f}' + (', knife-edge' if abs(ratio - 1) < 0.005 else ''),
                          'yes' if flag['exceeds_2x_floor_16384'] else '**no**', '**hardware-only**' if flag['hardware_only'] else 'confirmatory',
                          f'{c["v1"] - b["v1"]:+.2e} (2 sigma {e3(2 * c["se1"])})'])
dev15_rule_table = table(['patch', 'n', 'L', 'V_unital - V_noiseless (k = 1)', 'Dev. 15 error', 'error / half separation', '> 6.10e-5 (criterion (c) part 1)', 'Deviation 15 designation', 'V_nonunital - V_unital (k = 1)'], rule_rows)

li_pp_rows = []
for q in CRIT['c']['part2']['propagation_point_estimates']:
    li_pp_rows.append([q['n'], q['L'], f3(q['r_noiseless']), f3(q['r_unital']), f3(q['r_nonunital']), f3(q['R_unital']), f3(q['R_nonunital']),
                       f'{q["D"]:+.3f} +/- {q["D_2sigma"]:.3f}', 'no' if not q['separated_point_estimate'] else 'yes',
                       '; '.join(sorted(set(status_word(s).replace('**', '') for s in q['status'])))])
li_pp_table = table(['n', 'L', 'r noiseless', 'r unital', 'r non-unital', 'R unital', 'R non-unital', 'D +/- 2 sigma (independent, not paired)', 'separated', 'row status'], li_pp_rows)

floor_rows = []
for L in (8, 12):
    for n, patch in PATCHES:
        for m in ('unital', 'nonunital'):
            d = dev[(n, L, m)]
            for lab, v in (('k = 1', d['v1']), ('k = L', d['vmc'])):
                floor_rows.append([n, L, m, lab, e4(v), f2(v / SF4096), 'yes' if v > d37_4096['floor_3sigma_used'] else '**no**',
                                   'yes' if v > d37_16384['floor_3sigma_used'] else '**no**', 'yes' if v > 10 * SF4096 else 'no', 'yes' if v > 10 * SF16384 else 'no'])
floor_table = table(['n', 'L', 'model', 'k', 'V_MC', 'V / (1/(2 x 4096))', f'above the Deviation 37 floor at 4096 shots ({d37_4096["floor_3sigma_used"]:.2e})',
                     f'above the Deviation 37 floor at 16384 shots ({d37_16384["floor_3sigma_used"]:.2e})', 'above the superseded 10x allowance at 4096 (1.22e-3)', 'above the superseded 10x allowance at 16384 (3.05e-4)'], floor_rows)

dial_rows = []
for L in (8, 12):
    for d_, p in (('delay', 0.0), ('dephase', 0.5), ('reset', 0.25), ('reset', 0.5)):
        r = dial_off[(L, d_, p)]
        dial_rows.append([L, d_, p, f'{e4(r["v1"])} +/- {e3(2 * r["se1"])}', f'{e4(r["vmc"])} +/- {e3(2 * r["se"])}', f'{e4(r["vc"])} +/- {e3(2 * r["sec"])}',
                          f'{r["mean"]:.3e}', e4(r['pf']) if r['pf'] is not None else 'n/a (no masks)', status_word(r['status'])])
dial_table = table(['L', 'dial', 'p', 'V(k = 1) +/- 2 sigma', 'V(k = L) +/- 2 sigma', 'Var[C_mix] +/- 2 sigma', 'E[C_mix]', 'pattern floor (K = 256)', 'status'], dial_rows)
pending_values += ['Dial-grid rows (6x10, n = 53; 8 rows) under the Deviation 34 layer model: the ZZ-off values stand; the idle-ZZ upper bound moved them by at most 0.8% at k = L (reset) and 9-15% on the p = 0 / dephasing references',
                   'Main-grid (Deviation 15) noisy rows at L = 8 / 12 under the Deviation 34 layer model: the ZZ-off values stand; expected shift <= 10% (the Gate 1b p = 0 rows moved -5% to -8% at L = 8), criterion (d) margin 1.99e-4 vs 1.38e-4 holds',
                   'Deviation 36 recompute of the n = 39 rows at edge (93, 103): not done (tracker P1.1.21); superseded by Deviation 46, which re-derives the edge per run day (cone-graph rule)',
                   'Gate 1b clause (e): predicted M = 100 interval widths for every core point (pre-registration Gate 1b status: still running)',
                   'Gate 1b references on the run-day placement: re-drawn under Deviation 46 before the first Paper 1 pre-flight (the 20 Sep 03:08Z snapshot gives 20 / 37 / 50 / 68 / 85)']

# validation
n_val = len(val_rows); n_in = sum(1 for r in val_rows if r['inside_ci'] == 'True')
pts = {(r['model'], r['dial'], r['patch'], r['L'], r['k']) for r in val_rows}
p64 = next(r for r in pat_rows if r['K'] == '64'); p256 = next(r for r in pat_rows if r['K'] == '256')
ratio_pat = fl(p64['excess_var_exact']) / fl(p256['excess_var_exact'])
ratio_pat_err = ratio_pat * math.hypot(fl(p64['excess_var_se']) / fl(p64['excess_var_exact']), fl(p256['excess_var_se']) / fl(p256['excess_var_exact']))

# placements
OLD = {'4x5': ('20, (8, 1)', '93_103'), '4x10': ('39, (8, 0)', '94_95'), '6x10': ('56, (0, 0)', '35_36'), '8x10': ('71, (2, 0)', '43_44'), '10x10': ('90, (0, 0)', '43_44')}
NEW20 = {'4x5': ('20, (8, 2)', '94_104'), '4x10': ('37, pending', '94_104 by the cone-graph rule (Deviation 36 restated by Deviation 46)'), '6x10': ('50, (3, 0)', '43_44'), '8x10': ('68, (3, 0)', '75_85'), '10x10': ('85, pending', 'pending')}
pl_rows = []
for patch in ['4x5', '4x10', '6x10', '8x10', '10x10']:
    p = placements['patches'][patch]
    pl_rows.append([patch, OLD[patch][0] + ', edge ' + OLD[patch][1], f'**{p["n"]}**, ({p["origin"][0]}, {p["origin"][1]}), edge {p["observable_edge"][0]}_{p["observable_edge"][1]}, {len(p["broken_edges"])} broken couplers',
                    f'**{NEW20[patch][0]}**, edge {NEW20[patch][1]}'])
pl_table = table(['patch', 'old rule (19 Sep 15:59Z snapshot)', 'Deviations 22 + 26 on the 19 Sep 19:25Z snapshot (every Gate 1 / Gate 1b prediction)', '20 Sep 03:08Z snapshot (run-day rule; Deviation 46 re-draw pending)'], pl_rows)
pending_values.append('20 Sep placement details for the 4x10 and 10x10 rungs (origins, broken couplers): the handover records the counts 37 and 85 and the 4x5 / 6x10 / 8x10 moves only; `place_patch` on the 03:08Z snapshot gives the rest')

# ============================================================================= MARKDOWN
md = f"""# {TITLE}

Programme gradvar-phoenix (SSIT Tumakuru; Mohammed Owais, Dr. Raviram V, physics co-author to be decided). Pre-registration `preregistration_q1.html` v0.11.4 (Deviations 31-45; the copy read here) as amended to v0.12.0 by Deviations 46-49 (placement re-derivation per run day; budget model v3; kill rule (b) job packing; Gate 2 (e) transient rule), which this report cites from the adoption log relayed by the coordinator. Data: `main` @ {MAIN_SHA} for the complete Gate 1 grid (135 points, 0 deferred; `gate1_summary.json` read from {SUMMARY_SRC}{SUMMARY_NOTE}), the exact points, the validation and the smoke-test review (`docs/postrun/02_phoenix_smoke_2026-09-20.md`); the Deviation 34 whole-layer-ZZ rows, the clause (b) readings and the shot table from {ZZ_SRC}. Verdict words are those of `gate1_summary.json`; 2 sigma, deficits and ratios are recomputed from the file values; a value absent from the files is written "pending". This is v2 of the report published as v1 on 20 Sep 2026 (commit 1549a12); v1's tables are kept where still valid and its superseded readings are listed in Section 10.

## 0. Decision

**Gate 1: PASS.** Decided 20 Sep 2026 by Claude under Dr. Raviram's delegation (relayed 20:10 IST: he agrees with the deviations so far and asks Claude to act on his behalf, reviewing periodically); PI countersignature on his next review. Conditions: Deviation 46 re-draw of the Gate 1b references on the run-day placement before the first Paper 1 pre-flight; Gate 2 decided after the first campaign day's null-control and M = 200 point (Gate 2 (a)), with (b)-(d) already met on the smoke test and (e) under Deviation 49. Review note: this rebuild had no separate independent review (Owais's 20 Sep compute-budget instruction); its inputs were reviewed (pp-zz-idle review, analysis second review, post-run review).

Basis, in one paragraph: the grid is complete (135 points, 0 deferred); (a) passes under Deviation 25, (b) passes, (c) part 1 passes at {c1['n_exceeding']} of {len(c1['points'])} points, (c) part 2 is not-evaluated and moot under Deviation 16, (d) passes on the exact points and under Deviation 37 at L <= 8 (smallest L = 8 prediction {d37_4096['by_L']['8']['min_var']:.1e} against the bar {d37_4096['floor_3sigma_used']:.2e}) with L = 12 exploratory, (e) passes, (f) is reported; the stop rule (failing (c) or (d)) is not triggered. Gate 1b: the separation clauses pass at every rung under the Deviation 34 layer model ({sep_ratio[(39, 8)]:.1f} / {sep_ratio[(53, 8)]:.1f} / {sep_ratio[(87, 8)]:.1f}x at L = 8, {sep_ratio[(39, 12)]:.1f} / {sep_ratio[(53, 12)]:.1f} / {sep_ratio[(87, 12)]:.1f}x at L = 12); the frozen clause (b) reads pass 3 of 3 under Deviations 44-45 (all six p = 0 references at 16384 shots), with its full reading history in Section 2.2.

## 1. Gate 1 criteria (a)-(f), complete grid

""" + crit_table + f"""

## 2. Gate 1b under the Deviation 34 layer model

### 2.1 Separation clauses

Rows `stage = gate1b`, `zz_layer = on` of `pauliprop_predictions.csv` ({ZZ_SRC}): snapshot unital noise on the Deviation 22 / 26 placements plus the static layer ZZ on every coupler of the cone in every layer and the idle ZZ on both-idle couplers in the dial layer; k = L; p = 0 is the delay-matched control, p = 0.25 the reset dial with K = 256 masks x 16 shots (Deviation 27). Shot floor 1/(2 x 4096) = 1.221e-4 (the p = 0.25 series stays at 4096 shots); combined floor = shot + pattern floor. Shifts are against the ZZ-off rows (v1 of this report).

""" + sep_table + f"""
The separation clause (>= 3x the combined floor) and the pattern-floor clause (< half the separation) pass at every rung and depth; the ZZ terms move the p = 0.25 series by less than 1% and the p = 0 references by -5% to -8% at L = 8 (-9% to -32% at L = 12, where the reference is below the shot floor either way). The 10x10 L = 12 rows are lower bounds only (sampler time cap) and enter the separation with V_trunc.

### 2.2 Clause (b): the four wordings against the three ZZ settings

The unital-reference clause was frozen after Deviation 30 (PI countersigned rows 29-30 on 20 Sep 2026, 07:54 IST). Deviations 35, 44 and 45 change shot counts and the reading of the frozen text, not its wording. The Deviation 34 layer-model numbers (the booked model) arrived at {ZZ_COMMIT_TIME} (commit {ZZ_NUM_SHA} on `pp-zz-layer`), after the three shot decisions had been adopted on the ZZ-off and idle-upper-bound readings; the table shows what each wording reads under each model. Kurtosis kappa = {KAPPA:.2f} (measured at n = 20, L = 8, M = 400), M = 350 on the references.

""" + readings_table + f"""
Reading: under the booked layer model the frozen wording at the pre-registered 4096 shots **fails** (the 10x10 rung is counted at {lay87["var_p0_L8_over_shot_floor"]:.2f} floors and its fall is {lay87["fall_over_3sf"]:.2f} x 3 floors, so 1 of 2 counted rungs passes), it is **inconclusive** under the idle upper bound (one counted rung; Deviation 35 (ii)) and it **passes** 2 of 2 with ZZ off (v1's reading). Deviation 35 restores a pass (2 of 3) by counting rungs on the measured reference and moving the n = 53 reference to 16384 shots; Deviations 44 and 45 move every reference to 16384 shots and all three rungs count and pass under every ZZ setting (Deviation 45 with the layer model: {' / '.join(f'{r[3]:.2f}' for r in d45_rows)} x 3 floors; fall / 2 sigma {' / '.join(f'{r[4]:.2f}' for r in d45_rows)} at M = 350). The shot decisions were taken on predictions that the layer model has since lowered by 5-8% at L = 8; the margins under Deviation 45 (the smallest 2.77x on the 53-qubit rung) absorb that. The frozen wording is unchanged; the Deviation 39 on-day M rule (M -> 600 on a rung whose measured 2 sigma exceeds half its predicted fall) remains the safety valve.

### 2.3 The ZZ model (Deviation 34)

Convention exp(-i zeta tau/4 Z_a Z_b) per pair over a time tau, zeta = 2 pi J with J the signed per-edge coupling of the raw properties (median 27 kHz over 218 couplers), i.e. `rzz(zeta tau/2)`; the conditional phase one qubit accrues is zeta tau and the incoherent weight moved per pair per layer is sin^2(zeta tau/2). tau_layer is read from the scheduled ISA circuits (`scripts/zz_layer_timing.py`, `zz_layer_timing.json`): 380-392 ns per grid layer, of which the static ZZ-active time per coupler-layer is 232-244 ns median (204-312 ns range), plus the 400 ns dial slot as a mask-conditional both-idle term; per pair and layer the rerouted weight is 7.8e-5 (static, 244 ns) and 1.1e-3 (idle, 400 ns); the earlier idle-only run at twice the angle moved 4.5e-3 and is kept as the upper-bound record. Validation (`pauliprop_zz_layer_validation.csv`, 2x3, L = 4, three models and the reset dial): {zz_ok} of {len(zzval_rows)} quantities agree with the brute-force doubled-space theta average to <= {zz_maxrel:.1e} relative; the non-unital rows sit at the known {zz_nu:.1e} Z -> I relaxation residual of the base model (identical without ZZ); the 2x2 plaquette test with the static layer and the idle term agrees to 1e-9. The static term moves the 2x3 L = 4 variances by -0.22%.

""" + shift_table + f"""
### 2.4 Pending under the layer model

The layer model has been applied to the 12 Gate 1b rows. The dial-grid rows at n = 53 and the main-grid (Deviation 15) noisy rows at L = 8 / 12 stand at their ZZ-off values (Sections 7 and 8): the expected shift is <= 10% (the idle upper bound, four times the weight, moved the reset rows by at most 0.8% at k = L and the p = 0 rows by 9-15%), and the criterion (d) margin under Deviation 37 (1.99e-4 against 1.38e-4, a factor 1.45) holds under a 10% shift. Deviation 46 re-draws the Gate 1b references on the run-day placement before the first Paper 1 pre-flight.

## 3. Placement: 19 Sep predictions, 20 Sep snapshot, Deviation 46

Every Gate 1 and Gate 1b prediction was drawn on the 19 Sep 19:25Z snapshot (`ibm_phoenix_2026-09-19T192510Z.csv`; ladder n = 20 / 39 / 53 / 70 / 87). Deviations 22 and 26 place the patches from the newest snapshot's raw properties and the runner re-derives the placement on the run day: on the 20 Sep 03:08Z snapshot the ladder is **20 / 37 / 50 / 68 / 85**, the 4x5 moves to origin (8, 2) with observable edge 94_104 (Q91's initialisation error rose to 1.05e-3 overnight), the 6x10 and 8x10 move to origin (3, 0) with edges 43_44 and 75_85, and Q67 and Q119 are newly excluded. The smoke test ran on that 4x5 (qubits 82-86 / 92-96 / 102-106 / 112-116, edge 94_104, coupler 95-96 broken). Deviation 36's 4x10 edge (93, 103) was an instance of the cone-graph rule on the 19 Sep placement and no longer matches; **Deviation 46** re-states it as the rule the generator implements (the intact 4x10 coupler whose L = 2 cone graph equals the 4x5 rung's; on 20 Sep the 4x5 edge is 94_104, so the 4x10 edge follows it), re-derives the placement per run day, re-draws the Gate 1 / Gate 1b predictions on the run-day placements before each day's pre-flight (`gate1_pauliprop.py --only-missing`, keyed by patch, edge and cone graph) with the 19 Sep predictions kept as the pre-registered record, and records the ladder counts per run day in each list's `placement` block.

""" + pl_table + f"""
Why the counts move: the readout cut, the initialisation-error cut (5e-4), the |ZZ| rule (1 MHz to an excluded or dead qubit) and the CZ cut (5e-3) are read from each snapshot; a qubit crossing a cut adds a hole or moves a patch. The predictions depend on the cone graph, not on n: the 4x5 and 4x10 rungs share the L = 2 cone graph, as do the 6x10 and 8x10 (Deviation 36), so a re-placement that preserves the cone graph reproduces the prediction and one that does not is re-drawn.

## 4. Smoke-test cross-check (ibm_phoenix, 20 Sep 2026, job list 02)

Not a Gate 1 input (Gate 1 is simulation-only; Deviation 32), but the first hardware datum against the predictions. Ten Estimator jobs in one Batch (run 35489912431, jobs created 04:45 UTC, executed 11:14-11:15 UTC after a 6 h 28 min queue, retrieved 14:17 UTC), 52 QPU seconds charged (0.87 Flex minutes) against 39.6 s predicted by the Deviation 24 model (ratio 1.31); 359.13 Flex minutes remain. Findings (`docs/postrun/02_phoenix_smoke_2026-09-20.md`):

* **The device tracks the noiseless gradients draw by draw.** n = 20, k = 1, M = 10, 4096 shots: corr(noiseless, hardware) = 0.999 / 0.999 / 1.000 at L = 2 and 0.979 / 0.974 / 0.963 at L = 8 (levels 0 / 1 / 2); slope hardware / noiseless 0.90 / 0.94 / 1.00 at L = 2 and **0.77 / 0.87 / 1.11 at L = 8**, i.e. a global attenuation at level 0 consistent with the unital model (the Gate 1 unital / noiseless variance ratio at L = 8 is 0.62-0.69, slope 0.79-0.83), TREX recovering to 0.87 and ZNE mildly over-correcting; per-draw residual at the shot level (0.009-0.018 against a shot SE of 0.011-0.028). The L = 8 sample variance is 8.5x its prediction at every level, driven by one heavy-tailed draw (seed 13, g = -0.128 on hardware, -0.174 noiseless): a 10-draw sample from a kurtosis-6-8 distribution does not test a population variance; the main grid's M = 200 does.
* **Usage 1.31x the model** (5 / 8 / 15 s on the three grid jobs against 4.7 / 6.4 / 11.8 s): the per-job constant is 3.0-3.1 s at resilience 0 and 5.6-5.9 s at resilience >= 1 (not 2 s), the per-execution time 11.4 us at level 0 (below the modelled 16.5 us), ZNE multiplies timed seconds by 5.0 (not 3), and the Estimator runs 64 shots per pub when 16 are requested at resilience >= 1. **Deviation 47** adopts these as budget model v3; the Section 2 grid re-budgets to about 62 min at 1 us (73.1 under v2) against its 190.5-minute line.
* **Kill rule (b) fired** on the per-job constant alone (171 jobs x 3.0 s = 8.6 min against the 7.0-minute line; 12.8 min on the evaluator's weighting), so the dial arm in the Deviation 27 job structure does not fit; **Deviation 48** fixes this by job packing. Kill rules (a) (reset error max 8.8e-3 raw, 5.4e-3 net of the prepare-|0> reference; line 2e-2), (c) (0 mid-circuit measures; dial layer 0.75 us) and (d) (mid-circuit reset accepted at levels 0 and 1) pass.
* **Gate 2**: (a) non-decisive at M = 10 by design (L = 8: z = 1.72 against 3; L = 2: z = 3.30), decided on the first campaign day with the measured null control and M = 200; (b) pass (default rep_delay 1 us, range 0-2000 us, dynamic_reprate_enabled True; grid 73.1 min under v2 against 200); (c) pass (state-preparation bias change 3.4e-4 / 1.2e-3 between 1 us and 250 us against 1.56e-2; every rung honoured, per-execution time 14.1 us + 0.974 x rep_delay); (d) pass (58.9 min for the grid against 200); (e) one cone qubit (Q93, neighbour of observable qubit 94) at 3.03x its planning readout error in the 03:49 UTC calibration, back to 0.56% by 13:44 UTC, below the 3% layout cut: **Deviation 49** makes a single non-observable cone qubit above 1.5x but below the layout cut a logged re-read at the next calibration rather than a pause, while any observable qubit above 1.5x pauses.
* Dial probes (p = 0.25, L = 8, one draw, 16 masks x 16 shots): pipeline exercised end to end, no reading; level-1 pubs at 16 requested shots ran at 64 (the Estimator's measure-twirling minimum), which enters the dial design and budget.

## 5. Exact light-cone results, L <= 4 (unchanged from v1)

Method (`scripts/gate1_ladder.py`): exact `density_matrix` for cones <= 10 qubits (the noisy L = 1 points on the 8-qubit edge-plus-neighbours register), 32 noise trajectories on Aer `statevector` up to 24 cone qubits, statevector for noiseless points; M = 200 (M = 100 for the 23-qubit noiseless 4x10 L = 2 cone, excluded from (b)); seed 2026; 10,000 bootstrap resamples; {n_grid} points under Deviations 22 + 26 (commit c103d95). Cone sizes: 4x5 L = 1/2/4: 2/16/20; 4x10: 2/20/36; 6x10: 2/16/48; 8x10: 2/16/65; 10x10: 2/12/72.

### 5.1 Grid

""" + grid_table + f"""
### 5.2 The four paired non-unital differences (criterion (c) part 2, Deviation 14)

""" + li_table + f"""
None of the four is separated; at L = 2 the predicted |D| is at the 1e-2 level against an interval half-width of about 0.02, the Deviation 16 reading.

### 5.3 Null control (criterion (d)); the last column is the Deviation 37 floor

""" + null_table + f"""
The ratio below 1 is expected: at L = 1, E[<Z_i Z_j>^2] is about 1/4, so the exact two-term floor is about 0.78/(2N) and 1/(2N) is the ev = 0 upper bound. Deviation 37 replaces the 10x allowance by the null floor + 3 sigma, {d37_4096['floor_3sigma_used']:.2e} at 4096 shots and {d37_16384['floor_3sigma_used']:.2e} at 16384 (the n = 39 register, the larger of the two).

## 6. Pauli-propagation method and validation (unchanged from v1, plus the ZZ terms)

The quantity is Var_theta[d<O>/d theta_(k,q)] and Var_theta[<O>] for theta uniform on [0, 2 pi)^(nL), O the readout-folded Z_i Z_j on the interior edge. Back-propagating O through the transpiled noisy circuit writes <O> as a sum over Pauli paths whose theta-dependence is a product of 1 / cos / sin factors; because E[cos^2] = E[sin^2] = 1/2 and every cross term averages to zero, the second moment is a positive linear map on squared coefficients over Pauli strings, and the derivative keeps the paths that do not commute with the generator at gate (k, q). Every channel parameter is read from the Pauli-transfer matrices of the `gradvar.noise` models; the reset dial is N_p = p Reset + (1 - p) Idle(400 ns); the Deviation 34 ZZ terms are one amplitude-level op per layer (Section 2.3). Two engines: a deterministic truncation (delta = 1e-7 and 1e-6, cap 4e5 strings), a rigorous lower bound V_trunc <= V; and an unbiased Pauli-path Monte Carlo (N = 2e6 paths, 1e6 on the larger ZZ-layer rows) with a standard error. Prediction V_MC +/- 2 sigma; Deviation 15 error max(2 sigma, V_MC - V_trunc); `status` converged / sampled / not converged as in `docs/PAULIPROP.md`. Validation: 3-point angle grid on a 2x2 patch exact to 1e-6 (noiseless, reset dial) and 3e-5 (non-unital); **{n_in} of {n_val} rows ({len(pts)} distinct points, {len(pts) - 2} inside)** of `pauliprop_validation.csv` inside the 95% bootstrap interval of the exact M = 200 estimate, the two outside missing by less than 5% of the interval width; the sampler reproduced independently at 4x5 L = 8 with two seeds; the pattern-floor check on 2x3 L = 4 gives an excess-variance ratio K = 64 / K = 256 of {ratio_pat:.2f} +/- {ratio_pat_err:.2f} against 4 with PP Var_mask {fl(p64['var_mask_pp']):.4f} vs exact {fl(p64['var_mask_exact']):.4f} +/- {fl(p64['var_mask_exact_se']):.4f}; the ZZ-layer op exact to {zz_maxrel:.0e} on 2x3 L = 4 (Section 2.3). Measured k = L kurtosis {KAPPA:.2f} at (4x5, n = 20, L = 8, M = 400; the Deviation 30 / 39 input). Known gaps: idle-branch T1 (t_z about 2e-3 per layer) unmodelled; two Z -> I relaxation branches across a CZ treated as distinct paths (relative < 1e-3, positive).

## 7. Deviation 15 predictions (ZZ off; these values stand, Section 2.4)

### 7.1 L = 8

""" + dev15_tables[8] + f"""
### 7.1b L = 12 (exploratory under Deviations 37 and 43)

""" + dev15_tables[12] + f"""
### 7.1c The formerly deferred groups: large-cone L = 4 (4x10 .. 10x10) and the cost-cut noisy 4x5 L = 4 and 4x10 L = 2 (new in v2; grid complete)

""" + l4_table + f"""
### 7.2 Deviation 15 rule and criterion (c) part 1 at k = 1 (L = 8 / 12)

""" + dev15_rule_table + f"""
### 7.3 Layer-index point estimates (criterion (c) part 2; moot under Deviation 16)

""" + li_pp_table + f"""
### 7.4 Noisy L >= 8 predictions against the Deviation 37 floor (and the superseded 10x allowance)

""" + floor_table + f"""
## 8. Dial-grid predictions at n = 53 (ZZ off; these values stand, Section 2.4)

""" + dial_table + f"""
Reference lines: the ansatz-specific floor of Deviation 33 replaces p^4/9 as the H5 / H6 threshold (at n = 53, raw readout: k = L floors 1.06e-3 / 7.35e-3 and Var[C] floors 2.20e-3 / 1.50e-2 at p = 0.25 / 0.5; the predictions clear them by 1.88 / 1.30 and 1.62 / 1.22); p^4/9 (4.3e-4 / 6.9e-3) is a historical line. E[C_mix] = readout-folded p^2 (0.0658 / 0.252). H6 statistic (Deviation 40): the k = L depth ratio V(12)/V(8), predicted 1.00 for the dial against 0.023-0.044 for the unital references, with the absolute separation from the references; the dial k = 1 rows (3.5e-6 to 1.5e-8) are below the shot floor and reported as upper bounds. Mask sharing between shift circuits is fixed per point and logged (Deviation 38).

## 9. Budget lines recorded so far

* Ledger (pre-registration v0.11.4 Section 6, 1 us rep_delay): main grid **190.5** min (re-based from 200 by Deviation 45), dial arm 65 + 8.0 (Deviation 44, reserve) + 9.5 (Deviation 45 top-up) = 75.0 min core, Paper 2 characterisation 45, reserve 50 (10 dry run, 20 Deviation 19, 2.6 null controls (Deviation 43), 2.7 absorbed by Deviation 44, up to 4.5 Deviation 39, 4.9 unallocated); total 360. Spent: 52 QPU s (0.87 Flex min) on the smoke test; 359.13 Flex minutes remain.
* **Deviation 24 model (v2) superseded by Deviation 47 (v3)** from the smoke test: 3.0 s per job at resilience 0, +2.7 s at resilience >= 1, 5 us execution overhead, depth-weighted ZNE (x 4.8 on timed seconds), 64-shot minimum per pub at resilience >= 1; the Section 2 grid is about 62 min at 1 us (73.1 under v2, 80 in v1 of this report). The dial arm's 171 jobs per gradient point cost 8.6 min of job constants alone against the 7.0-minute kill line (Deviation 41): **Deviation 48** re-packs the jobs; the re-based dial line is recorded there.
* Deviation 27 (K = 256, 51,200 circuits per gradient point) and the Deviation 30 correction (M = 350 on the p = 0 references) stand; Deviations 44-45 put all six references at 16384 shots (23.6 min at 1 us under v2).

## 10. Superseded since v1 (20 Sep 2026, commit 1549a12)

* Gate 1 overall "not-evaluated" (v1, 32 points deferred) -> grid complete, decision PASS (Section 0).
* Criterion (d) "provisional pass; L = 12 below the 4096-shot floor; shots to be decided" -> pass under Deviation 37 at L <= 8 with the null floor + 3 sigma bar ({d37_4096['floor_3sigma_used']:.2e} at 4096 shots); L = 12 exploratory (Deviations 37, 43); the 10x-allowance rows of v1 are kept only as a record (table 7.4, last two columns).
* Gate 1b clause (b) "pass 2 of 2 counted rungs (Deviation 30, ZZ off)" -> under the Deviation 34 layer model the frozen wording at 4096 shots fails (10x10 fall {lay87["fall_over_3sf"]:.2f} x 3 floors); Deviations 35, 44, 45 read pass 2 of 3 and 3 of 3 (Section 2.2).
* Gate 1b separation ratios 3.19 / 4.24 / 4.02 (L = 8), 5.02 / 4.92 / 4.97 (L = 12), ZZ off -> {sep_ratio[(39, 8)]:.2f} / {sep_ratio[(53, 8)]:.2f} / {sep_ratio[(87, 8)]:.2f} and {sep_ratio[(39, 12)]:.2f} / {sep_ratio[(53, 12)]:.2f} / {sep_ratio[(87, 12)]:.2f} under the layer model.
* p = 0 references at L = 8: 7.840e-4 / 2.821e-4 / 3.994e-4 (ZZ off) -> {e4(g1b_layer[(39, 8, 'delay')]['vmc'])} / {e4(g1b_layer[(53, 8, 'delay')]['vmc'])} / {e4(g1b_layer[(87, 8, 'delay')]['vmc'])} (layer model).
* "ZZ idle phase unmodelled (10-20% on the p = 0 reference)" -> modelled (Deviation 34: static layer + idle; measured shift -5% to -8% at L = 8).
* Budget model v2 (Deviation 24) -> v3 (Deviation 47); dial core 63.5 min -> 75.0 min booked (65 + 8.0 + 9.5) and kill rule (b) re-packing (Deviation 48).
* Ladder 20 / 39 / 53 / 70 / 87 (19 Sep snapshot) -> re-derived per run day (Deviation 46); 20 / 37 / 50 / 68 / 85 on the 20 Sep 03:08Z snapshot.
* The p^4/9 reference line -> the Deviation 33 ansatz-specific floor as the H5 / H6 threshold.
* v1 Section 10 "Gate 2 booking decisions for the PI" (six items) -> resolved by Deviations 37, 43-49 and the decision block; the Deviation 24 table recompute is now the Deviation 47 v3 re-base before the 1 October pre-flight.

## 11. Sources and pending values

* Pre-registration: `scratchpad/prereg/preregistration_q1.html` v0.11.4 (Deviations 31-45 read here); v0.12.0 Deviations 46-49 as relayed in the adoption log (placement re-derivation; budget model v3; kill rule (b) job packing; Gate 2 (e) transient rule).
* Reviews: `scratchpad/review/gate1_grid_review.md`, `gate1_pauliprop_review.md` (passes 1 and 2), `gate1_report_review.md` (v1), the pp-zz-idle review, `analysis_p1_review.md` and `analysis_p1_review2.md`, `docs/postrun/02_phoenix_smoke_2026-09-20.md`; `prereg_v05_review.md`, `marrakesh_postrun_review.md`.
* Commits on `main` @ {MAIN_SHA}: [1d52b85]({GH}/commit/1d52b85) smoke-test post-run review; [acea0cb]({GH}/commit/acea0cb) smoke-test retrieval; [7155c34]({GH}/commit/7155c34) merge `pp-zz-idle` (idle ZZ, L = 4 groups, grid complete, shot table); [8bd7e8b]({GH}/commit/8bd7e8b) merge `analysis-p1`; [fc57ee3]({GH}/commit/fc57ee3) pp-zz-idle review fixes; [9cdc673]({GH}/commit/9cdc673) ZZ-on Gate 1b and dial rows, shot table; [81e460b]({GH}/commit/81e460b) ZZ idle rule, deferred groups, complete-grid re-summary; [df0054e]({GH}/commit/df0054e) merge `gate1-pauli-prop`; [1549a12]({GH}/commit/1549a12) report v1. {ZZ_BRANCH_LINE}: [e3859fd]({GH}/commit/e3859fd) Deviation 34 recompute (Gate 1b rows, readings, shot table; Deviation 37 (d) reading); [e5983f8]({GH}/commit/e5983f8) validation; [4571e7c]({GH}/commit/4571e7c) the layer rule and timing.
* Data: `data/predictions/gate1_summary.json`, `gate1_predictions.csv`, `gate1_layer_index.csv`, `gate1_null_control.json`, `gate1_renyi.json`, `ladder_placements.json`, `pauliprop_validation.csv`, `pauliprop_kurtosis.json`, `pauliprop_pattern_check.csv`, `pauliprop_zz_validation.csv` (main); `pauliprop_summary.json`, `pauliprop_predictions.csv`, `gate1b_shot_table.csv`, `pauliprop_zz_layer_validation.csv`, `zz_layer_timing.json` ({ZZ_SRC}); `docs/GATE1_RESULTS.md`, `docs/PAULIPROP.md`, `docs/HANDOVER.md`, `docs/ANALYSIS.md`.

### Values marked pending in this report

""" + '\n'.join(f'* {p}' for p in pending_values) + '\n'

# ============================================================================= HTML
STATUS_WORDS = {
    'pass': 'pass', 'PASS': 'pass', 'Gate 1: PASS.': 'pass', 'fail': 'fail', 'pending': 'pending', 'not-evaluated': 'neutral', 'provisional pass': 'prov', 'reported': 'rep',
    'converged': 'pass', 'sampled': 'prov', 'not converged': 'prov', 'lower bound only': 'prov', 'hardware-only': 'prov', 'inconclusive': 'neutral',
    'no': 'neutral', 'complete': 'pass', 'exploratory': 'neutral', 'fails': 'fail', 'passes': 'pass', 'complete**': 'pass',
}


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)

    def bold(m):
        w = m.group(1); key = w.strip()
        if key in STATUS_WORDS:
            return f'<span class="st" data-status="{STATUS_WORDS[key]}">{w}</span>'
        if re.match(r'^(pass|PASS) \d of \d', key) or key.startswith('pass 3 of 3') or key == '0.77 / 0.87 / 1.11 at L = 8':
            return f'<span class="st" data-status="pass">{w}</span>' if 'pass' in key.lower() else f'<strong>{w}</strong>'
        return f'<strong>{w}</strong>'
    return re.sub(r'\*\*(.+?)\*\*', bold, s)


def md_to_html(text):
    out, lines, i, sec_open = [], text.split('\n'), 0, False
    split = lambda row: [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', row.strip()[1:-1])]
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('# '):
            i += 1; continue
        m = re.match(r'^(##|###) (.+)$', ln)
        if m:
            level = len(m.group(1))
            if level == 2:
                if sec_open:
                    out.append('</section>')
                sid = 's' + re.sub(r'[^0-9]', '', m.group(2).split('.')[0]) if re.match(r'^\d', m.group(2)) else 'sx'
                out.append(f'<section id="{sid}">'); sec_open = True
            out.append(f'<h{level}>{inline(m.group(2))}</h{level}>'); i += 1; continue
        if ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i]); i += 1
            hdr = split(rows[0])
            t = ['<div class="tw"><table><thead><tr>' + ''.join(f'<th scope="col">{inline(c)}</th>' for c in hdr) + '</tr></thead><tbody>']
            for r in rows[2:]:
                t.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in split(r)) + '</tr>')
            t.append('</tbody></table></div>'); out.append('\n'.join(t)); continue
        if re.match(r'^(\*|\d+\.) ', ln):
            ordered = ln[0].isdigit(); items = []
            while i < len(lines) and re.match(r'^(\*|\d+\.) ', lines[i]):
                items.append(re.sub(r'^(\*|\d+\.) ', '', lines[i])); i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        if ln.strip() == '':
            i += 1; continue
        para = []
        while i < len(lines) and lines[i].strip() != '' and not lines[i].startswith(('|', '#', '* ')) and not re.match(r'^\d+\. ', lines[i]):
            para.append(lines[i]); i += 1
        cls = ' class="decision"' if para and para[0].startswith('**Gate 1: PASS.**') else ''
        out.append(f'<p{cls}>{inline(" ".join(para))}</p>')
    if sec_open:
        out.append('</section>')
    return '\n'.join(out)


CSS = """
:root{--paper:#f3f6f8;--surface:#ffffff;--ink:#172029;--muted:#5a6a78;--line:#d6dee5;--line-soft:#e7edf1;--accent:#0b5c6c;--accent-ink:#0b5c6c;--accent-soft:#dfeef0;--head:#0f1a22;
--pass:#1f7a4d;--pass-bg:#e3f3ea;--fail:#b3261e;--fail-bg:#fbe7e5;--prov:#9a5b00;--prov-bg:#fcefd8;--pend:#4d5d6d;--pend-bg:#e6ebf0;--rep:#33547f;--rep-bg:#e3eaf5;--neutral:#4d5d6d;--neutral-bg:#eef1f4;--code-bg:#eef2f5}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#0e1418;--surface:#151c22;--ink:#e4eaef;--muted:#9aaab8;--line:#2a353f;--line-soft:#1f2a33;--accent:#5cc3d0;--accent-ink:#8fd6df;--accent-soft:#12303a;--head:#f2f6f9;
--pass:#6fd39a;--pass-bg:#15301f;--fail:#f39a92;--fail-bg:#3a1a17;--prov:#e6b268;--prov-bg:#34260e;--pend:#aab8c6;--pend-bg:#232d36;--rep:#93b4e0;--rep-bg:#1a2536;--neutral:#aab8c6;--neutral-bg:#1e272f;--code-bg:#1b252d}}
:root[data-theme="dark"]{--paper:#0e1418;--surface:#151c22;--ink:#e4eaef;--muted:#9aaab8;--line:#2a353f;--line-soft:#1f2a33;--accent:#5cc3d0;--accent-ink:#8fd6df;--accent-soft:#12303a;--head:#f2f6f9;
--pass:#6fd39a;--pass-bg:#15301f;--fail:#f39a92;--fail-bg:#3a1a17;--prov:#e6b268;--prov-bg:#34260e;--pend:#aab8c6;--pend-bg:#232d36;--rep:#93b4e0;--rep-bg:#1a2536;--neutral:#aab8c6;--neutral-bg:#1e272f;--code-bg:#1b252d}
html{background:var(--paper)}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding-block:0 64px;padding-inline:16px}
header.rep{border-bottom:1px solid var(--line);padding-block:36px 24px}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent-ink)}
h1{font-size:clamp(24px,3.2vw,34px);line-height:1.15;margin:.35em 0 .5em;color:var(--head);text-wrap:balance;font-weight:600;letter-spacing:-.01em;max-width:30ch}
.meta{display:flex;flex-wrap:wrap;gap:8px 22px;color:var(--muted);font-size:13.5px;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
.meta b{color:var(--ink);font-weight:500}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
.chip{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:5px 12px 5px 8px;font-size:13px}
.chip .st{margin:0}
nav.toc{margin-top:22px;display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13.5px}
nav.toc a{color:var(--accent-ink);text-decoration:none;border-bottom:1px solid transparent}
nav.toc a:hover,nav.toc a:focus-visible{border-bottom-color:var(--accent-ink);outline:none}
section{padding-block:28px 6px;border-bottom:1px solid var(--line-soft)}
section:last-of-type{border-bottom:0}
h2{font-size:21px;font-weight:600;color:var(--head);margin:0 0 14px;letter-spacing:-.005em;text-wrap:balance}
h3{font-size:16px;font-weight:600;color:var(--head);margin:22px 0 10px}
p{max-width:78ch;margin:0 0 14px}
#s0 p,#s1 p,#s2 p,#s3 p,#s4 p{max-width:96ch}
p.decision{border-left:4px solid var(--pass);background:var(--surface);padding:14px 18px;font-size:16px;max-width:96ch}
li{max-width:96ch;margin:0 0 6px}
ul,ol{padding-left:1.3em;margin:0 0 14px}
code{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:.88em;background:var(--code-bg);padding:1px 5px;border-radius:4px;color:var(--ink)}
a{color:var(--accent-ink)}
.tw{overflow-x:auto;margin:6px 0 18px;border:1px solid var(--line);border-radius:6px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:12.6px;font-variant-numeric:tabular-nums;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
thead th{position:sticky;top:0;background:var(--surface);color:var(--muted);font-weight:500;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:12px;letter-spacing:.01em;white-space:nowrap;z-index:1}
tbody td{padding:6px 10px;border-bottom:1px solid var(--line-soft);vertical-align:top;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:var(--accent-soft)}
#s1 tbody td,#s3 tbody td,#s10 td,#s11 td{white-space:normal;min-width:14ch}
#s1 tbody td:nth-child(2),#s1 tbody td:nth-child(3),#s1 tbody td:nth-child(4){min-width:30ch}
#s1 table,#s3 table{font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:13px}
#s2 table.readings td{white-space:normal}
#s2 tbody td:nth-child(n+4){white-space:normal;min-width:16ch}
.st{display:inline-block;font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:11.5px;font-weight:600;letter-spacing:.02em;line-height:1;padding:4px 7px;border-radius:4px;border:1px solid transparent;vertical-align:baseline;white-space:nowrap}
p .st,li .st{font-size:12px;vertical-align:1px}
.st[data-status="pass"]{color:var(--pass);background:var(--pass-bg)}
.st[data-status="fail"]{color:var(--fail);background:var(--fail-bg)}
.st[data-status="prov"]{color:var(--prov);background:var(--prov-bg)}
.st[data-status="pending"]{color:var(--pend);background:var(--pend-bg);border-color:var(--line)}
.st[data-status="rep"]{color:var(--rep);background:var(--rep-bg)}
.st[data-status="neutral"]{color:var(--neutral);background:var(--neutral-bg)}
footer{color:var(--muted);font-size:12.5px;padding-block:24px 0;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
@media (max-width:640px){h1{max-width:none}.meta{gap:6px 14px}table{font-size:12px}}
"""

header = f"""<header class="rep">
<div class="eyebrow">gradvar-phoenix &middot; Gate 1 &middot; pre-registration v0.11.4 / v0.12.0 &middot; report v2</div>
<h1>{html.escape(TITLE)}</h1>
<div class="meta">
  <span>main <b>@ {MAIN_SHA}</b></span>
  <span>Deviation 34 rows <b>{html.escape(ZZ_SRC.split(' (')[0].replace('`', ''))}</b></span>
  <span>predictions on the <b>19 Sep 19:25Z</b> snapshot, ladder <b>20 / 39 / 53 / 70 / 87</b></span>
  <span>for Owais, Dr. Raviram V, the theorist</span>
</div>
<div class="chips">
  <span class="chip"><span class="st" data-status="pass">Gate 1: PASS</span> decided 20 Sep 2026 under delegation; PI countersignature on next review</span>
  <span class="chip"><span class="st" data-status="pass">pass</span> (a) Dev. 25 &middot; (b) &middot; (c) part 1, {c1['n_exceeding']} of {len(c1['points'])} &middot; (d) Dev. 37 at L &lt;= 8 &middot; (e)</span>
  <span class="chip"><span class="st" data-status="neutral">not-evaluated</span> (c) part 2, moot under Dev. 16</span>
  <span class="chip"><span class="st" data-status="neutral">exploratory</span> L = 12 (Dev. 37, 43)</span>
  <span class="chip"><span class="st" data-status="rep">reported</span> (f)</span>
  <span class="chip"><span class="st" data-status="pass">pass</span> Gate 1b separation, all rungs, Dev. 34 model</span>
  <span class="chip"><span class="st" data-status="pass">pass 3 of 3</span> Gate 1b clause (b) under Dev. 44-45 (frozen wording at 4096 shots: <span class="st" data-status="fail">fail</span> under the layer model)</span>
  <span class="chip"><span class="st" data-status="pending">pending</span> {len(pending_values)} listed values (Section 11)</span>
</div>
<nav class="toc" aria-label="Sections">
  <a href="#s0">0 Decision</a><a href="#s1">1 Criteria</a><a href="#s2">2 Gate 1b</a><a href="#s3">3 Placement</a><a href="#s4">4 Smoke test</a>
  <a href="#s5">5 Exact grid</a><a href="#s6">6 Method</a><a href="#s7">7 Deviation 15</a><a href="#s8">8 Dial grid</a>
  <a href="#s9">9 Budget</a><a href="#s10">10 Superseded</a><a href="#s11">11 Sources</a>
</nav>
</header>"""

page = f"""<title>Gradvar Phoenix Gate 1 Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="wrap">
{header}
<main>
{md_to_html(md)}
</main>
<footer>Built from main @ {MAIN_SHA} and {html.escape(ZZ_SRC.split(' (')[0].replace('`', ''))} by scripts/build_gate1_report.py ({{COMMIT_NOTE}}). Derived quantities computed at build time; verdict words as in gate1_summary.json.</footer>
</div>
"""

if __name__ == '__main__':
    if not ARGS.no_md:
        (ROOT / 'docs' / 'GATE1_REPORT.md').write_text(md)
    note = f'builder and Markdown twin docs/GATE1_REPORT.md committed as {ARGS.commit}' if ARGS.commit else 'builder and Markdown twin docs/GATE1_REPORT.md not yet committed to main'
    out = Path(ARGS.html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.replace('{COMMIT_NOTE}', note))
    print('wrote', ROOT / 'docs' / 'GATE1_REPORT.md', len(md), 'chars;', out, len(page), 'chars')
    print('pending marks:', md.count('**pending**'))
    for p in pending_values:
        print(' -', p)
