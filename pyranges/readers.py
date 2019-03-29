
from __future__ import print_function

import sys

import pandas as pd
import numpy as np

import pkg_resources

from pyranges.pyranges import PyRanges
from pyranges import data

from pyrle import PyRles, Rle

from pyranges.version import __version__


def read_bed(f, output_df=False):

    columns = "Chromosome Start End Name Score Strand ThickStart ThickEnd ItemRGB BlockCount BlockSizes BlockStarts".split()

    df = pd.read_csv(f, dtype={"Chromosome": "category", "Strand": "category"}, header=None, sep="\t")

    df.columns = columns[:df.shape[1]]

    if df.Strand.str.contains("\.").any():
        print("Bed file contains '.' strands and is considered unstranded.", file=sys.stderr)

    if not output_df:
        return PyRanges(df)
    else:
        return df


def read_bam(f, output_df=False):

    import pysam

    samfile = pysam.AlignmentFile(f, "rb")

    chromosomes, starts, ends, names, sequences, strands = [], [], [], [], [], []
    for read in samfile.fetch():
        strand = '+'
        if(read.is_reverse):
            strand = '-'

        chromosomes.append(samfile.getrname(read.tid))
        starts.append(read.pos)
        ends.append(read.aend)
        sequences.append(read.seq)
        strands.append(strand)
        names.append(read.qname)

    df = pd.DataFrame({"Chromosome": chromosomes, "Start": starts, "End": ends,
                       "Sequence": sequences, "Strand": strands, "Name": names})["Chromosome Start End Sequence Name Strand".split()]

    if not output_df:
        return PyRanges(df)
    else:
        return df


def _fetch_gene_transcript_exon_id(attribute, annotation):

    no_quotes = attribute.str.replace('"', '').str.replace("'", "")

    df = no_quotes.str.extract("gene_id.?(.+?);(?:.*transcript_id.?(.+?);)?(?:.*exon_number.?(.+?);)?(?:.*exon_id.?(.+?);)?", expand=True)# .iloc[:, [1, 2, 3]]

    df.columns = "GeneID TranscriptID ExonNumber ExonID".split()

    # df.loc[:, "ExonNumber"] = df.ExonNumber.astype(int)

    if annotation == "ensembl":
        newdf = []
        for c in "GeneID TranscriptID ExonID".split():
            r = df[c].astype(str).str.extract('(\d+)').astype(float)
            newdf.append(r)

        newdf = pd.concat(newdf, axis=1)
        newdf.insert(2, "ExonNumber", df["ExonNumber"])
        df = newdf

    return df


def skiprows(f):

    try:
        import gzip
        fh = gzip.open(f)
        for i, l in enumerate(fh):
            if l.decode()[0] != "#":
                break
    except:
        fh = open(f)
        for i, l in enumerate(fh):
            if l[0] != "#":
                break

    fh.close()

    return i

def read_gtf(f, annotation=None, output_df=False, nrows=None):

    """seqname - name of the chromosome or scaffold; chromosome names can be given with or without the 'chr' prefix. Important note: the seqname must be one used within Ensembl, i.e. a standard chromosome name or an Ensembl identifier such as a scaffold ID, without any additional content such as species or assembly. See the example GFF output below.
    # source - name of the program that generated this feature, or the data source (database or project name)
    feature - feature type name, e.g. Gene, Variation, Similarity
    start - Start position of the feature, with sequence numbering starting at 1.
    end - End position of the feature, with sequence numbering starting at 1.
    score - A floating point value.
    strand - defined as + (forward) or - (reverse).
    # frame - One of '0', '1' or '2'. '0' indicates that the first base of the feature is the first base of a codon, '1' that the second base is the first base of a codon, and so on..
    attribute - A semicolon-separated list of tag-value pairs, providing additional information about each feature."""
    dtypes = {"Chromosome": "category", "Feature": "category", "Strand": "category"}

    _skiprows = skiprows(f)

    names = "Chromosome Source Feature Start End Score Strand Frame Attribute".split()
    # names = "Chromosome Start End Score Strand Source Feature Frame Attribute".split()
    df_iter = pd.read_csv(f, sep="\t", header=None, names=names, dtype=dtypes, chunksize=int(1e4), skiprows=_skiprows, nrows=int(1e5)) 

    dfs = []
    for df in df_iter:
        extra = to_rows(df.Attribute)
        df = df.drop("Attribute", axis=1)
        ndf = pd.concat([df, extra], axis=1) 
        dfs.append(ndf)

    df = pd.concat(dfs)

    if not output_df:
        return PyRanges(df)
    else:
        return df




def to_rows(anno):
    rowdicts = []
    for l in anno:
        l = l.replace('"', '').replace(";", "").split()
        rowdicts.append({k: v for k, v in zip(*([iter(l)] * 2))})

    return pd.DataFrame.from_dict(rowdicts).set_index(anno.index)


def read_gtf_restricted(f, annotation=None, output_df=False):


    """seqname - name of the chromosome or scaffold; chromosome names can be given with or without the 'chr' prefix. Important note: the seqname must be one used within Ensembl, i.e. a standard chromosome name or an Ensembl identifier such as a scaffold ID, without any additional content such as species or assembly. See the example GFF output below.
    # source - name of the program that generated this feature, or the data source (database or project name)
    feature - feature type name, e.g. Gene, Variation, Similarity
    start - Start position of the feature, with sequence numbering starting at 1.
    end - End position of the feature, with sequence numbering starting at 1.
    score - A floating point value.
    strand - defined as + (forward) or - (reverse).
    # frame - One of '0', '1' or '2'. '0' indicates that the first base of the feature is the first base of a codon, '1' that the second base is the first base of a codon, and so on..
    attribute - A semicolon-separated list of tag-value pairs, providing additional information about each feature."""
    dtypes = {"Chromosome": "category", "Feature": "category", "Strand": "category"}

    df_iter = pd.read_csv(f, sep="\t", comment="#", usecols=[0, 2, 3, 4, 5, 6, 8], header=None, names="Chromosome Feature Start End Score Strand Attribute".split(), dtype=dtypes, chunksize=int(1e4))

    dfs = []
    for df in df_iter:
        # Since Start is 1-indexed
        df.Start -= 1

        if sum(df.Score == ".") == len(df):
            cols_to_concat = "Chromosome Start End Strand Feature".split()
        else:
            cols_to_concat = "Chromosome Start End Strand Feature Score".split()

        extract = _fetch_gene_transcript_exon_id(df.Attribute, annotation)
        extract.columns = "GeneID TranscriptID ExonNumber ExonID".split()

        extract.ExonNumber = extract.ExonNumber.astype(float)

        df = pd.concat([df[cols_to_concat],
                            extract], axis=1)

        dfs.append(df)

    df = pd.concat(dfs)

    if not output_df:
        return PyRanges(df)
    else:
        return df
