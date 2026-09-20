#!/usr/bin/env python3
"""Build the Gate 1 report (docs/GATE1_REPORT.md and an HTML artifact page) from the committed data.

Sources (all read from the repository at build time):
  docs/GATE1_RESULTS.md (narrative only), data/predictions/gate1_summary.json (verdict wording, criteria (a)-(f),
  propagation findings), gate1_predictions.csv, gate1_layer_index.csv, gate1_null_control.csv, ladder_placements.json,
  pauliprop_predictions.csv, pauliprop_summary.json, pauliprop_validation.csv, pauliprop_kurtosis.json,
  pauliprop_pattern_check.csv.
Verdict words (pass / fail / provisional pass / not-evaluated / reported) are copied from gate1_summary.json; every
derived number (2 sigma, deficits, ratios) is recomputed here from the file values.

    python scripts/build_gate1_report.py [--html PATH]
"""
import argparse
import collections
import csv
import html
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'predictions'
GH = 'https://github.com/SSIT-Q/gradvar-phoenix'
PREREG = 'preregistration_q1.html v0.9.7 (Version 24)'
TITLE = 'Gate 1 report: simulation predictions before the ibm_phoenix dry run (20 Sep 2026)'
SF4096 = 1 / (2 * 4096)
SF16384 = 1 / (2 * 16384)
PATCHES = [(20, '4x5'), (39, '4x10'), (53, '6x10'), (70, '8x10'), (87, '10x10')]
MODELS = ['noiseless', 'unital', 'nonunital']


def sha():
    try:
        return subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--short', 'HEAD']).decode().strip()
    except Exception:  # noqa: BLE001
        return 'HEAD'


def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def e4(x):
    return 'pending' if x is None else f'{x:.3e}'


def e3(x):
    return 'pending' if x is None else f'{x:.2e}'


def f2(x):
    return 'pending' if x is None else f'{x:.2f}'


def f3(x):
    return 'pending' if x is None else f'{x:.3f}'


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
        return '**lower bound only**'
    return s


def table(headers, rows):
    esc = lambda c: str(c).replace('|', '\\|')
    out = ['| ' + ' | '.join(esc(h) for h in headers) + ' |', '|' + '---|' * len(headers)]
    for r in rows:
        out.append('| ' + ' | '.join(esc(c) for c in r) + ' |')
    return '\n'.join(out) + '\n'


# ----------------------------------------------------------------------------- load
MAIN_SHA = sha()
summary = json.load(open(DATA / 'gate1_summary.json'))
ppsum = json.load(open(DATA / 'pauliprop_summary.json'))
pp_rows = list(csv.DictReader(open(DATA / 'pauliprop_predictions.csv')))
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
D30 = ppsum['deviation_30']
BOOKED = ppsum['gate1b_booked_reading']

pending_values = []
dev, g1b, dial = {}, {}, {}
for r in pp_rows:
    st = r['stage']
    n = int(float(r['n'])) if r['n'] else None
    L = int(r['L'])
    rec = dict(patch=r['patch'], vmc=fl(r['var_kL_mc']), se=fl(r['se_kL_mc']), vpp=fl(r['var_kL_pp']),
               v1=fl(r['var_k1_mc']), se1=fl(r['se_k1_mc']), v1pp=fl(r['var_k1_pp']),
               vc=fl(r['var_cost_mc']), sec=fl(r['se_cost_mc']), mean=fl(r['mean_cost']), disc=fl(r['discarded']),
               status=r['status'], t=fl(r['runtime_s']), nb=int(float(r['n_broken_edges'] or 0)), edge=r['edge'],
               vm=fl(r['var_mask']), vmse=fl(r['var_mask_se']), pf=fl(r['pattern_floor']), K=r['K_masks'],
               p=fl(r['p']), dial=r['dial'])
    if st == 'dev15':
        dev[(n, L, r['model'])] = rec
    elif st == 'gate1b':
        g1b[(n, L, r['dial'])] = rec
    elif st == 'dial':
        dial[(L, r['dial'], rec['p'])] = rec
        if rec['vmc'] is None:
            pending_values.append(f'dial-grid row 6x10 L = {L} {r["dial"]} p = {r["p"]}')

# ----------------------------------------------------------------------------- Deviation 15 tables
dev15_tables = {}
for L in (8, 12):
    rows = []
    for n, patch in PATCHES:
        for m in MODELS:
            d = dev[(n, L, m)]
            deficit = d['vmc'] - d['vpp']
            err = max(2 * d['se'], deficit)
            rows.append([m, patch, n, d['edge'], d['nb'], f'{e4(d["vmc"])} +/- {e3(2 * d["se"])}', e4(d['vpp']),
                         f'{deficit:+.2e} ({deficit / d["vmc"] * 100:+.1f}%)', e3(err),
                         f'[{e4(d["vpp"])}, {e4(d["vmc"] + 2 * d["se"])}]',
                         f'{e4(d["v1"])} +/- {e3(2 * d["se1"])}', e4(d['v1pp']), f'{d["disc"]:.3f}',
                         status_word(d['status']), f'{d["t"]:.0f}'])
    dev15_tables[L] = table(
        ['model', 'patch', 'n', 'edge', 'broken couplers', 'V_MC(k = L) +/- 2 sigma', 'lower bound V_trunc(k = L)',
         'deficit V_MC - V_trunc', 'Dev. 15 error max(2 sigma, deficit)', 'one-sided interval [V_trunc, V_MC + 2 sigma]',
         'V_MC(k = 1) +/- 2 sigma', 'V_trunc(k = 1)', 'discarded mass', 'status', 's'], rows)

rule_rows = []
for L in (8, 12):
    for n, patch in PATCHES:
        a, b, c = dev[(n, L, 'noiseless')], dev[(n, L, 'unital')], dev[(n, L, 'nonunital')]
        sep = b['v1'] - a['v1']
        err = max(max(2 * x['se1'], x['v1'] - x['v1pp']) for x in (a, b))
        flag = next(f for f in FIND['deviation_15_hardware_only_flags'] if f['n'] == n and f['L'] == L)
        ratio = err / (abs(sep) / 2)
        rule_rows.append([patch, n, L, f'{sep:+.3e}', e4(abs(sep) / 2), e3(err), f'{ratio:.3f}' + (', knife-edge' if abs(ratio - 1) < 0.005 else ''),
                          'yes' if flag['exceeds_2x_floor_16384'] else '**no**',
                          '**hardware-only**' if flag['hardware_only'] else 'confirmatory',
                          f'{c["v1"] - b["v1"]:+.2e} (2 sigma {e3(2 * c["se1"])})'])
dev15_rule_table = table(['patch', 'n', 'L', 'V_unital - V_noiseless (k = 1)', 'half separation', 'Dev. 15 error',
                          'error / half separation', '> 2 x floor(16384) = 6.10e-5 (criterion (c) part 1)',
                          'designation (Deviation 15, k = 1 rule as in pauliprop_summary.json)', 'V_nonunital - V_unital (k = 1)'], rule_rows)

li_pp_rows = []
for q in CRIT['c']['part2']['propagation_point_estimates']:
    li_pp_rows.append([q['n'], q['L'], f3(q['r_noiseless']), f3(q['r_unital']), f3(q['r_nonunital']), f3(q['R_unital']),
                       f3(q['R_nonunital']), f'{q["D"]:+.3f} +/- {q["D_2sigma"]:.3f}',
                       'no' if not q['separated_point_estimate'] else 'yes',
                       '; '.join(sorted(set(status_word(s).replace('**', '') for s in q['status'])))])
li_pp_table = table(['n', 'L', 'r noiseless', 'r unital', 'r non-unital', 'R unital', 'R non-unital',
                     'D = R_nu - R_u +/- 2 sigma (independent, not paired)', 'separated (point estimate)', 'row status'], li_pp_rows)

floor_rows = []
for L in (8, 12):
    for n, patch in PATCHES:
        for m in MODELS:
            d = dev[(n, L, m)]
            for lab, v in (('k = 1', d['v1']), ('k = L', d['vmc'])):
                floor_rows.append([n, L, m, lab, e4(v), f2(v / SF4096), f2(v / SF16384),
                                   'yes' if v > 10 * SF4096 else '**no**', 'yes' if v > 10 * SF16384 else '**no**'])
floor_table = table(['n', 'L', 'model', 'k', 'V_MC', 'V / (1/(2 x 4096))', 'V / (1/(2 x 16384))',
                     'above the 10x allowance at 4096 shots (1.221e-3)', 'above the 10x allowance at 16384 shots (3.052e-4)'], floor_rows)

