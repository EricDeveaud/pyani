#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) The James Hutton Institute 2013-2019
# (c) The University of Strathclude 2019-2020
# Author: Leighton Pritchard
#
# Contact:
# leighton.pritchard@strath.ac.uk
#
# Leighton Pritchard,
# Strathclyde Institute of Pharmaceutical and Biomedical Sciences
# The University of Strathclyde
# 161 Cathedral Street
# Glasgow
# G4 0RE
# Scotland,
# UK
#
# The MIT License
#
# Copyright (c) 2013-2019 The James Hutton Institute
# (c) The University of Strathclude 2019-2020
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Pytest configuration file."""

import copy
import subprocess

from argparse import Namespace
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple

import pandas as pd
import pytest

from pyani import download
from pyani.download import ASMIDs, DLStatus
from pyani.pyani_config import (
    BLASTALL_DEFAULT,
    BLASTN_DEFAULT,
    FILTER_DEFAULT,
    FORMATDB_DEFAULT,
    MAKEBLASTDB_DEFAULT,
    NUCMER_DEFAULT,
)
from pyani.pyani_tools import get_labels
from pyani.scripts import genbank_get_genomes_by_taxon

# Path to tests, contains tests and data subdirectories
TESTSPATH = Path(__file__).parents[0]
FIXTUREPATH = TESTSPATH / "fixtures"


class ANIbOutput(NamedTuple):

    """Convenience struct for ANIb output."""

    fragfile: Path
    tabfile: Path
    legacytabfile: Path


class ANIbOutputDir(NamedTuple):

    """Convenience struct for ANIb output."""

    infiles: List[Path]
    fragfiles: List[Path]
    blastdir: Path
    legacyblastdir: Path
    blastresult: pd.DataFrame
    legacyblastresult: pd.DataFrame


class DeltaDir(NamedTuple):

    """Convenience struct for MUMmer .delta file and associated parsed output."""

    seqdir: Path
    deltadir: Path
    deltaresult: pd.DataFrame


class DeltaParsed(NamedTuple):

    """Convenience struct for MUMmer .delta file and associated parsed output."""

    filename: Path
    data: Tuple[int]


class GraphicsTestInputs(NamedTuple):

    """Convenience struct for graphics test inputs."""

    filename: Path
    labels: Dict[str, str]
    classes: Dict[str, str]


class JobScript(NamedTuple):

    """Convenience struct for job script creation tests."""

    params: Dict[str, str]
    script: str


class MUMmerExample(NamedTuple):

    """Convenience struct for MUMmer command-line examples."""

    infiles: List[Path]
    ncmds: List[str]
    fcmds: List[str]


def modify_namespace(namespace: Namespace, **kwargs):
    """Update arguments in a passed Namespace.

    :param namespace:       argparse.Namespace object
    :param args:            dict of argument: value pairs

    The expected usage pattern is, for a command-line application with many
    or complex arguments, to define a base argparse.Namespace object, then
    change only a few arguments, specific to a test. This function takes
    a base namespace and a dictionary of argument: value pairs, and
    returns the modified namespace.
    """
    new_namespace = copy.deepcopy(namespace)
    for argname, argval in kwargs.items():
        setattr(new_namespace, argname, argval)
    return new_namespace


@pytest.fixture
def anib_output(dir_anib_in):
    """Namedtuple of example ANIb output.

    fragfile - fragmented FASTA query file
    tabfile  - BLAST+ tabular output
    legacytabfile - blastall tabular output
    """
    return ANIbOutput(
        dir_anib_in / "NC_002696-fragments.fna",
        dir_anib_in / "NC_002696_vs_NC_011916.blast_tab",
        dir_anib_in / "NC_002696_vs_NC_010338.blast_tab",
    )


@pytest.fixture
def anib_output_dir(dir_anib_in):
    """Namedtuple of example ANIb output - full directory.

    infiles - list of FASTA query files
    fragfiles - list of fragmented FASTA query files
    blastdir - path to BLAST+ output data
    legacyblastdir - path to blastall output data
    blastresult - pd.DataFrame result for BLAST+
    legacyblastresult - pd.DataFrame result for blastall
    """
    return ANIbOutputDir(
        [
            _
            for _ in (dir_anib_in / "sequences").iterdir()
            if _.is_file() and _.suffix == ".fna"
        ],
        [
            _
            for _ in (dir_anib_in / "fragfiles").iterdir()
            if _.is_file() and _.suffix == ".fna"
        ],
        dir_anib_in / "blastn",
        dir_anib_in / "blastall",
        pd.read_csv(dir_anib_in / "dataframes" / "blastn_result.csv", index_col=0),
        pd.read_csv(dir_anib_in / "dataframes" / "blastall_result.csv", index_col=0),
    )


@pytest.fixture
def args_createdb(tmp_path):
    """Command-line arguments for database creation."""
    return ["createdb", "--dbpath", tmp_path / "pyanidb", "--force"]


@pytest.fixture
def args_single_genome_download(tmp_path):
    """Command-line arguments for single genome download."""
    return [
        "download",
        "-t",
        "218491",
        "--email",
        email_address,
        tmp_path,
        "--force",
    ]


@pytest.fixture
def blastall_available():
    """Returns True if blastall can be run, False otherwise."""
    cmd = str(BLASTALL_DEFAULT)
    # Can't use check=True, as blastall without arguments returns 1!
    try:
        result = subprocess.run(
            cmd,
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        return False
    return result.stdout[1:9] == b"blastall"


@pytest.fixture
def blastn_available():
    """Returns True if blastn can be run, False otherwise."""
    cmd = [str(BLASTN_DEFAULT), "-version"]
    try:
        result = subprocess.run(
            cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
    except OSError:
        return False
    return result.stdout[:6] == b"blastn"


@pytest.fixture
def delta_output_dir(dir_anim_in):
    """Namedtuple of example MUMmer .delta file output."""
    return DeltaDir(
        dir_anim_in / "sequences",
        dir_anim_in / "deltadir",
        pd.read_csv(dir_anim_in / "dataframes" / "deltadir_result.csv", index_col=0),
    )


@pytest.fixture
def deltafile_parsed(dir_anim_in):
    """Example parsed deltafile data."""
    return DeltaParsed(dir_anim_in / "test.delta", (4074001, 2191))


@pytest.fixture
def dir_anib_in():
    """Input files for ANIb tests."""
    return FIXTUREPATH / "anib"


@pytest.fixture
def dir_anim_in():
    """Input files for ANIm tests."""
    return FIXTUREPATH / "anim"


@pytest.fixture
def dir_graphics_in():
    """Input files for graphics tests."""
    return FIXTUREPATH / "graphics"


@pytest.fixture
def dir_seq():
    """Sequence files for tests."""
    return FIXTUREPATH / "sequences"


@pytest.fixture
def dir_targets():
    """Target files for output comparisons."""
    return FIXTUREPATH / "targets"


@pytest.fixture
def dir_tgt_fragments(dir_targets):
    """Target files for FASTA file fragmentation."""
    return dir_targets / "fragments"


@pytest.fixture
def email_address():
    """Dummy email address."""
    return "pyani.tests@pyani.org"


@pytest.fixture
def fragment_length():
    """Fragment size for ANIb-related analyses."""
    return 1000


@pytest.fixture
def graphics_inputs(dir_graphics_in):
    """Returns namedtuple of graphics inputs."""
    return GraphicsTestInputs(
        dir_graphics_in / "ANIm_percentage_identity.tab",
        get_labels(dir_graphics_in / "labels.tab"),
        get_labels(dir_graphics_in / "classes.tab"),
    )


@pytest.fixture
def job_dummy_cmds():
    """Dummy commands for testing job creation."""
    return ["ls -ltrh", "echo ${PWD}"]


@pytest.fixture
def job_empty_script():
    """Empty script for testing job creation."""
    return 'let "TASK_ID=$SGE_TASK_ID - 1"\n\n\n\n'


@pytest.fixture
def job_scripts():
    """Return two JobScript namedtuples for testing job creation."""
    return (
        JobScript(
            {"-f": ["file1", "file2", "file3"]},
            "".join(
                [
                    'let "TASK_ID=$SGE_TASK_ID - 1"\n',
                    "-f_ARRAY=( file1 file2 file3  )\n\n",
                    'let "-f_INDEX=$TASK_ID % 3"\n',
                    "-f=${-f_ARRAY[$-f_INDEX]}\n",
                    'let "TASK_ID=$TASK_ID / 3"\n\n',
                    "cat\n",
                ]
            ),
        ),
        JobScript(
            {"-f": ["file1", "file2"], "--format": ["fmtA", "fmtB"]},
            "".join(
                [
                    'let "TASK_ID=$SGE_TASK_ID - 1"\n',
                    "--format_ARRAY=( fmtA fmtB  )\n",
                    "-f_ARRAY=( file1 file2  )\n\n",
                    'let "--format_INDEX=$TASK_ID % 2"\n',
                    "--format=${--format_ARRAY[$--format_INDEX]}\n",
                    'let "TASK_ID=$TASK_ID / 2"\n',
                    'let "-f_INDEX=$TASK_ID % 2"\n',
                    "-f=${-f_ARRAY[$-f_INDEX]}\n",
                    'let "TASK_ID=$TASK_ID / 2"\n\n',
                    "myprog\n",
                ]
            ),
        ),
    )


@pytest.fixture
def legacy_ani_namespace(tmp_path):
    """Base namespace for legacy average_nucleotide_identity.py tests."""
    return Namespace(
        outdirname=tmp_path,
        indirname=FIXTUREPATH / "legacy" / "ANI_input",
        verbose=False,
        debug=False,
        force=True,
        fragsize=1020,
        logfile=Path("test_ANIm.log"),
        skip_nucmer=False,
        skip_blastn=False,
        noclobber=False,
        nocompress=False,
        graphics=True,
        gformat="pdf,png",
        gmethod="seaborn",
        labels=FIXTUREPATH / "legacy" / "ANI_input" / "labels.txt",
        classes=FIXTUREPATH / "legacy" / "ANI_input" / "classes.txt",
        method="ANIm",
        scheduler="multiprocessing",
        workers=None,
        sgeargs=None,
        sgegroupsize=10000,
        maxmatch=False,
        nucmer_exe=NUCMER_DEFAULT,
        filter_exe=FILTER_DEFAULT,
        blastn_exe=BLASTN_DEFAULT,
        blastall_exe=BLASTALL_DEFAULT,
        makeblastdb_exe=MAKEBLASTDB_DEFAULT,
        formatdb_exe=FORMATDB_DEFAULT,
        write_excel=False,
        rerender=False,
        subsample=None,
        seed=None,
        jobprefix="ANI",
    )


@pytest.fixture
def legacy_anib_sns_namespace(tmp_path, legacy_ani_namespace):
    """Namespace for legacy ANIm script tests.

    Uses the base namespace to run ANIm with seaborn output
    """
    return modify_namespace(legacy_ani_namespace, method="ANIb")


@pytest.fixture
def legacy_anib_mpl_namespace(tmp_path, legacy_ani_namespace):
    """Namespace for legacy ANIm script tests.

    Runs ANIm with matplotlib output
    """
    return modify_namespace(legacy_ani_namespace, gmethod="mpl", method="ANIb")


@pytest.fixture
def legacy_anim_sns_namespace(tmp_path, legacy_ani_namespace):
    """Namespace for legacy ANIm script tests.

    Uses the base namespace to run ANIm with seaborn output
    """
    return legacy_ani_namespace


@pytest.fixture
def legacy_anim_mpl_namespace(tmp_path, legacy_ani_namespace):
    """Namespace for legacy ANIm script tests.

    Runs ANIm with matplotlib output
    """
    return modify_namespace(legacy_ani_namespace, gmethod="mpl")


@pytest.fixture
def legacy_download_namespace(tmp_path):
    """Namespace for legacy download script tests."""
    return Namespace(
        outdirname=tmp_path,
        taxon="203804",
        verbose=False,
        force=True,
        noclobber=False,
        logfile=None,
        format="fasta",
        email="pyani@pyani.tests",
        retries=20,
        batchsize=10000,
        timeout=10,
        debug=False,
    )


@pytest.fixture
def legacy_tetra_sns_namespace(tmp_path, legacy_ani_namespace):
    """Namespace for legacy ANIm script tests.

    Uses the base namespace to run ANIm with seaborn output
    """
    return modify_namespace(legacy_ani_namespace, method="TETRA")


@pytest.fixture
def legacy_tetra_mpl_namespace(tmp_path, legacy_ani_namespace):
    """Namespace for legacy ANIm script tests.

    Uses the base namespace to run ANIm with mpl output
    """
    return modify_namespace(legacy_ani_namespace, method="TETRA", gmethod="mpl")


@pytest.fixture
def mummer_cmds_four(path_file_four):
    """Example MUMmer commands (four files)."""
    return MUMmerExample(
        path_file_four,
        [
            "nucmer --mum -p nucmer_output/file1_vs_file2 file1.fna file2.fna",
            "nucmer --mum -p nucmer_output/file1_vs_file3 file1.fna file3.fna",
            "nucmer --mum -p nucmer_output/file1_vs_file4 file1.fna file4.fna",
            "nucmer --mum -p nucmer_output/file2_vs_file3 file2.fna file3.fna",
            "nucmer --mum -p nucmer_output/file2_vs_file4 file2.fna file4.fna",
            "nucmer --mum -p nucmer_output/file3_vs_file4 file3.fna file4.fna",
        ],
        [
            (
                "delta_filter_wrapper.py delta-filter -1 "
                "nucmer_output/file1_vs_file2.delta "
                "nucmer_output/file1_vs_file2.filter"
            ),
            (
                "delta_filter_wrapper.py delta-filter -1 "
                "nucmer_output/file1_vs_file3.delta "
                "nucmer_output/file1_vs_file3.filter"
            ),
            (
                "delta_filter_wrapper.py delta-filter -1 "
                "nucmer_output/file1_vs_file4.delta "
                "nucmer_output/file1_vs_file4.filter"
            ),
            (
                "delta_filter_wrapper.py delta-filter -1 "
                "nucmer_output/file2_vs_file3.delta "
                "nucmer_output/file2_vs_file3.filter"
            ),
            (
                "delta_filter_wrapper.py delta-filter -1 "
                "nucmer_output/file2_vs_file4.delta "
                "nucmer_output/file2_vs_file4.filter"
            ),
            (
                "delta_filter_wrapper.py delta-filter -1 "
                "nucmer_output/file3_vs_file4.delta "
                "nucmer_output/file3_vs_file4.filter"
            ),
        ],
    )


@pytest.fixture
def nucmer_available():
    """Test that nucmer is available."""
    cmd = [str(NUCMER_DEFAULT), "--version"]
    try:
        result = subprocess.run(
            cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
    except OSError:
        return False
    return result.stderr[:6] == b"nucmer"


@pytest.fixture
def path_concordance_jspecies():
    """Path to JSpecies analysis output."""
    return FIXTUREPATH / "concordance/jspecies_output.tab"


@pytest.fixture
def path_file_two():
    """Path to two arbitrary filenames."""
    return [Path(f"file{_:d}.fna") for _ in range(1, 3)]


@pytest.fixture
def path_file_four():
    """Path to four arbitrary filenames."""
    return [Path(f"file{_:d}.fna") for _ in range(1, 5)]


@pytest.fixture
def path_fna(dir_seq):
    """Path to one .fna sequence file from dir_seq."""
    fnapaths = [_ for _ in dir_seq.iterdir() if _.is_file() and _.suffix == ".fna"]
    return fnapaths[0]


@pytest.fixture
def path_fna_two(dir_seq):
    """Paths to two .fna sequence file in dir_seq."""
    fnapaths = [_ for _ in dir_seq.iterdir() if _.is_file() and _.suffix == ".fna"]
    return fnapaths[:2]


@pytest.fixture
def path_fna_all(dir_seq):
    """Paths to all .fna sequence file in dir_seq."""
    return [_ for _ in dir_seq.iterdir() if _.is_file() and _.suffix == ".fna"]


@pytest.fixture
def paths_concordance_fna():
    """Paths to FASTA inputs for concordance analysis."""
    return [
        _
        for _ in (FIXTUREPATH / "concordance").iterdir()
        if _.is_file() and _.suffix == ".fna"
    ]


@pytest.fixture(autouse=True)
def skip_by_unavailable_executable(
    request, blastall_available, blastn_available, nucmer_available
):
    """Skip test if executable is unavailable.

    Use with @pytest.mark.skip_if_exe_missing("executable") decorator.
    """
    if request.node.get_closest_marker("skip_if_exe_missing"):
        exe_name = request.node.get_closest_marker("skip_if_exe_missing").args[0]
        tests = {
            "blastall": blastall_available,
            "blastn": blastn_available,
            "nucmer": nucmer_available,
        }
        try:
            if not tests[exe_name]:
                pytest.skip(f"Skipped as {exe_name} not available")
        except KeyError:  # Unknown executables are ignored
            pytest.skip(f"Executable {exe_name} not recognised")


@pytest.fixture
def threshold_anib_lo_hi():
    """Threshold for concordance comparison split between high and low identity.

    When comparing ANIb results with ANIblastall results, we need to account for
    the differing performances of BLASTN and BLASTN+ on more distantly-related
    sequences. On closely-related sequences both methods give similar results;
    for more distantly-related sequences, the results can be quite different. This
    threshold is the percentage identity we consider to separate "close" from
    "distant" related sequences.
    """
    return 90


@pytest.fixture
def tolerance_anib_hi():
    """Tolerance for ANIb concordance comparisons.

    This tolerance is for comparisons between "high identity" comparisons, i.e.
    genomes having identity greater than threshold_anib_lo_hi in homologous regions.

    These "within-species" level comparisons need to be more accurate
    """
    return 0.1


@pytest.fixture
def tolerance_anib_lo():
    """Tolerance for ANIb concordance comparisons.

    This tolerance is for comparisons between "low identity" comparisons, i.e.
    genomes having identity less than threshold_anib_lo_hi in homologous regions.

    These "intra-species" level comparisons vary more as a result of the change of
    algorithm from BLASTN to BLASTN+ (megablast).
    """
    return 5


@pytest.fixture
def tolerance_anim():
    """Tolerance for ANIm concordance comparisons."""
    return 0.1


@pytest.fixture
def tolerance_tetra():
    """Tolerance for TETRA concordance comparisons."""
    return 0.1


@pytest.fixture
def mock_single_genome_dl(monkeypatch):
    """Mocks remote database calls for single-genome downloads.

    This masks calls to the download module, for safe testing.
    """

    def mock_asmuids(*args, **kwargs):
        """Mock download.get_asm_uids()."""
        return ASMIDs("txid218491[Organism:exp]", 1, ["32728"])

    def mock_ncbi_esummary(*args, **kwargs):
        """Mock download.get_ncbi_esummary()."""
        return (
            {
                "Taxid": "218491",
                "SpeciesTaxid": "29471",
                "AssemblyAccession": "GCF_000011605.1",
                "AssemblyName": "ASM1160v1",
                "SpeciesName": "Pectobacterium atrosepticum",
            },
            "GCF_000011605.1_ASM1160v1",
        )

    def mock_genome_hash(*args, **kwargs):
        """Mock download.retrieve_genome_and_hash()."""
        return DLStatus(
            "ftp://ftp.ncbi.nlm.nih.gov/dummy_genomic.fna.gz",
            "ftp://ftp.ncbi.nlm.nih.gov/dummy/md5checksums.txt",
            FIXTUREPATH
            / "single_genome_download"
            / "GCF_000011605.1_ASM1160v1_genomic.fna.gz",
            FIXTUREPATH / "single_genome_download/GCF_000011605.1_ASM1160v1_hashes.txt",
            False,
            None,
        )

    monkeypatch.setattr(download, "get_asm_uids", mock_asmuids)
    monkeypatch.setattr(download, "get_ncbi_esummary", mock_ncbi_esummary)
    monkeypatch.setattr(download, "retrieve_genome_and_hash", mock_genome_hash)


@pytest.fixture
def mock_legacy_single_genome_dl(monkeypatch):
    """Mocks remote database calls for single-genome downloads.

    This masks calls to functions in genbank_get_genomes_by_taxon, for safe testing.

    This will be deprecated once the genbank_get_genomes_by_taxon.py script is
    converted to use the pyani.download module.
    """

    def mock_asmuids(*args, **kwargs):
        """Mock genbank_get_genomes_by_taxon.get_asm_uids()."""
        return ["32728"]

    def mock_ncbi_asm(*args, **kwargs):
        """Mock genbank_get_genomes_by_taxon.get_ncbi_asm()."""
        return (
            Path(
                "tests/test_output/legacy_scripts/C_blochmannia_legacy/GCF_000011605.1_ASM1160v1_genomic.fna"
            ),
            "8b0cab310cb638c977d453ff06eceb64\tGCF_000011605.1_ASM1160v1_genomic\tPectobacterium atrosepticum",
            "8b0cab310cb638c977d453ff06eceb64\tGCF_000011605.1_ASM1160v1_genomic\tP. atrosepticum SCRI1043",
            "GCF_000011605.1",
        )

    monkeypatch.setattr(genbank_get_genomes_by_taxon, "get_asm_uids", mock_asmuids)
    monkeypatch.setattr(genbank_get_genomes_by_taxon, "get_ncbi_asm", mock_ncbi_asm)
