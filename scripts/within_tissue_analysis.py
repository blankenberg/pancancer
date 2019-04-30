"""
Gregory Way 2017
PanCancer NF1/RAS Classifier
scripts/within_tissue_analysis.py

Usage: Run in command line

        python within_tissue_analysis.py

with the following required flags:

        --genes         comma separated string of HUGO gene symbols

and the following optional flags:

        --diseases      comma separated string of disease types to include
        --l1_ratios     comma separated string of l1 parameters to test
        --folder        string indicating the location to save results
        --remove_hyper  if present, remove hypermutated tumors

Output:
Results of single tissue classifier run through pancancer_classifier.py
"""

import os
import subprocess
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('-g', '--genes',
                    help='Comma separated string of HUGO gene symbols')
parser.add_argument('-d', '--diseases', default='Auto',
                    help='Comma separated string of disease types to consider')
parser.add_argument('-a', '--alphas', default='0.1,0.15,0.2,0.5,0.8,1',
                    help='the alphas for parameter sweep')
parser.add_argument('-l', '--l1_ratios', default='0,0.1,0.15,0.18,0.2,0.3',
                    help='the l1 ratios for parameter sweep')
parser.add_argument('-v', '--remove_hyper', action='store_true',
                    help='Remove hypermutated samples')
parser.add_argument('-f', '--alt_folder', default='Auto',
                    help='location to save')
parser.add_argument('-x', '--x_matrix', default=None,
                    help='Filename of features to use in model')
parser.add_argument('--filename_mut', default=None,
                    help='Filename of sample/gene mutations to use in model')
parser.add_argument('--filename_mut_burden', default=None,
                    help='Filename of sample mutation burden to use in model')
parser.add_argument('--filename_sample', default=None,
                    help='Filename of patient/samples to use in model')
parser.add_argument('--filename_copy_loss', default=None,
                    help='Filename of copy number loss')
parser.add_argument('--filename_copy_gain', default=None,
                    help='Filename of copy number gain')
parser.add_argument('--filename_cancer_gene_classification', default=None,
                    help='Filename of cancer gene classification table')


args = parser.parse_args()

# make it a little easier to pass forward filename args
args_dict = vars(args)
filename_arg_list = ['x_matrix']
for k in args_dict.keys():
    if k.startswith('filename_'):
        filename_arg_list.append(k)

# Load command arguments
genes = args.genes
diseases = args.diseases.split(',')
folder = args.alt_folder
alphas = args.alphas
l1_ratios = args.l1_ratios
remove_hyper = args.remove_hyper

base_folder = os.path.join('classifiers', 'within_disease',
                           genes.replace(',', '_'))

if diseases == 'Auto':
    sample_freeze_file = os.path.join('data', 'sample_freeze.tsv')
    sample_freeze = pd.read_table(sample_freeze_file, index_col=0)
    disease_types = sample_freeze['DISEASE'].unique().tolist()
else:
    disease_types = diseases

# Loop over disease types
for acronym in disease_types:
    print(acronym)
    if folder == 'Auto':
        alt_folder = os.path.join(base_folder, acronym)
    else:
        alt_folder = os.path.join(folder, acronym)
    command = ['python', os.path.join('scripts', 'pancancer_classifier.py'),
               '--genes', genes, '--diseases', acronym, '--drop',
               '--copy_number', '--alphas', alphas, '--l1_ratios', l1_ratios,
               '--alt_folder', alt_folder, '--shuffled', '--keep_intermediate']
    if remove_hyper:
        command += ['--remove_hyper']
    # Only set filename if it has been set
    for fname_arg in filename_arg_list:
        val = args_dict.get(fname_arg, None)
        if val:
            command += ['--%s' % (fname_arg), val]
    subprocess.call(command)