# ----------------------------------------------------------------------------- Gate 1b
g1b_rows = []
clause = {}
for L in (8, 12):
    for n, patch in ((39, '4x10'), (53, '6x10'), (87, '10x10')):
        p0, p25 = g1b[(n, L, 'delay')], g1b[(n, L, 'reset')]
        sep = p25['vmc'] - p0['vmc']
        comb = SF4096 + p25['pf']
        err = max(2 * p0['se'], p0['vmc'] - p0['vpp'], 2 * p25['se'], p25['vmc'] - p25['vpp'])
        clause[(n, L)] = dict(sep=sep, comb=comb, ratio=sep / comb, err=err, p0=p0, p25=p25)
        g1b_rows.append([patch, n, L, p0['edge'],
                         f'{e4(p0["vmc"])} +/- {e3(2 * p0["se"])}', e4(p0['vpp']), status_word(p0['status']),
                         f'{e4(p25["vmc"])} +/- {e3(2 * p25["se"])}', e4(p25['vpp']), status_word(p25['status']),
                         e4(sep), f'{p25["vm"]:.4f} +/- {p25["vmse"]:.1e}', e4(p25['pf']), e4(comb), f2(sep / comb),
                         '**pass**' if sep / comb >= 3 else '**fail**', '**pass**' if p25['pf'] < sep / 2 else '**fail**',
                         e3(err), '**pass**' if err < sep / 2 else '**fail**', f2(p0['vmc'] / SF4096)])
g1b_table = table(['patch', 'n', 'L', 'edge', 'p = 0 delay-matched V(k = L) +/- 2 sigma', 'p = 0 lower bound', 'p = 0 status',
                   'p = 0.25 reset V(k = L) +/- 2 sigma', 'p = 0.25 lower bound', 'p = 0.25 status', 'separation',
                   'Var_mask[C] (p = 0.25)', 'pattern floor Var_mask/(2K), K = 256', 'combined floor (shot + pattern)',
                   'separation / combined floor', '(b) separation >= 3x', '(d) pattern floor < half separation',
                   'truncation error', '(f) error < half separation', 'p = 0 reference / shot floor (4096)'], g1b_rows)

fall_rows = []
for rg in D30['rungs']:
    n = rg['n']
    v8, v12, fall = rg['var_p0_L8'], rg['var_p0_L12'], rg['fall']
    two200 = 2 * v8 * math.sqrt((KAPPA - 1) / 200)
    st = 'counted' if rg['counted'] else '**reference unresolvable at 4096 shots** (not counted)'
    res250 = '**pass**' if rg['passes'] else ('not counted' if not rg['counted'] else '**fail**')
    res350 = '**pass**' if rg['M350']['passes'] else ('not counted' if not rg['counted'] else '**fail**')
    fall_rows.append([rg['patch'], n, e4(v8), f2(rg['var_p0_L8_over_shot_floor']), e4(v12), e4(fall), f2(rg['fall_over_3sf']),
                      f'{e3(two200)} / {fall / two200:.2f}',
                      f'{e3(rg["draw_2sigma_L8_M250"])} / {rg["fall_over_2sigma"]:.2f}',
                      f'{e3(rg["M350"]["draw_2sigma_L8"])} / {rg["M350"]["fall_over_2sigma"]:.2f}',
                      rg['min_M_for_2sigma'], f'{rg["M350"]["kurtosis_upper_bound_for_2x"]:.1f}', st, res250, res350])
fall_table = table(['patch', 'n', 'p = 0 V(k = L), L = 8', 'L = 8 reference / shot floor', 'p = 0 V(k = L), L = 12', 'depth fall',
                    'fall / (3 x shot floor 3.662e-4)', 'L = 8 draw 2 sigma / fall over it, M = 200 (Dev. 29 record)',
                    'same, M = 250 (Dev. 30 as adopted)', 'same, M = 350 (Dev. 30 corrected, booked)',
                    'minimum M for 2x (M >= 17.5 (kappa - 1))', 'kappa covered at M = 350', 'rung status', 'passes (M = 250)',
                    'passes (M = 350)'], fall_rows)

# ----------------------------------------------------------------------------- dial grid n = 53
dial_rows = []
for L in (8, 12):
    for d_, p in (('delay', 0.0), ('dephase', 0.5), ('reset', 0.25), ('reset', 0.5)):
        r = dial[(L, d_, p)]
        dial_rows.append([L, d_, p, f'{e4(r["v1"])} +/- {e3(2 * r["se1"])}', f'{e4(r["vmc"])} +/- {e3(2 * r["se"])}', e4(r['vpp']),
                          f'{e4(r["vc"])} +/- {e3(2 * r["sec"])}', f'{r["mean"]:.3e}',
                          e4(r['pf']) if r['pf'] is not None else 'n/a (no masks)',
                          f'{r["vm"]:.4f}' if r['vm'] is not None else 'n/a', status_word(r['status'])])
dial_table = table(['L', 'dial', 'p', 'V(k = 1) +/- 2 sigma', 'V(k = L) +/- 2 sigma', 'V(k = L) lower bound', 'Var[C_mix] +/- 2 sigma',
                    'E[C_mix]', 'pattern floor Var_mask/(2K), K = 256', 'Var_mask[C]', 'status'], dial_rows)

# ----------------------------------------------------------------------------- exact grid (main)
grid_rows.sort(key=lambda r: (int(r['n']), int(r['L']), int(r['k']), MODELS.index(r['model'])))
grid_table = table(['model', 'patch', 'n', 'L', 'k', 'M', 'cone', 'method', 'variance', '95% CI', 'hi/lo', 'eps_N 4096', 'eps_N 16384', 's', 'note'],
                   [[r['model'], r['patch'], r['n'], r['L'], r['k'], r['M'], r['n_cone'], r['method'] + (' x32' if r['n_traj'] == '32' else ''),
                     f'{fl(r["var"]):.3e}', f'[{fl(r["ci_lo"]):.3e}, {fl(r["ci_hi"]):.3e}]', f'{fl(r["hi_lo"]):.2f}',
                     f'{fl(r["eps_N_4096"]):.2e}', f'{fl(r["eps_N_16384"]):.2e}', f'{fl(r["runtime_s"]):.0f}', r['note']] for r in grid_rows])
n_grid = len(grid_rows)
li_table = table(['n', 'L', 'M', 'r noiseless', 'r unital', 'r non-unital', 'R unital [95% CI]', 'R non-unital [95% CI]', 'D = R_nu - R_u [95% CI]', 'separated (D_lo > 0)'],
                 [[r['n'], r['L'], int(float(r['M'])), f3(fl(r['r_noiseless'])), f3(fl(r['r_unital'])), f3(fl(r['r_nonunital'])),
                   f'{fl(r["R_unital"]):.3f} [{fl(r["R_unital_lo"]):.3f}, {fl(r["R_unital_hi"]):.3f}]',
                   f'{fl(r["R_nonunital"]):.3f} [{fl(r["R_nonunital_lo"]):.3f}, {fl(r["R_nonunital_hi"]):.3f}]',
                   f'{fl(r["D"]):+.3f} [{fl(r["D_lo"]):+.3f}, {fl(r["D_hi"]):+.3f}]', r['separated']] for r in li_rows])
null_table = table(['n', 'edge', 'register', 'null qubit', 'N shots', 'Var_null', '95% CI', '1/(2N)', 'two-term floor', 'Var_null / (1/(2N))', 'mean grad +/- se', '10x allowance'],
                   [[r['n'], r['edge'], r['n_register'], r['null_parameter_qubit'], r['shots'], f'{fl(r["var_null"]):.3e}',
                     f'[{fl(r["ci_lo"]):.3e}, {fl(r["ci_hi"]):.3e}]', f'{fl(r["floor_analytic_1_over_2N"]):.3e}', f'{fl(r["floor_two_term_mean"]):.3e}',
                     f'{fl(r["ratio_var_to_analytic"]):.2f}', f'{fl(r["mean_grad"]):+.1e} +/- {fl(r["se_mean"]):.1e}', f'{fl(r["hardware_allowance_10x"]):.3e}'] for r in null_rows])

