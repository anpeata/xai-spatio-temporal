import argparse
from pathlib import Path
import pandas as pd
import csv


def select_track_ids(input_csv, targets, chunksize=100000):
    # targets: dict city->n
    found = {city:set() for city in targets}
    for chunk in pd.read_csv(input_csv, usecols=['track_id','city'], chunksize=chunksize, low_memory=False):
        for city, n in targets.items():
            need = n - len(found[city])
            if need <= 0:
                continue
            # filter rows for this city
            rows = chunk[chunk['city']==city]
            if rows.empty:
                continue
            ids = rows['track_id'].dropna().unique().tolist()
            for tid in ids:
                if len(found[city]) < n:
                    found[city].add(tid)
                else:
                    break
        # early exit if all satisfied
        if all(len(found[c])>=targets[c] for c in targets):
            break
    return found


def write_reduced(input_csv, output_csv, selected_ids, chunksize=100000):
    selected = set()
    for s in selected_ids.values():
        selected.update(s)
    out_path = Path(output_csv)
    first = True
    for chunk in pd.read_csv(input_csv, chunksize=chunksize, low_memory=False):
        mask = chunk['track_id'].isin(selected)
        subset = chunk[mask]
        if subset.empty:
            continue
        if first:
            subset.to_csv(out_path, index=False, mode='w')
            first = False
        else:
            subset.to_csv(out_path, index=False, header=False, mode='a')


if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--n-nantes', type=int, default=10)
    p.add_argument('--n-montpellier', type=int, default=6)
    args = p.parse_args()
    input_csv = Path(args.input)
    output_csv = Path(args.output)
    targets = {'Nantes': args.n_nantes, 'Montpellier': args.n_montpellier}
    print('Selecting track ids for targets:', targets)
    selected = select_track_ids(input_csv, targets)
    print('Selected counts:', {k:len(v) for k,v in selected.items()})
    write_reduced(input_csv, output_csv, selected)
    print('Wrote reduced CSV to', output_csv)
