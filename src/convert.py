import os
import sys
import re
from rdflib import Graph, URIRef, BNode, Literal, Namespace, RDF, SKOS, XSD
from rdflib.collection import Collection

SH = Namespace("http://www.w3.org/ns/shacl#")
DASH = Namespace("http://datashapes.org/dash#")
EX = Namespace("http://example.com/pact#")

def convert(csv: str, controlled_lists: dict) -> Graph:
    output = Graph()
    output.bind("sh", SH)
    output.bind("dash", DASH)
    output.bind("ex", EX)
    output.bind("pact", Namespace("http://purl.org/pact_funders/"))

    nodeshape = EX.GrantShape
    output.add((nodeshape, RDF.type, SH.NodeShape))
    output.add((nodeshape, SH.targetClass, EX.Grant))

    file = open(csv, "r")

    # skip header line
#AF    next(file)

    # error message debug purpose
    row = 1

    for line in file:
        row += 1

        subject = BNode()
        output.add((nodeshape, SH.property, subject))
        output.add((subject, SH.order, Literal(row)))

        print(line.split("\t"))
        (group, predicate, label, answtype, listname, req, cardinality, comment) = line.split("\t")
        #print(f"got line {label}")

        # predicate
        #print(f"\tpredicate is {predicate}")
        output.add((subject, SH.path, URIRef(predicate)))

        # label
        name = re.sub(r"(?<!^)(?<!\s|[A-Z])([A-Z])", r" \1", label)
        #print(f"\tname is {name}")
        output.add((subject, SH.name, Literal(name)))

        # answer type
        if answtype == "text":
            output.add((subject, SH.nodeKind, SH.Literal))
            output.add((subject, DASH.viewer, DASH.LiteralViewer))
            output.add((subject, DASH.editor, DASH.TextFieldEditor))
        elif answtype == "URI":
            output.add((subject, SH.nodeKind, SH.IRI))
            output.add((subject, DASH.viewer, DASH.LabelViewer))
            output.add((subject, DASH.editor, DASH.URIEditor))
        elif answtype == "date":
            output.add((subject, SH.datatype, XSD.date))
            output.add((subject, DASH.viewer, DASH.LiteralViewer))
            output.add((subject, DASH.editor, DASH.BooleanSelectEditor))
        elif answtype == "controlled list":
            output.add((subject, SH.nodeKind, SH.IRI))
            output.add((subject, DASH.viewer, DASH.LabelViewer))
            output.add((subject, DASH.editor, DASH.EnumSelectEditor))

            if listname not in controlled_lists.keys():
                print(f"error on row {row}: controlled list name '{listname}' is not a known controlled list name")
                continue

            uri = controlled_lists[listname]
            concepts = parse_controlled_list_concept(uri)
            
            if len(concepts) > 0:
                l = BNode()
                c = Collection(output, l, concepts)
                output.add((subject, SH["in"], l))
            else:
                print(f"error on row {row}: list is empty")
                output.add((subject, SH["in"], RDF.nil))

        elif answtype == "number":
            output.add((subject, SH.datatype, XSD.int))
            output.add((subject, DASH.viewer, DASH.LiteralViewer))
            output.add((subject, DASH.editor, DASH.TextFieldEditor))
        elif answtype == "boolean":
            output.add((subject, SH.datatype, XSD.boolean))
            output.add((subject, DASH.viewer, DASH.LiteralViewer))
            output.add((subject, DASH.editor, DASH.BooleanSelectEditor))
        else:
            print(f"error on row {row}: answer type '{answtype}' is not recognized")

        # parse cardinality
        (min_card, max_card) = cardinality.split("..")
        if min_card == "0":
            #print("\tskip min cardinality because it is 0")
            pass
        else:
            #print(f"\tmin cardinality is {min_card}")
            output.add((subject, SH.minCount, Literal(int(min_card))))
        if max_card == "n":
            #print("\tskip max cardinality because it is n")
            pass
        else:
            #print(f"\tmax cardinality is {max_card}")
            output.add((subject, SH.maxCount, Literal(int(max_card))))

    return output


def parse_controlled_lists(tsv: str) -> dict:
    file = open(tsv, "r")

    lists = {}

    for line in file:
        print("controlled: ", line.rstrip().split("\t"))
        (name, uri) = line.rstrip().split("\t")
        lists[name] = uri

    return lists


def parse_controlled_list_concept(uri: str):
    try:
        g = Graph().parse(format="ttl", location=uri)
    except:
        print(f"error: could not parse {uri}")
        return []

    if (URIRef(uri), SKOS.broader, None) in g:
        print(f"error: {uri} seems to be a narrow concept")

    return [concept for concept in g.objects(subject=URIRef(uri), predicate=SKOS.narrower)]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Missing arguments. Please invoke with:")
        print(f"{sys.argv[0]} schema.tsv controlled-lists.tsv")
        sys.exit(1)

    controlled_lists = parse_controlled_lists(sys.argv[2])
    #print(controlled_lists)

    output = convert(sys.argv[1], controlled_lists)
    path = sys.argv[1]
    if os.path.exists(path.rpartition('.')[0] + ".fdp"):
        os.remove(path.rpartition('.')[0] + ".fdp")

    file=open(path.rpartition('.')[0] + ".fdp", 'w')
    file.write(output.serialize())
    file.close()

    if os.path.exists(sys.argv[2]):
        os.remove(sys.argv[2])