# ----------------------------------------------------------------------------- validation, pattern check
n_val = len(val_rows)
n_in = sum(1 for r in val_rows if r['inside_ci'] == 'True')
ref = [r for r in val_rows if r['source'].startswith('gate1_predictions')]
n_ref, n_ref_in = len(ref), sum(1 for r in ref if r['inside_ci'] == 'True')
n_fresh, n_fresh_in = n_val - n_ref, n_in - n_ref_in
pts = {(r['model'], r['dial'], r['patch'], r['L'], r['k']) for r in val_rows}
outside = [r for r in val_rows if r['inside_ci'] != 'True']
outside_txt = '; '.join(f'{r["patch"]} L = {r["L"]} k = {r["k"]} {r["model"]}: exact {fl(r["exact"]):.4e} [{fl(r["ci_lo"]):.3e}, {fl(r["ci_hi"]):.3e}], PP {fl(r["pp"]):.4e}' for r in outside)
p64 = next(r for r in pat_rows if r['K'] == '64'); p256 = next(r for r in pat_rows if r['K'] == '256')
ratio_pat = fl(p64['excess_var_exact']) / fl(p256['excess_var_exact'])
ratio_pat_err = ratio_pat * math.hypot(fl(p64['excess_var_se']) / fl(p64['excess_var_exact']), fl(p256['excess_var_se']) / fl(p256['excess_var_exact']))
pattern_table = table(['patch', 'n', 'L', 'p', 'M', 'K', 'excess gradient variance, exact masks', 'floor from exact Var_mask', 'floor from PP Var_mask', 'Var_mask exact', 'Var_mask PP'],
                      [[r['patch'], r['n'], r['L'], r['p'], r['M'], r['K'], f'{fl(r["excess_var_exact"]):.3e} +/- {fl(r["excess_var_se"]):.2e}',
                        f'{fl(r["floor_from_exact_varmask"]):.3e}', f'{fl(r["floor_from_pp_varmask"]):.3e}',
                        f'{fl(r["var_mask_exact"]):.4f} +/- {fl(r["var_mask_exact_se"]):.4f}', f'{fl(r["var_mask_pp"]):.4f} +/- {fl(r["var_mask_pp_se"]):.4f}'] for r in pat_rows])

# ----------------------------------------------------------------------------- placements
OLD = {'4x5': ('20, (8, 1), []', '93_103', '16'), '4x10': ('39, (8, 0), [107]', '94_95', '23'),
       '6x10': ('56, (0, 0), [17, 24, 49, 55]', '35_36', '13'), '8x10': ('71, (2, 0), [24, 49, 55, 61, 62, 63, 72, 73, 77]', '43_44', '13'),
       '10x10': ('90, (0, 0), [17, 24, 49, 55, 61, 62, 63, 72, 73, 77]', '43_44', '13')}
NEWCONE = {'4x5': '16', '4x10': '20', '6x10': '16', '8x10': '16', '10x10': '12'}
pl_rows = []
for patch in ['4x5', '4x10', '6x10', '8x10', '10x10']:
    p = placements['patches'][patch]
    broken = ', '.join(f'{k} ({v:.1e})' for k, v in p['broken_edge_cz_errors'].items()) or 'none'
    pl_rows.append([patch, OLD[patch][0], f'**{p["n"]}**, ({p["origin"][0]}, {p["origin"][1]}), {p["holes"]}', broken,
                    f'{OLD[patch][1]} -> {p["observable_edge"][0]}_{p["observable_edge"][1]} (CZ error {p["observable_edge_cz_error"]:.2e})',
                    f'{OLD[patch][2]} -> {NEWCONE[patch]}'])
pl_table = table(['patch', 'old rule: n, origin, holes', 'Deviations 22 + 26: n, origin, holes', 'broken couplers (CZ error)', 'observable edge (old -> new)', 'L = 2 cone qubits (old -> new)'], pl_rows)

# ----------------------------------------------------------------------------- scalars for the prose
c8 = [clause[(n, 8)]['ratio'] for n in (39, 53, 87)]
c12 = [clause[(n, 12)]['ratio'] for n in (39, 53, 87)]
m350 = [rg['M350']['fall_over_2sigma'] for rg in D30['rungs']]
m250 = [rg['fall_over_2sigma'] for rg in D30['rungs']]
minM = [rg['min_M_for_2sigma'] for rg in D30['rungs']]
kap_ub = [rg['M350']['kurtosis_upper_bound_for_2x'] for rg in D30['rungs']]
L12f = FIND['L12_all_below_shot_floor_4096']
L8f = FIND['L8_rows_below_criterion_d_10x_allowance']
below16384 = ', '.join(f'{r["model"]} n = {r["n"]} k = {r["k"]} ({r["var"]:.2e})' for r in L8f['rows_below_16384_allowance'])
maxL8 = max(dev[(n, 8, m)]['vmc'] for n, _ in PATCHES for m in MODELS)
statcount = collections.Counter(d['status'] for d in dev.values())
notconv = [f'{d["patch"]} L = {k[1]} {k[2]} ({(d["vmc"] - d["vpp"]) / d["vmc"] * 100:.0f}%)' for k, d in sorted(dev.items(), key=lambda kv: (kv[0][1], kv[0][0], MODELS.index(kv[0][2]))) if d['status'].startswith('not converged')]
a_note = CRIT['a']['note']
b_note = CRIT['b']['note']
c1 = CRIT['c']['part1']
d_note = CRIT['d']['note']
f_note = CRIT['f']['note']
part1_L8 = [p for p in c1['points'] if p['L'] == 8]
part1_L12 = [p for p in c1['points'] if p['L'] == 12]
part1_exact = [p for p in c1['points'] if p['source'] == 'exact']
pending_values += [
    'Gate 1b clause (e): predicted M = 100 interval widths for every core point ("still running", pre-registration v0.9.7 Gate 1b status)',
    'Criterion (c) part 2 at L = 8 / 12: paired-bootstrap interval of D (the propagation yields moments, not draws; only point estimates with independent 2 sigma exist)',
    'Large-cone L = 4 groups (n = 39 / 53 / 70 / 87, cones 36-72 qubits) and the cost-cut noisy groups (n = 20 L = 4, n = 39 L = 2): 32 points not computed by either method',
    'Gate 1b ratios under the ZZ-idle model: provisional until the per-edge ZZ coupling is added to the propagation (Deviation 30 correction, pre-Gate-2 action)',
    'Deviation 24 recompute of the Section 2 / 3b / 6 tables with the placed n: not yet done',
]

