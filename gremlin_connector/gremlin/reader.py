#   Copyright 2021 Invana
#  #
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#  #
#    http:www.apache.org/licenses/LICENSE-2.0
#  #
#    Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
from gremlin_python.structure.io import graphsonV3d0
from gremlin_connector.typing.elements import Node, RelationShip
from gremlin_python.process.traversal import T, Direction
from gremlin_connector.schema.janusgraph.utils import get_id


class InvanaMapType(graphsonV3d0.MapType):

    @staticmethod
    def create_node(dict_data):
        _ = dict_data.copy()
        node_id = get_id(_[T.id])
        node_label = _[T.label]
        del _[T.id]
        del _[T.label]
        return Node(node_id, node_label, properties=_)

    @staticmethod
    def create_edge(dict_data):
        _ = dict_data.copy()
        node_id = get_id(_[T.id])
        node_label = _[T.label]
        inv = _[Direction.IN]
        outv = _[Direction.OUT]
        del _[T.id]
        del _[T.label]
        del _[Direction.IN]
        del _[Direction.OUT]
        return RelationShip(node_id, node_label, outv, inv, properties=_)

    @classmethod
    def objectify(cls, l, reader):
        new_dict = super(InvanaMapType, cls).objectify(l, reader)
        if T.id in new_dict and Direction.IN not in new_dict:
            return cls.create_node(new_dict)
        if T.id in new_dict and Direction.IN in new_dict:
            return cls.create_edge(new_dict)
        return new_dict


class InvanaVertexDeserializer(graphsonV3d0.VertexDeserializer):

    @classmethod
    def objectify(cls, d, reader):
        return Node(reader.toObject(get_id(d["id"])), d.get("label", "vertex"))


class InvanaEdgeDeserializer(graphsonV3d0.EdgeDeserializer):

    @classmethod
    def objectify(cls, d, reader):
        return RelationShip(reader.toObject(get_id(d["id"])),
                            d.get("label", "edge"),
                            Node(reader.toObject(d["outV"]), d.get("outVLabel", "vertex")),
                            Node(reader.toObject(d["inV"]), d.get("inVLabel", "vertex")))


DESERIALIZER_MAP = {
    "g:Map": InvanaMapType,
    "g:Vertex": InvanaVertexDeserializer,
    "g:Edge": InvanaEdgeDeserializer,
}

invana_graphson_reader = graphsonV3d0.GraphSONReader(
    # deserializer_map=DESERIALIZER_MAP
)
