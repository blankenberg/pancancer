"""
Gregory Way 2017
PanCancer Classifier
scripts/snaptron/process_tp53_junctions.py

Takes in snaptron data and classifier decision scores for each sample and
outputs a summarized table of snaptron exon-exon predictions for samples which
have a c.375G>T mutation in TP53.

Usage: Run by dna_damage_repair_tp53exon.sh

Output: Concatenated junction data with classifier decision scores
"""

import argparse
import os
import pandas as pd


def get_rail_id(row):
    """
    Extract specific rail_ids from complex data structure that assigns rail_ids
    (Sample IDs) to snaptron_ids (exon-exon junctions). Designed to be used
    as a pd.DataFrame().apply() function.

    Arguments:
    row - a row in the junction dataframe

    Output: a list of sample IDs with the specific snaptron ID
    """

    row = row['samples'].split(',')

    all_sample_ids = []
    for sample_id in row:
        if sample_id != '':
            sample_id = sample_id.split(':')[0]
            all_sample_ids.append(sample_id)
    return(all_sample_ids)


parser = argparse.ArgumentParser()

parser.add_argument('--sample_file', default=None,
                    help='Filename of SNAPTRON samples')
parser.add_argument('--junction_file', default=None,
                    help='Filename of SNAPTRON junctions')
parser.add_argument('--alt_folder', default=None,
                    help='Folder containing classifier')
parser.add_argument('--output', default=None,
                    help='Filename of output junctions')

args = parser.parse_args()


# File paths
sample_file = args.sample_file or 'samples.tsv.gz'
junction_file = args.junction_file or 'tp53_junctions.txt.gz'
if args.alt_folder:
    mut_scores_file = os.path.join(args.alt_folder,
                                   'tables', 'mutation_classification_scores.tsv')
else:
    mut_scores_file = os.path.join('..', '..', 'classifiers', 'TP53',
                                   'tables', 'mutation_classification_scores.tsv')
out_junc_file = args.output or 'junctions_with_mutations.csv.gz'
# FIXME: upgrading to pandas 0.24.0+ will give 'infer' for to_csv
# currently at 0.23.0
# Only care about gzip for now due to backwards compatibility
if out_junc_file.endswith('.gz'):
    compression_type = 'gzip'
else:
    compression_type = None


samples = pd.read_table(sample_file, compression='infer', low_memory=False)
dictionary = samples[['rail_id', 'gdc_cases.samples.submitter_id']]
junc = pd.read_table(junction_file, compression='infer')
mut_df = pd.read_table(mut_scores_file, index_col=0)

# Process junction file
# diff will store how far away each TP53 junction is away from the specific
# location on exon 4
junc = junc.assign(diff_start=abs(7675994 - junc['start']))
junc = junc.assign(diff_end=abs(7675994 - junc['end']))
junc = junc.sort_values(by="diff_start")

# Map the snaptron IDs onto Rail IDs
junc = junc.assign(rail_id=junc.apply(get_rail_id, axis=1))

# Make new rows for each sample and corresponding junction
junc = junc.set_index(['snaptron_id', 'start', 'end', 'length', 'strand',
                       'left_motif', 'right_motif', 'samples_count',
                       'coverage_sum', 'coverage_avg', 'coverage_median',
                       'diff_start', 'diff_end'])['rail_id']\
            .apply(pd.Series).stack().reset_index()
junc[0] = junc[0].astype(int)

# Map TCGA sample IDs onto snaptron IDs
junc = junc.merge(dictionary, left_on=0, right_on='rail_id')
junc = junc.assign(tcga_id=junc['gdc_cases.samples.submitter_id']
                   .str.slice(start=0, stop=15))
junc.drop(['level_13', 'gdc_cases.samples.submitter_id', 'rail_id'], axis=1,
          inplace=True)

# Merge junctions and mutation classification file
junctions_full = junc.merge(mut_df, left_on='tcga_id', right_index=True)
junctions_full.to_csv(out_junc_file, compression=compression_type)