# ============================================================================= MARKDOWN
md = f"""# {TITLE}

Programme gradvar-phoenix (SSIT Tumakuru; Mohammed Owais, Dr. Raviram V, physics co-author to be decided). Pre-registration `{PREREG}`: Gate 1 criteria (a)-(f), Gate 1b, Deviations 15-30 (Deviation 30 with its second-review correction: p = 0 reference points at M = 350, rule M = 17.5 (1.3 kappa - 1); ZZ idle model as a pre-Gate-2 action). Source: `main` @ {MAIN_SHA} (branch `gate1-pauli-prop` merged at df0054e; 74 tests): `docs/GATE1_RESULTS.md`, `docs/PAULIPROP.md`, `data/predictions/gate1_summary.json` (re-summary of `scripts/gate1_resummary.py` including the propagation rows through `gradvar/pauliprop_summary.py`), `pauliprop_summary.json`, `pauliprop_predictions.csv`, `pauliprop_validation.csv`, `pauliprop_kurtosis.json`, `pauliprop_pattern_check.csv`, `gate1_predictions.csv`, `gate1_layer_index.csv`, `gate1_null_control.json`, `gate1_renyi.json`, `ladder_placements.json`, `figures/`. Verdict words are those of `gate1_summary.json` (pass / provisional pass / not-evaluated / reported); 2 sigma, deficits and ratios are recomputed from the file values; a value absent from the files is written "pending". Built by `scripts/build_gate1_report.py`.

## 1. Verdict

Gate 1 overall: **not-evaluated** (`gate1_summary.json` -> overall): "{summary['overall']}". Criterion by criterion: **(a)** **fail** as registered and **pass** under Deviation 25 ((a-i) max |g_sim - g_closed| = 1.8e-14 over n = 4..20; (a-ii) 9 of 9; (a-iii) 7 of 8 at seed 2026, the n = 20 point at the 2.4th percentile (0.043 against the 2.5% quantile 0.043) resolved by the seed-2027 replicate, 0.212 inside [0.043, 5.764]); the statevector is exact, the pre-registered estimator is not coverable at n >= 13 (kurtosis (3/2)^n). **(b)** **pass**: 0 of 41 points at M >= 200 exceed the Deviation 17 depth-dependent bound. **(c)** **not-evaluated**: part 1 **pass**, {c1['n_exceeding']} of {len(c1['points'])} (n, L) points exceed 2 x floor(16384) = 6.10e-5 at k = 1 ({len(part1_exact)} exact points and all five L = 8 propagation points; none of the five L = 12 points, whose unital - noiseless separations 3.52e-6 to 1.68e-5 are below the threshold, both models having collapsed); part 2 **not-evaluated**: the four paired D at L = 2 include 0, and at L = 8 / 12 the propagation gives point estimates of D with an independent (not paired) 2 sigma, |D| <= 0.02 at L = 8 with 2 sigma 0.06-0.09, which do not enter the result field. **(d)** **provisional pass** on the exact points (Var_null / (1/(2N)) = 0.74, 0.66, 0.85, 0.80; smallest exact noisy signal 7.25e-2 against the 10x allowance 1.22e-3 / 3.05e-4); the propagation rows are recorded as findings for the Gate 2 booking decision, not as a verdict: every L = 12 predicted variance ({L12f['min']:.1e} to {L12f['max']:.1e}) lies below the 4096-shot floor 1.22e-4, and at L = 8 the 10x allowance is 1.22e-3 at 4096 shots (above every L = 8 prediction, max {maxL8:.2e}) and 3.05e-4 at 16384 shots, below which lie the unital and non-unital k = L rows at n = 53 / 70 and the noisy k = 1 rows at n = 20 / 53 / 70 / 87. **(e)** **pass** on the {n_grid} exact points (eps_N(4096) < 1 everywhere); on the propagation rows eps_N(4096) > 1 at every L = 12 point (Section 6.4). **(f)** **reported**: L_s = 14 / 13 / 12 at n = 12 / 16 / 20, geometric, not extrapolated. **Gate 1b** (K = 256, Deviations 27-30): the separation clause and the pattern-floor clause **pass** at every rung at L = 8 (separation / combined floor {c8[0]:.2f} / {c8[1]:.2f} / {c8[2]:.2f} at n = 39 / 53 / 87) and L = 12 ({c12[0]:.2f} / {c12[1]:.2f} / {c12[2]:.2f}); the truncation error is below half the separation everywhere (clause (f)); clause (b), the unital-reference resolvability, was **amended three times before any hardware datum** (Deviation 28 -> 29 -> 30, history in Section 7) and is **frozen** pending PI review of rows 28-30; under the frozen Deviation 30 wording, per rung, rungs 39 and 87 **pass** (fall / 2 sigma {m250[0]:.2f} / {m250[2]:.2f} at M = 250, {m350[0]:.2f} / {m350[2]:.2f} at the booked M = 350) and rung 53 is **reference unresolvable at 4096 shots** (its L = 8 reference is {D30['rungs'][1]['var_p0_L8_over_shot_floor']:.2f} shot floors) and is not counted, so clause (b) passes 2 of 2 counted rungs and `pauliprop_summary.json` -> gate1b_booked_reading reads **pass**; the ratios are provisional until the ZZ idle phase is in the propagation model (Deviation 30 correction), and clause (e) is **pending**. The stop rule (failing (c) or (d)) is not triggered and not cleared; no allocation minute is booked on the strength of this report. The decisions this leaves for the PI are listed in Section 10.

## 2. Gate 1 criteria (a)-(f)

Thresholds and statistics as in pre-registration Section 4 and Deviations 14, 15, 17, 25; results and wording from `gate1_summary.json` @ {MAIN_SHA}; the last column carries the `propagation.findings` of the same file (recorded for the Gate 2 booking decision, not verdicts).

""" + table(['criterion', 'statistic', 'threshold', 'result (gate1_summary.json)', 'evidence file(s)', 'propagation rows (findings, not verdicts)'], [
    ['(a) chain regression', 'Var[d<Z_(n-1)>/d theta_0] of the Ry + CX chain, n = 4..20; Deviation 25: (a-i) per-draw identity |g_sim - g_closed|, (a-ii) percentile bootstrap at n <= 12 (M = 1000), (a-iii) exact null sampling distribution at n = 13..20 (M = 300, 10^4 replicates), replicate rule at seed 2027',
     'as registered: 2^-n inside the 95% bootstrap interval; Deviation 25: (a-i) < 1e-10, (a-ii) inside, (a-iii) inside the central 95%',
     '**fail** as registered, **pass** under Deviation 25: ' + a_note,
     '`figures/gate1_noiseless.csv`, `gate1_chain_identity.csv`, `gate1_chain_replicates.csv`; `gate1_summary.json` -> criteria.a', 'n/a'],
    ['(b) interval ratio', 'bootstrap hi/lo of the variance at M = 200 (10,000 resamples)', 'Deviation 17: < 1.5 at L = 1, < 2.0 at L = 2, < 2.5 at L >= 4 (1.5 where M >= 400 / 700)',
     '**pass**: ' + b_note, '`data/predictions/gate1_predictions.csv` (hi_lo); `gate1_summary.json` -> criteria.b',
     'not tested on the propagation rows (exact theta-averages, M = 0); the measured k = L kurtosis 14.24 at (n = 20, L = 8, M = 400) implies a relative draw 2 sigma of 0.515 at M = 200'],
    ['(c) part 1', '|Var_unital - Var_noiseless| at k = 1', '> 2 x 1/(2 x 16384) = 6.10e-5 at >= 6 (n, L) points of the 25-point ladder',
     '**pass**: ' + c1['note'] + f' [{len(part1_exact)} exact + {sum(1 for p in part1_L8 if p["exceeds_2floor"])} propagation at L = 8 of {len(c1["points"])}]', '`gate1_summary.json` -> criteria.c.part1; `docs/GATE1_RESULTS.md`',
     f'all five L = 8 points exceed the threshold (gaps {min(abs(p["unital_minus_noiseless"]) for p in part1_L8):.2e} to {max(abs(p["unital_minus_noiseless"]) for p in part1_L8):.2e}); no L = 12 point does (gaps {min(abs(p["unital_minus_noiseless"]) for p in part1_L12):.2e} to {max(abs(p["unital_minus_noiseless"]) for p in part1_L12):.2e}); Deviation 15 hardware-only flag only at 4x5, L = 12 (table 6.2)'],
    ['(c) part 2', 'D = R_nonunital - R_unital, R_m = [Var_m(k = L)/Var_m(k = 1)] / [same, noiseless]; paired bootstrap over shared draws (Deviation 14)', 'D_lo > 0 at n = 40 or 100, L = 8 / 12 (H3 is a consistency check with D = 0 since Deviation 16)',
     '**not-evaluated**: ' + CRIT['c']['part2']['note'], '`data/predictions/gate1_layer_index.csv`; `gate1_summary.json` -> criteria.c.part2',
     'point estimates with independent 2 sigma at every (n, L = 8 / 12) (table 6.3): |D| <= 0.02 at L = 8 (2 sigma 0.06-0.09); ' + FIND['criterion_c_part2_at_L12']],
    ['(d) null control', 'Var of the shot-sampled gradient of a parameter outside the light cone (L = 1, non-unital model, Aer readout confusion) against the smallest signal to be claimed', 'floor below the smallest signal, allowing a hardware floor up to 10x the analytic 1/(2N)',
     '**provisional pass**: ' + d_note, '`data/predictions/gate1_null_control.json` / `.csv`; `gate1_summary.json` -> criteria.d',
     CRIT['d']['propagation_note'] + '. Findings: ' + L12f['statement'] + '; ' + L8f['statement']],
    ['(e) resolvability', 'eps_N = Var_shot / (N Var_theta) per point', '< 1 at every point to be claimed',
     f'**pass**: ' + CRIT['e']['note'] + f'; 0 of {n_grid} exact points at or above 1', '`data/predictions/gate1_predictions.csv` (eps_N_4096, eps_N_16384)',
     'eps_N(4096) > 1 at every L = 12 propagation point (V / floor 0.04-0.54); at L = 8 V / floor(4096) is 1.63-9.81 (table 6.4)'],
    ['(f) Renyi-2 saturation depth', 'half-patch S_2(L) vs the Page value; L_s(n) = first L with mean S_2 >= 95% of Page (50 draws)', 'design check, no pass/fail threshold',
     '**reported**: ' + f_note, '`data/predictions/gate1_renyi.json`, `figures/gate1_renyi.png` / `.csv`', 'n/a'],
    ['overall', 'Section 4 stop rule: failing (c) or (d) stops the hardware stage', '', '**not-evaluated**: ' + summary['overall'], '`data/predictions/gate1_summary.json`',
     f'{summary["propagation"]["grid_after_propagation"]["n_points_computed"]} points computed, {summary["propagation"]["grid_after_propagation"]["n_points_deferred"]} deferred: ' + summary['propagation']['grid_after_propagation']['remaining_deferred']],
]) + f"""

## 3. Ladder placements: old rule vs Deviations 22 + 26

The ladder is **n = 20 / 39 / 53 / 70 / 87** on the 19 Sep 19:25Z snapshot (`ibm_phoenix_2026-09-19T192510Z.csv`, raw properties `ibm_phoenix_properties_20260919T192510Z.json.gz`); it was 20 / 39 / 56 / 71 / 90 under the old rule. Excluded qubits: {placements['excluded']}. Rules (`ladder_placements.json`): fixed cluster {placements['rules']['fixed']}, readout cut {placements['rules']['readout_cut']}, initialisation-error cut {placements['rules']['init_error_cut']}, |ZZ| cut {placements['rules']['zz_cut_mhz']} MHz to an excluded or dead qubit, CZ cut {placements['rules']['cz_cut']}.

""" + pl_table + f"""
**Why (Deviation 22).** The exclusion rule gained two criteria read from the raw `backend.properties()`: (i) |ZZ| >= 1 MHz to an excluded or dead qubit and (ii) initialisation error >= 5e-4. On the 19:25Z properties this adds 18 and 27 (ZZ -5.0 / +4.3 MHz to dead qubit 17; median |ZZ| 27 kHz) and 8, 11, 22, 59 (initialisation error 1.8e-3 / 5.8e-4 / 4.3e-3 / 6.2e-4 against a 2e-5 median). Deviation 22's original text named only 22 and 27 and said the L <= 4 cones were unchanged; the independent review (`gate1_grid_review.md`, MAJOR-1) showed that qubit 27 lay in the old 6x10 L = 2 cone and qubit 22 in the old 8x10 and 10x10 L = 2 cones, so the first-pass n = 56 / 71 / 90 points were computed on qubit sets the hardware will not use. They are kept in `gate1_predictions_oldrule.csv` and `pauliprop_predictions_old_placement.csv` as a labelled first pass, not as predictions.

**Why (Deviation 26).** Every coupler of a placed patch must have CZ error < 5e-3; a coupler above the cut is a broken edge (no CZ applied; ansatz, light cone and noise model skip it) and the observable edge must be intact. On the snapshot 36 of 218 couplers are at or above 5e-3, 10 of them between non-excluded qubits. The 4x10 patch keeps its qubits but loses (86,87), (87,97), (95,96) [3.1e-2, on observable qubit 95], (100,101) [6.3e-2] and (100,110), which is what made its first-pass unital variance anomalously low (review item 7: with (95,96) at the median the L = 4 unital/noiseless ratio moves from 0.55 to 0.79). The 6x10 and 8x10 patches move to origins (6,0) and (4,0) and share the observable edge 84_85 and the same 16-qubit L = 2 cone, so their L <= 2 rows are identical by construction; they differ from L = 3 on (cones 53 vs 65 qubits at L = 4; 53 vs 70 at L >= 8).

## 4. Exact light-cone results, L <= 4

Method (`scripts/gate1_ladder.py`): exact `density_matrix` for cones <= 10 qubits (the noisy L = 1 points use the 8-qubit edge-plus-neighbours register so the last layer's CZ channels on the observable qubits are included), 32 noise trajectories on Aer `statevector` up to 24 cone qubits, statevector for noiseless points; M = 200 (M = 100 for the 23-qubit noiseless 4x10 L = 2 cone, excluded from (b)); seed 2026; 10,000 bootstrap resamples. All {n_grid} exact-feasible points were computed under Deviations 22 + 26 (commit c103d95, none time-capped). Cone sizes: 4x5 L = 1/2/4: 2/16/20; 4x10: 2/20/36; 6x10: 2/16/48; 8x10: 2/16/65; 10x10: 2/12/72. Every noiseless L = 1 value is 2.421e-1 because the L = 1 cone is the bare edge.

### 4.1 Grid

""" + grid_table + f"""
### 4.2 The four paired non-unital differences (criterion (c) part 2, Deviation 14)

r_m = Var_m(k = L) / Var_m(k = 1), R_m = r_m / r_noiseless, D = R_nonunital - R_unital; paired bootstrap over the same 200 draws, 10,000 resamples; "separated" means D_lo > 0. The n = 53 and 70 rows are the same computation (shared edge and cone, Section 3).

""" + li_table + f"""
None of the four is separated; at L = 2 the predicted |D| is at the 1e-2 level against an interval half-width of about 0.02, consistent with Deviation 16's reclassification of H3 as a consistency check. The L = 8 / 12 pairs are covered by the propagation point estimates (Section 6.3).

### 4.3 Null control (criterion (d))

""" + null_table + f"""
The ratio below 1 is expected: at L = 1, E[<Z_i Z_j>^2] is about 1/4, so the exact two-term floor is about 0.78/(2N) and 1/(2N) is the ev = 0 upper bound.

## 5. Pauli-propagation method (`gradvar/pauliprop.py`)

The quantity is Var_theta[d<O>/d theta_(k,q)] and Var_theta[<O>] for theta uniform on [0, 2 pi)^(nL), with O the readout-folded Z_i Z_j on the interior edge and q the first observable qubit. Back-propagating O through the transpiled noisy circuit (`ry = rz sx rz(pi + theta) sx rz`, calibration error after every `sx` and `cz`, 68 ns idle relaxation per CZ sub-layer for the non-unital model) writes <O> as a sum over Pauli paths whose theta-dependence is a product of 1 / cos / sin factors; because E[cos^2] = E[sin^2] = 1/2 and every cross term averages to zero, the second moment is a positive linear map on squared coefficients over Pauli strings (a rotation about axis A sends P not in {{I, A}} to 1/2 on each of the two other Paulis; Cliffords permute; a single-qubit channel r -> D r + t sends P_a to D_a^2 P_a and t_a^2 to I), and the derivative keeps the paths that do not commute with the generator at gate (k, q). Every channel parameter is read from the Pauli-transfer matrices of the very `NoiseModel` objects of `gradvar.noise`, including Aer's composition order; the reset dial is N_p = p Reset + (1 - p) Idle(400 ns) with D = (1 - p)(e^(-400/T2), e^(-400/T2), 1) and t_z = p on top of the snapshot unital noise, the delay-matched control is p = 0, the dephasing dial has t = 0. Two engines run on one op program: a deterministic truncation by coefficient (delta = 1e-7 and 1e-6, cap 4e5 strings) whose result is a rigorous lower bound V_trunc <= V, and an unbiased Pauli-path Monte Carlo (N = 2e6 paths) with a standard error. The prediction is V_MC +/- 2 sigma; the truncation error is the deficit V_MC - V_trunc; the Deviation 15 error is max(2 sigma, V_MC - V_trunc); `status` is `converged` (sampled value, deficit < 10%, 2 sigma < 5%), `sampled, trunc. deficit < 10%` (2 sigma above 5%, quote the one-sided interval [V_trunc, V_MC + 2 sigma]) or `not converged (truncation deficit >= 10%)` (the sampled value with its 2 sigma is the prediction, the truncated value its lower bound). The pattern-noise floor Var_mask[C] / (2K) comes from a sampled propagation with a fresh reset mask per path and layer. The recorded discarded mass (0.5-0.9 at L >= 8) is a diagnostic, not an error bound. Known model gaps (`docs/PAULIPROP.md`): the ZZ phase between neighbours during the 400 ns dial idle (about 1e-4 weight per pair per layer; Deviation 30 correction estimates a 10-20% effect on the p = 0 L = 8 reference and makes adding it a pre-Gate-2 action) and T1 on the idle branch (t_z about 2e-3 per layer) are not modelled; two Z -> I relaxation branches separated by a CZ are treated as distinct paths (relative < 1e-3, positive, below the sampler's 2 sigma). Runtime: median 176 s, max 444 s per point on one core; 175 core-minutes for the 50 points.

**Validation** (`pauliprop_validation.csv`, `tests/test_pauliprop.py`, review `gate1_pauliprop_review.md`): (i) on a 2x2 patch at L = 2 the propagation reproduces the exact uniform average on a 3-point angle grid to 1e-6 relative for the noiseless and reset-dial rules and 3e-5 for the non-unital model; (ii) **{n_in} of {n_val} rows ({len({k for k in pts})} distinct points, {len({k for k in pts}) - 2} of them inside; the L = 1 rows appear twice, once per k)** lie inside the 95% bootstrap interval of the exact M = 200 estimate: {n_ref_in} of {n_ref} against the frozen n = 12 / 16 reference rows (`pauliprop_reference_exact.csv`) and {n_fresh_in} of {n_fresh} against fresh exact density-matrix rows at n <= 10 (2x4, 2x5; non-unital, reset p = 0.25 / 0.5, dephasing p = 0.5, delay p = 0; L = 3-4), e.g. 2x4 L = 4 non-unital k = 1 exact 1.9468e-2 [1.495e-2, 2.447e-2] vs PP 2.3640e-2, MC 2.3777e-2 +/- 1.3e-4; the two outside miss by less than 5% of the interval width ({outside_txt}). (iii) The sampler was reproduced independently at 4x5 L = 8 noiseless with two seeds (4.86e-4 +/- 1.8e-5, 5.00e-4 +/- 1.9e-5 vs CSV 4.98e-4 +/- 5.8e-6). (iv) Exact pattern-floor check (`pauliprop_pattern_check.csv`; 2x3, L = 4, p = 0.25, M = 60 draws, K = 64 and 256):

""" + pattern_table + f"""
The ratio of the exact excess variances at K = 64 and K = 256 is {ratio_pat:.2f} +/- {ratio_pat_err:.2f} against the expected 4 (the 1/K scaling behind Deviation 27), and the propagated Var_mask {fl(p64['var_mask_pp']):.4f} agrees with the exact {fl(p64['var_mask_exact']):.4f} +/- {fl(p64['var_mask_exact_se']):.4f}. Measured k = L gradient kurtosis (`pauliprop_kurtosis.json`): {KAPPA:.2f} at ({kurt['patch']}, n = {kurt['n']}, L = {kurt['L']}, k = {kurt['k']}, noiseless, M = {kurt['M']}; variance {kurt['var']:.3e} [{kurt['ci_lo']:.3e}, {kurt['ci_hi']:.3e}]), against 8.4 assumed since Deviation 17; implied relative draw 2 sigma at M = 200: {kurt['rel_2sigma_M200']:.3f}; sampling error on kappa 20-30% (Deviation 29).

## 6. Deviation 15 predictions: L = 8 and L = 12, five patches, three models

Placements from `ladder_placements.json` (Deviations 22 / 26; calibration `ibm_phoenix_2026-09-19T192510Z.csv`). Of the 30 rows, {statcount['converged']} are `converged`, {statcount.get('sampled, trunc. deficit < 10%', 0)} `sampled` (deficit < 10%, 2 sigma above 5%, all at L = 12) and {sum(v for k, v in statcount.items() if k.startswith('not converged'))} `not converged` on the 10% deficit rule ({', '.join(notconv)}); every row carries a sampled value and a lower bound, so none is pending. The first-pass rows on the old placements (n = 56 / 71 / 90) are archived in `pauliprop_predictions_old_placement.csv` and are not predictions.

### 6.1 L = 8

""" + dev15_tables[8] + f"""
### 6.1b L = 12

""" + dev15_tables[12] + f"""
### 6.2 Deviation 15 rule and criterion (c) part 1 at k = 1

A point whose error exceeds half the unital-vs-noiseless separation is designated hardware-only (criterion (c) judged on the exactly computable points; the hardware result reported as exploratory). Error = max over the noiseless and unital rows of max(2 sigma, V_MC - V_trunc). Flags as in `pauliprop_summary.json` -> dev15 and `gate1_summary.json` -> propagation.findings.deviation_15_hardware_only_flags.

""" + dev15_rule_table + f"""
{FIND['criterion_c_part2_at_L12']}; the hardware-only column is the Deviation 15 rule applied literally and does not make the L = 12 points confirmatory.

### 6.3 Layer-index ratios from the propagation rows (criterion (c) part 2; point estimates, not paired)

From `gate1_summary.json` -> criteria.c.part2.propagation_point_estimates. The propagation yields moments, not draws, so there is no paired bootstrap; the 2 sigma treats the three models as independent and is wider than a paired interval would be. These values do not change the (c) part 2 result field.

""" + li_pp_table + f"""
### 6.4 Predictions against the shot floors (findings for criteria (d) and (e); computed from the rows)

""" + floor_table + f"""
## 7. Gate 1b at K = 256, per rung (Deviations 27-30)

Rows `stage = gate1b` of `pauliprop_predictions.csv`: snapshot unital noise plus the reset dial on the Deviation 22 / 26 placements; k = L; p = 0 is the delay-matched control (no masks, its own floor is the shot floor), p = 0.25 the reset dial with K = 256 masks x 16 shots (Deviation 27). Shot floor 1/(2 x 4096) = 1.221e-4; combined floor = shot + pattern floor of the p = 0.25 series. Clause letters follow Gate 1b in the pre-registration. `pauliprop_summary.json` -> gate1b_booked_reading: separation clause L = 8 {BOOKED['separation_clause_L8']}, L = 12 {BOOKED['separation_clause_L12']}, fall clause (Deviation 30) {BOOKED['fall_clause_deviation_30']}, overall **{'pass' if BOOKED['passes'] else 'fail'}** (a prediction under the frozen Deviation 30 wording, margins in the two tables below; not a hardware result).

""" + g1b_table + f"""
**Clause (b), depth-fall part (Deviations 29-30), per rung.** The delay-matched p = 0 variance at L = 12 must lie below its L = 8 value by more than 3x the shot floor (3.662e-4) and more than 2x the L = 8 point's draw 2 sigma at the booked M with the measured kurtosis kappa = {KAPPA:.2f} (2 sigma = 2 V sqrt((kappa - 1)/M)); a rung whose L = 8 reference lies below 3 shot floors is "reference unresolvable at 4096 shots" and is not counted; the clause passes if at least two of the three rungs pass. The booked M is 350 (Deviation 30 correction: M >= 17.5 (1.3 kappa - 1) rounded up, 306 at kappa = 14.2; M = 350 keeps the 2x condition up to kappa about 21); M = 250 is Deviation 30 as first adopted and M = 200 the Deviation 29 record.

""" + fall_table + f"""
**Deviation 30 booked reading** (`pauliprop_summary.json` -> deviation_30; pre-registration row 30 with its correction): rungs 39 and 87 counted and passing (fall / 2 sigma {m250[0]:.2f} / {m250[2]:.2f} at M = 250, {m350[0]:.2f} / {m350[2]:.2f} at M = 350; 3-shot-floor part {D30['rungs'][0]['fall_over_3sf']:.2f}x / {D30['rungs'][2]['fall_over_3sf']:.2f}x), rung 53 unresolvable ({D30['rungs'][1]['fall_over_3sf']:.2f}x three shot floors; its L = 8 reference is {D30['rungs'][1]['var_p0_L8_over_shot_floor']:.2f} shot floors), **{D30['n_passing']} of {D30['n_counted']} counted rungs pass**; minimum M for 2x {minM[0]} / {minM[1]} / {minM[2]}, kappa covered at M = 350 up to {kap_ub[0]:.1f} / {kap_ub[1]:.1f} / {kap_ub[2]:.1f}. The pre-registration's status sentence gives the same reading (2.5 at M = 350, 2.1 at M = 250, 1.86 / 1.90 / 1.88 at M = 200). Under Deviation 29 as written (M = 200) the clause reads fail (fall / 2 sigma below 2 on every rung); that reading is kept in the JSON for the record.

**Clause (b) history, stated plainly.** The clause has been amended three times before any hardware datum, each time because prediction showed the previous wording unresolvable on the re-placed patches: Deviation 28 (per-series floors: the n-ladder fall 7.84e-4 - 3.99e-4 = 3.85e-4 at L = 8 was 3.2x the shot floor but 6% short of the combined floor it had wrongly been held to; M = 500 booked for the p = 0 ladder points), Deviation 29 (the measured kurtosis 14.2 instead of the assumed 8.4 makes the n-ladder fall a 1.51x measurement even at M = 500, M >= 881 would be needed; the p = 0 series is non-monotone across the ladder because the 39- and 87-qubit patches carry 5 and 7 broken couplers; replaced by the depth fall at fixed n, predicted margin above 20 sigma), Deviation 30 (M = 250 from kappa = 14.2, per-rung evaluation, 2 of 3; second-review correction: the minimum-M arithmetic omitted the (1 - V12/V8) factor, so M >= 17.5 (kappa - 1) = 232, and M = 250 had only an 8% margin in kappa against a 20-30% sampling error and an unmodelled ZZ idle phase worth 10-20% on the p = 0 L = 8 reference; the six p = 0 reference points are booked at M = 350, about 6.2 min at 1 us, core about 63.5 min against the 65-minute line). The separation clause and the pattern-floor clause have passed at every point under every wording; with the pre-registered K = 64 design the pattern floor alone was about 1.1e-3 and the separation-to-floor ratios 1.03-1.37 (`pauliprop_summary.json` -> gate1b_K64), a failure at every point, which Deviation 27 repaired by K = 256 at unchanged shot count. Clause (b) is frozen from Deviation 30 until the PI reviews rows 28-30; rows 29 and 30 ask for specific countersignature. Clause (c) (move the ladder to L = 12) is not triggered; at L = 12 the p = 0 reference (V / shot floor {clause[(39, 12)]['p0']['vmc'] / SF4096:.2f} / {clause[(53, 12)]['p0']['vmc'] / SF4096:.2f} / {clause[(87, 12)]['p0']['vmc'] / SF4096:.2f}) is below the shot floor, so the ladder is booked at L = 8 and L = 12 is the H6 inconclusive-reference branch. Clause (e) (predicted M = 100 interval widths for every core point) is **pending** ("still running", pre-registration Gate 1b status).

## 8. Dial-grid predictions at n = 53 (Section 3b grid) and the H5-H7 signatures

Rows `stage = dial` of `pauliprop_predictions.csv`: the 6x10 patch (n = 53, edge 84_85, Deviations 22 / 26), snapshot unital noise plus the dial channel after every layer; L = 8 and 12; reset p = 0.25 and 0.5 (K = 256), dephasing p = 0.5 (unital, t = 0), delay-matched p = 0. The p = 0 and p = 0.25 rows are the same computation as the Gate 1b rows on this patch.

""" + dial_table + f"""
Reference lines: the Corollary 6 lower bound p^4/9 for |P| = 2 (Deviation 21): 4.3e-4 at p = 0.25, 6.9e-3 at p = 0.5; shot floor 1/4096 = 2.44e-4 on Var[C_mix], 1/(2 x 4096) = 1.22e-4 on the gradient. E[C_mix] = a_i a_j p^2 + (a_i b_j + a_j b_i) p + b_i b_j is the readout-folded p^2 (0.0658 / 0.252 at p = 0.25 / 0.5), the free pipeline check.

**Signatures implied.** H5 (cost-variance floor): Var[C_mix] is {dial[(8, 'reset', 0.25)]['vc']:.3e} at p = 0.25 and {dial[(8, 'reset', 0.5)]['vc']:.3e} at p = 0.5 at L = 8, and the same to three figures at L = 12 ({dial[(12, 'reset', 0.25)]['vc']:.3e}, {dial[(12, 'reset', 0.5)]['vc']:.3e}), i.e. 8.3x and 2.6x the p^4/9 bound and flat in L, against a delay-matched p = 0 Var[C] of {dial[(8, 'delay', 0.0)]['vc']:.3e} (L = 8) falling to {dial[(12, 'delay', 0.0)]['vc']:.3e} (L = 12); H5 is tested against this pre-drawn curve, with the 2-design bound drawn as a line (Deviation 21). H6 (layer-index dependence): the k = L variance at p = 0.25 is flat at {dial[(8, 'reset', 0.25)]['vmc']:.3e} (L = 8) and {dial[(12, 'reset', 0.25)]['vmc']:.3e} (L = 12), and across the ladder 1.99e-3 to 2.09e-3 (Section 7), at p = 0.5 at {dial[(8, 'reset', 0.5)]['vmc']:.3e} at both depths, while the k = 1 variance collapses ({dial[(8, 'reset', 0.25)]['v1']:.2e} at L = 8 and {dial[(12, 'reset', 0.25)]['v1']:.2e} at L = 12 for p = 0.25; {dial[(8, 'reset', 0.5)]['v1']:.1e} and {dial[(12, 'reset', 0.5)]['v1']:.1e} for p = 0.5) and the delay-matched p = 0 reference falls from {dial[(8, 'delay', 0.0)]['vmc']:.3e} to {dial[(12, 'delay', 0.0)]['vmc']:.3e}, a factor {dial[(8, 'delay', 0.0)]['vmc'] / dial[(12, 'delay', 0.0)]['vmc']:.0f}; the dephasing dial at p = 0.5 (unital, t = 0) gives k = L {dial[(8, 'dephase', 0.5)]['vmc']:.2e} at L = 8 and {dial[(12, 'dephase', 0.5)]['vmc']:.1e} +/- {2 * dial[(12, 'dephase', 0.5)]['se']:.1e} at L = 12, i.e. no floor, which is the unital reference H6 needs. H7 (noise-induced effective depth) is read from the truncation arm and the k = 1 collapse; the H6 ladder claim is made against the pre-drawn curve, which is non-monotone in n at p = 0 (n = 53 lowest, Section 7) because of the broken-coupler pattern. All dial-channel numbers are provisional until the ZZ idle phase is in the model (Deviation 30 correction).

## 9. Budget consequences already recorded

* **Deviation 24** (Marrakesh pipeline check, 22 s charged vs 12.2 s predicted): the per-job model gains 10 us of acquisition per execution, t_meas from the target (2.684 us Marrakesh, 1.94 us Phoenix to be confirmed) and the TREX learning term 32 x shots x n_bases at resilience >= 1 (back-prediction 21.1 s); the ibm_phoenix smoke test re-budgets to about 5.0 min at 250 us (0.5 min at 1 us), the Paper 1 grid to about 1,260 / 170 / 80 min at 250 / 20 / 1 us; ibm_phoenix's measured default rep_delay is 1.0 us (Deviation 23 criterion (a), commit 127337d), so the grid is booked at 1 us; the Section 2 / 3b / 6 tables are to be recomputed under this model before Gate 2.
* **Deviation 27** (K = 256) and the Deviation 30 correction: 51,200 distinct circuits per gradient point, 171 jobs at max_experiments 300, about 5.7 min of job overhead per gradient point at any rep_delay (about 46 min for the eight core points, 5.7 min for the truncation pair); the six p = 0 reference points at M = 350 cost about 6.2 min at 1 us; the dial core is about 63.5 min at 1 us against the 65-minute Section 6 line (about 100 min at 250 us, so bookable only at the fast default); ledger 200 + 65 + 45 + 50 = 360 with the 10-minute dry run drawn from the reserve; predicted usage at 1 us about 80 + 63.5 + 2.7 + 10 = 156 of 360; contingent items about 33 min at 1 us.

## 10. Gate 2 booking decisions for the PI, and follow-ups

These are decisions, not verdicts; the Gate 1 verdict words stand as in Section 2.

1. **The L = 12 rung at the pre-registered shots.** {L12f['statement']} (`gate1_summary.json` -> propagation.findings), so the L = 12 rung is unresolvable at 4096 shots (eps_N > 1 everywhere, Section 6.4) and criterion (c) part 2 is unresolvable there whatever the truncation. Decide whether the L = 12 rung is booked at all, at more shots, or reported as the inconclusive branch.
2. **Shots per point at L >= 8, or the allowance factor.** At L = 8 the criterion (d) 10x allowance is {L8f['allowance_10x_4096']:.2e} at 4096 shots, above every L = 8 prediction (max {maxL8:.2e}), and {L8f['allowance_10x_16384']:.2e} at 16384 shots, below which lie {below16384}. Shots per point at L >= 8 (4096 vs 16384 or more) or the allowance factor must be decided before (d) and the stop rule can be judged on the points to be claimed.
3. **Gate 1b clause (b): history and margins.** Deviations 28 -> 29 -> 30 (frozen; Section 7): the booked M = 350 covers kappa <= about 21 on the counted rungs; the ZZ idle phase is unmodelled and worth 10-20% on the p = 0 L = 8 reference, and rung 53 is unresolvable at 4096 shots (its L = 8 reference is 2.3 shot floors). The per-edge ZZ coupling (raw-properties median 27 kHz, Deviation 22) goes into the propagation model before Gate 2 (Deviation 30 correction, pre-Gate-2 action); the Gate 1b ratios are provisional until then. Clause (e) (M = 100 interval widths) is still to be predicted.
4. **The large-cone L = 4 groups and the cost-cut noisy points.** 32 points remain deferred: L = 4 at n = 39 / 53 / 70 / 87 (cones 36-72 qubits; about 30 core-minutes through the propagation) and the cut noisy groups n = 20 L = 4 and n = 39 L = 2 (statevector-feasible but 63 min to > 4 h per point). Until they exist the grid is not the complete ladder and the overall Gate 1 field stays not-evaluated.
5. **Deviation 24 table recompute before Gate 2**: Section 2 point counts, the Section 3b table and the 200 / 65 / 45 lines under the corrected model with the actual placed n; the runner's `estimate_budget` takes t_meas from the target and the 32-randomisation TREX term.
6. **PI countersignature of Deviations 21-30**, with 29 and 30 for specific countersignature (clause (b) history; the Deviation 30 correction is covered by the same request); Deviation 25 (criterion (a)) and Deviation 18's recorded counts (20 / 39 / 53 / 70 / 87) are among them.

Follow-ups that do not gate: kurtosis re-measurement at M = 1000 (optional; kappa = 14.24 at M = 400 carries 20-30% sampling error, and M = 350 already covers kappa <= 21); idle-T1 on the dial's non-reset branch (t_z about 2e-3 per layer, two orders below the dial's t_z = p) stays unmodelled and recorded in `docs/PAULIPROP.md`; the two noiseless 4x10 L = 2 points at M = 100 are listed but not tested in (b) and should be rerun at M = 200 if they are to be claimed (`predict.criterion_b_bound` returns 2.0 at L = 2 for any M < 400; review MINOR-5); a 2x10 vs 2x10 cut of the 4x10 patch would be the relevant criterion (f) design check for n = 39 (39-qubit statevector, not feasible here).

## 11. Sources

* Pre-registration: `scratchpad/prereg/preregistration_q1.html` (v0.9.7, 19-20 Sep 2026; Section 3b Gate 1b, Section 4 Gate 1, Section 6 budget, Deviations 14-30 with the Deviation 30 correction).
* Reviews: `scratchpad/review/gate1_grid_review.md` (branch `gate1-grid` @ 038fba2; MAJOR-1 Deviation 22 cones, MAJOR-2 criterion (a) estimator, MINOR-1..5), `scratchpad/review/gate1_pauliprop_review.md` (branch `gate1-pauli-prop` @ 58f52b8, pass 1; MAJOR-1 reference rows, MAJOR-2 error statement; derivation, noise rules, dial, truncation bound, sampler, validation, n = 39 anomaly, compliance), `scratchpad/review/prereg_v05_review.md` (BLOCKER-1 p^4/9; MAJOR-1..6), `scratchpad/review/marrakesh_postrun_review.md` (D1 budget model, D2 layout re-check, D3-D7); the second review of the propagation branch (Deviation 30 correction, status labels, validation count).
* Commits on `main`: [df0054e]({GH}/commit/df0054e) merge `gate1-pauli-prop` (Deviation 15 L = 8 / 12, Gate 1b under Deviations 27 + 30, dial grid, re-summary); [af087ab]({GH}/commit/af087ab) Gate 1 re-summary with the propagation rows; [0c9cebe]({GH}/commit/0c9cebe) validation count as in the CSV; [0a6dbf3]({GH}/commit/0a6dbf3) second-pass minors (status labels, Deviation 30 minimum M 232 and M = 350 reading); [36e9fa0]({GH}/commit/36e9fa0) final propagation tables, summary JSON, figure, docs; [bd73e12]({GH}/commit/bd73e12) exact half regenerated with the Deviation 25 replicate rule; [c103d95]({GH}/commit/c103d95) ladder resume complete, 43 exact points; [6fd9f57]({GH}/commit/6fd9f57) merge `gate1-grid` (Deviations 22, 25, 26; ladder 20/39/53/70/87); [bd15cd9]({GH}/commit/bd15cd9) Deviation 26 layout re-check; [02ab608]({GH}/commit/02ab608) post-run fixes D1-D5 (budget model v2); branch history [8105572]({GH}/commit/8105572), [7d040ad]({GH}/commit/7d040ad), [5cfadc5]({GH}/commit/5cfadc5), [cee728a]({GH}/commit/cee728a), [e58d704]({GH}/commit/e58d704), [604d6c2]({GH}/commit/604d6c2), [0d3b1cc]({GH}/commit/0d3b1cc).
* Data and figures (`main` @ {MAIN_SHA}): `data/predictions/gate1_summary.json`, `gate1_predictions.csv`, `gate1_layer_index.csv`, `gate1_null_control.json`, `gate1_renyi.json`, `gate1_ladder_schedule.json`, `ladder_placements.json`, `gate1_predictions_oldrule.csv`, `pauliprop_predictions.csv`, `pauliprop_predictions_old_placement.csv`, `pauliprop_reference_exact.csv`, `pauliprop_validation.csv`, `pauliprop_summary.json`, `pauliprop_kurtosis.json`, `pauliprop_pattern_check.csv`; `figures/gate1_noiseless.png`, `gate1_predictions.png`, `gate1_renyi.png`, `pauliprop_predictions.png`; `docs/GATE1_RESULTS.md`, `docs/PAULIPROP.md`.

### Values marked pending in this report

""" + '\n'.join(f'* {p}' for p in pending_values) + '\n'


