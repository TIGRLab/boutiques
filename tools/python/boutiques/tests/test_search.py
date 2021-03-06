from boutiques.bosh import bosh
from unittest import TestCase
import mock
from boutiques_mocks import mock_zenodo_search, MockZenodoRecord


def mock_get(*args, **kwargs):
    query = args[0].split("=")[1]
    query = query[:query.find("&")]

    exact = False
    if "*" not in query:
        exact = True

    query = query.replace("*", '')
    max_results = args[0].split("=")[-1]

    # Long description text to test truncation
    long_description = ("Lorem ipsum dolor sit amet, consectetur adipiscing "
                        "elit, sed do eiusmod tempor incididunt ut labore et "
                        "dolore magna aliqua. Ut enim ad minim veniam, quis "
                        "nostrud exercitation ullamco laboris nisi ut aliquip "
                        "ex ea commodo consequat.")

    mock_records = []
    # Return an arbitrary list of results with length max_results
    if query == "boutiques":
        for i in range(0, int(max_results)):
            mock_records.append(MockZenodoRecord(i, "Example Tool %s" % i,
                                                 long_description,
                                                 "exampleTool%s.json" % i, i))
    # Return only records containing the query
    else:
        mock_records.append(MockZenodoRecord(1234567, query))
        if not exact:
            mock_records.append(MockZenodoRecord(1234568, "foo-" + query))
            mock_records.append(MockZenodoRecord(1234569, query + "-bar"))

    return mock_zenodo_search(mock_records)


class TestSearch(TestCase):

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_all(self, mocked_get):
        results = bosh(["search"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION",
                                           "DOWNLOADS"])

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_query(self, mock_get):
        results = bosh(["search", "Example Tool 5"])
        assert(len(results) > 0)
        assert(any(d['TITLE'] == 'Example Tool 5' for d in results))
        assert(any(d['TITLE'] == 'foo-Example Tool 5' for d in results))
        assert(any(d['TITLE'] == 'Example Tool 5-bar' for d in results))

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_exact_match(self, mock_get):
        results = bosh(["search", "Example Tool 5", "--exact"])
        print(results)
        assert(len(results) > 0)
        assert(any(d['TITLE'] == 'Example Tool 5' for d in results))
        assert(not any(d['TITLE'] == 'foo-Example Tool 5' for d in results))
        assert(not any(d['TITLE'] == 'Example Tool 5-bar' for d in results))

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_verbose(self, mock_get):
        results = bosh(["search", "-v"])
        assert(len(results) > 0)
        assert(list(results[0].keys()) == ["ID", "TITLE", "DESCRIPTION",
                                           "DOWNLOADS", "AUTHOR", "VERSION",
                                           "DOI", "SCHEMA VERSION",
                                           "CONTAINER", "TAGS"])

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_specify_max_results(self, mock_get):
        results = bosh(["search", "-m", "20"])
        assert(len(results) == 20)

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_sorts_by_num_downloads(self, mock_get):
        results = bosh(["search"])
        downloads = []
        for r in results:
            downloads.append(r["DOWNLOADS"])
        assert(all(downloads[i] >= downloads[i+1]
               for i in range(len(downloads)-1)))

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_truncates_long_text(self, mock_get):
        results = bosh(["search"])
        for r in results:
            for k, v in r.items():
                assert(len(str(v)) <= 43)

    @mock.patch('requests.get', side_effect=mock_get)
    def test_search_no_trunc(self, mock_get):
        results = bosh(["search", "--no-trunc"])
        has_no_trunc = False
        for r in results:
            for k, v in r.items():
                if len(str(v)) > 43:
                    has_no_trunc = True
                    break
            else:
                continue
            break
        assert(has_no_trunc)
