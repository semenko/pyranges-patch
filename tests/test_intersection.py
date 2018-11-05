
import pytest

from pyranges.pyranges import PyRanges

from tests.helpers import assert_dfs_equal
import pandas as pd

from io import StringIO


@pytest.fixture
def simple_gr1():

    c = """Chromosome Start End Strand Score
chr1 3 6 + 5
chr1 5 7 - 7
chr1 8 9 + 1"""

    df = pd.read_table(StringIO(c), sep="\s+", header=0)
    return PyRanges(df)



@pytest.fixture
def simple_gr2():

    c = """Chromosome Start End Strand Score
chr1 1 2 + 1
chr1 6 7 - 2"""
    df = pd.read_table(StringIO(c), sep="\s+", header=0)
    return PyRanges(df)


@pytest.fixture
def expected_result_intersection_simple_granges():

    c = """Chromosome Start End Strand Score
chr1    6   7   - 7"""

    df = pd.read_table(StringIO(c), sep="\s+", header=0)
    return PyRanges(df)



def test_intersect_simple_granges(simple_gr1, simple_gr2, expected_result_intersection_simple_granges):

    print(simple_gr1)
    print(simple_gr2)
    result = simple_gr1.intersection(simple_gr2, strandedness=False)

    print("result\n", result)

    assert_dfs_equal(result, expected_result_intersection_simple_granges)


@pytest.fixture
def expected_result_same_strand_intersection_simple_granges():

    c = """Chromosome Start End Strand Score
chr1    6   7   - 7"""

    df = pd.read_table(StringIO(c), sep="\s+", header=0)
    return PyRanges(df)


def test_intersect_same_strand_simple_granges(simple_gr1, simple_gr2, expected_result_same_strand_intersection_simple_granges):

    result = simple_gr1.intersection(simple_gr2, strandedness="same")

    print("result")
    print(result)
    print("expected")
    print(expected_result_same_strand_intersection_simple_granges)

    assert_dfs_equal(expected_result_same_strand_intersection_simple_granges, result)



# @pytest.fixture
# def expected_result_opposite_strand_intersection_simple_granges():

#     c = """Chromosome Start End Strand Score
# chr1	3	6	+ 5
# chr1    5   7   - 7
# chr1	8	9	+ 1"""

#     df = pd.read_table(StringIO(c), sep="\s+", header=0)
#     return PyRanges(df)


def test_intersect_opposite_strand_simple_granges(simple_gr1, simple_gr2):

    result = simple_gr1.intersection(simple_gr2, strandedness="opposite")

    print(result)

    assert len(result) == 0



def test_intersect_unstranded_simple_granges_containment(simple_gr1, simple_gr2):

    result = simple_gr1.intersection(simple_gr2, strandedness=None, how="containment")

    print(result)

    assert len(result) == 0