# ============================================================================= HTML
STATUS_WORDS = {
    'pass': 'pass', 'fail': 'fail', 'pending': 'pending', 'not-evaluated': 'neutral', 'provisional pass': 'prov', 'reported': 'rep',
    'converged': 'pass', 'sampled': 'prov', 'not converged': 'prov', 'lower bound only': 'prov', 'hardware-only': 'prov',
    'frozen': 'neutral', 'no': 'neutral', 'reference unresolvable at 4096 shots': 'neutral',
    'amended three times before any hardware datum': 'neutral',
}


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)

    def bold(m):
        w = m.group(1)
        key = w.strip()
        if key in STATUS_WORDS:
            return f'<span class="st" data-status="{STATUS_WORDS[key]}">{w}</span>'
        m2 = re.match(r'^(\d+) of (\d+) counted rungs pass$', key)
        if m2:
            return f'<span class="st" data-status="pass">{w}</span>'
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
        out.append(f'<p>{inline(" ".join(para))}</p>')
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
#s1 p{max-width:92ch;font-size:15.5px}
li{max-width:88ch;margin:0 0 6px}
ul,ol{padding-left:1.3em;margin:0 0 14px}
code{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;font-size:.88em;background:var(--code-bg);padding:1px 5px;border-radius:4px;color:var(--ink)}
a{color:var(--accent-ink)}
.tw{overflow-x:auto;margin:6px 0 18px;border:1px solid var(--line);border-radius:6px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:12.6px;font-variant-numeric:tabular-nums;font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}
thead th{position:sticky;top:0;background:var(--surface);color:var(--muted);font-weight:500;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:12px;letter-spacing:.01em;white-space:nowrap;z-index:1}
tbody td{padding:6px 10px;border-bottom:1px solid var(--line-soft);vertical-align:top;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:var(--accent-soft)}
#s2 tbody td,#s10 td,#s11 td{white-space:normal;min-width:12ch}
#s2 tbody td:nth-child(2),#s2 tbody td:nth-child(3),#s2 tbody td:nth-child(4),#s2 tbody td:nth-child(6){min-width:28ch}
#s2 table,#s3 table{font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:13px}
#s3 tbody td{white-space:normal}
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
<div class="eyebrow">gradvar-phoenix &middot; Gate 1 &middot; pre-registration v0.9.7</div>
<h1>{html.escape(TITLE)}</h1>
<div class="meta">
  <span>main <b>@ {MAIN_SHA}</b></span>
  <span>snapshot <b>ibm_phoenix 2026-09-19T192510Z</b></span>
  <span>ladder <b>n = 20 / 39 / 53 / 70 / 87</b></span>
  <span>for Owais, Dr. Raviram V, the theorist</span>
</div>
<div class="chips">
  <span class="chip"><span class="st" data-status="neutral">not-evaluated</span> Gate 1 overall (large-cone L = 4 groups deferred)</span>
  <span class="chip"><span class="st" data-status="pass">pass</span> (a) under Dev. 25 &middot; (b) &middot; (c) part 1 &middot; (e)</span>
  <span class="chip"><span class="st" data-status="prov">provisional pass</span> (d)</span>
  <span class="chip"><span class="st" data-status="neutral">not-evaluated</span> (c) part 2</span>
  <span class="chip"><span class="st" data-status="rep">reported</span> (f)</span>
  <span class="chip"><span class="st" data-status="pass">pass</span> Gate 1b booked reading (Dev. 30: 2 of 2 counted rungs; clause (b) frozen)</span>
  <span class="chip"><span class="st" data-status="pending">pending</span> {len(pending_values)} listed pending values (Section 11)</span>
</div>
<nav class="toc" aria-label="Sections">
  <a href="#s1">1 Verdict</a><a href="#s2">2 Criteria</a><a href="#s3">3 Placements</a><a href="#s4">4 Exact grid</a>
  <a href="#s5">5 Method</a><a href="#s6">6 Deviation 15</a><a href="#s7">7 Gate 1b</a><a href="#s8">8 Dial grid</a>
  <a href="#s9">9 Budget</a><a href="#s10">10 Decisions</a><a href="#s11">11 Sources</a>
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
<footer>Built from main @ {MAIN_SHA} by scripts/build_gate1_report.py ({{COMMIT_NOTE}}). Derived quantities computed at build time; verdict words as in gate1_summary.json.</footer>
</div>
"""

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', default=str(ROOT / 'build' / 'gate1_report.html'), help='where to write the artifact page')
    ap.add_argument('--commit', default=None, help='hash of the commit that carries the builder and docs/GATE1_REPORT.md (footer note)')
    ap.add_argument('--no-md', action='store_true', help='do not rewrite docs/GATE1_REPORT.md')
    args = ap.parse_args()
    if not args.no_md:
        (ROOT / 'docs' / 'GATE1_REPORT.md').write_text(md)
    note = f'builder and Markdown twin docs/GATE1_REPORT.md committed as {args.commit}' if args.commit else 'builder and Markdown twin docs/GATE1_REPORT.md not yet committed to main'
    out = Path(args.html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.replace('{COMMIT_NOTE}', note))
    print('wrote', ROOT / 'docs' / 'GATE1_REPORT.md', len(md), 'chars;', out, len(page), 'chars')
    print('pending marks:', md.count('**pending**'))
    for p in pending_values:
        print(' -', p)
