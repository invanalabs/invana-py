#    Copyright 2021 Invana
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#     http:www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from invana.ogm.model_querysets import NodeModalQuerySet, RelationshipModalQuerySet
from invana.ogm.utils import convert_to_camel_case
from invana.ogm.properties import PropertyBase
from .. import graph
import types


class Direction:
    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    UNDIRECTED = "UNDIRECTED"


class PropertyManager:

    @classmethod
    def get_property_keys(cls, model):
        return [i for i in model.__dict__.keys() if i[:1] != '_' and isinstance(getattr(model, i), PropertyBase)]

    @classmethod
    def get_relationship_keys(cls, model):
        return [i for i in model.__dict__.keys() if i[:1] != '_' and isinstance(getattr(model, i), PropertyBase)]

        # return [i for i in model.__dict__.keys() if i[:1] != '_'
        #         and isinstance(getattr(model, i), (RelationshipUndirected, RelationshipFrom, RelationshipTo,))]

    @classmethod
    def get_properties(cls, model):
        property_keys = cls.get_property_keys(model)
        property_definitions = [getattr(model, prop_key) for prop_key in property_keys]
        return dict(zip(property_keys, property_definitions))

    @classmethod
    def get_relationships(cls, model):
        keys = cls.get_relationship_keys(model)
        relationship_definitions = [getattr(model, k) for k in keys]
        return dict(zip(keys, relationship_definitions))


class ModelMetaBase(type):

    def __new__(mcs, name, bases, attrs):
        super_new = super().__new__
        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).

        model_class = super_new(ModelMetaBase, name, bases, attrs)

        # parents = [b for b in bases if isinstance(b, ModelMetaBase)]
        # if not parents:
        #     return super_new(mcs, name, bases, attrs)
        # model_base_cls = bases[0]

        if hasattr(model_class, '__abstract__'):
            delattr(model_class, '__abstract__')
        else:

            if "__label__" not in attrs:
                # generate name for node/relationship
                model_class.__label__ = name if issubclass(model_class, NodeModel) else convert_to_camel_case(name)
            model_class.__graph__ = graph

            # TODO - also find queryset managers like objects
            model_class.__all_properties__ = PropertyManager.get_properties(model_class)
            model_class.__all_relationships__ = PropertyManager.get_relationships(model_class)

            model_class.objects = model_class.objects(graph, model_class)
        return model_class


def display_for(key):
    def display_choice(self):
        return getattr(self.__class__, key).choices[getattr(self, key)]

    return display_choice


class ModelBase(metaclass=ModelMetaBase):
    __label__ = None
    __graph__ = None
    __abstract__ = True
    _id = None

    def __init__(self, *args, **kwargs):

        properties = getattr(self, "__all_properties__", None)

        if "id" in kwargs:
            self._id = kwargs["id"]
            del kwargs['id']

        for name, prop in properties.items():
            if kwargs.get(name) is None:
                if getattr(prop, 'default', False):
                    setattr(self, name, prop.default)
                else:
                    setattr(self, name, None)
            else:
                setattr(self, name, kwargs[name])

            # if getattr(prop, 'choices', None):
            #     setattr(self, 'get_{0}_display'.format(name),
            #             types.MethodType(display_for(name), self))

            if name in kwargs:
                del kwargs[name]

        # # undefined properties (for magic @prop.setters etc)
        # for name, property in kwargs.items():
        #     setattr(self, name, property)

        super(ModelBase, self).__init__(*args, **kwargs)

    def translate_node_to_model_object(cls, node):
        properties = node.properties
        props = {"id": node.id}
        for key, prop in cls.__all_properties__.items():
            if hasattr(properties, key):
                props[key] = getattr(properties, key)
            else:
                props[key] = None
            # TODO - may be add validation again ? not sure because this is retrieved from db
            #  and serialised/validated already - validate required / default fields ?
            # TODO - check if data retrieved from db is validated?
            # map property name from database to object property
            #
            # if key in node_properties:
            #     props[key] = prop.inflate(node_properties[key], node)
            # elif prop.has_default:
            #     props[key] = prop.default_value()
            # else:
            #     props[key] = None

        new_node = cls(**props)

        # TODO - add model_instance
        a = dir(new_node)
        for k in dir(new_node):
            if not k.startswith("_"):
                v = getattr(new_node, k)
                # if type(v) is object and  isinstance(v, NodeModalQuerySet):
                #     pass
                if isinstance(v, NodeRelationshipQuerySet):
                    setattr(v, "node_model", new_node)
        return new_node

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        raise AttributeError('Operation Denied. assigning id after init not allowed.')

    # def __setattr__(self, name, value):
    #     if name == 'id':
    #         raise AttributeError("Operation Denied. assigning id after init not allowed.")
    #     else:
    #         object.__setattr__(self, name, value)

    def check_if_unsaved_object(self):
        raise NotImplementedError()

    def check_if_has_id(self):
        raise NotImplementedError()

    def save(self):
        # save the
        pass

    def delete(self):
        pass

    @classmethod
    def get_property_keys(cls):
        return cls.__all_properties__.keys()

    @classmethod
    def get_properties(cls):
        return cls.__all_properties__

    def __eq__(self, other):
        if not isinstance(other, (NodeModel,)):
            return False
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class NodeModel(ModelBase):
    """
    class Meta:
        invana = None
    """
    objects = NodeModalQuerySet
    __abstract__ = True

    @classmethod
    def get_schema(cls):
        return graph.backend.schame_reader.get_vertex_schema(cls.__label__)


class RelationshipModel(ModelBase):
    objects = RelationshipModalQuerySet
    __abstract__ = True
    _inv = None
    _outv = None

    # __label__ = None
    # __graph__ = None

    def __init__(self, *args, **kwargs):
        if "inv" in kwargs:
            self._inv = kwargs["inv"]
        if "outv" in kwargs:
            self._outv = kwargs["outv"]
        super(RelationshipModel, self).__init__(*args, **kwargs)

    @classmethod
    def get_schema(cls):
        # TODO - make graph to cls.__graph__
        return graph.backend.schame_reader.get_edge_schema(cls.__label__)

    @property
    def inv(self):
        return self._id

    @inv.setter
    def inv(self, value):
        raise AttributeError('Operation Denied. assigning inv after init not allowed.')

    @property
    def outv(self):
        return self._id

    @outv.setter
    def outv(self, value):
        raise AttributeError('Operation Denied. assigning outv after init not allowed.')

    # @classmethod
    # def get_property_keys(cls):
    #     return cls.__all_properties__.keys()
    #
    # @classmethod
    # def get_properties(cls):
    #     return cls.__all_properties__
    #
    # def __eq__(self, other):
    #     if not isinstance(other, (RelationshipModel,)):
    #         return False
    #     if hasattr(self, 'id') and hasattr(other, 'id'):
    #         return self.id == other.id
    #     return False
    #
    # def __ne__(self, other):
    #     return not self.__eq__(other)


class NodeRelationshipQuerySet:
    model = None
    direction = None
    relationship_model = None
    cardinality = None
    queryset = None

    def __init__(self, node_model: [NodeModel], relationship_model: [RelationshipModel], direction, cardinality):
        self.node_model = node_model
        self.direction = direction
        self.relationship_model = relationship_model
        self.cardinality = cardinality
        self.queryset = RelationshipModalQuerySet(graph, relationship_model)

    def add_relationship(self, node, **properties):
        # TODO - add validations if .id exist for self.model and node. or if any of the
        # objects is unsaved object
        args = []
        if self.direction == Direction.OUTGOING:
            args = [self.node_model.id, node.id]
        elif self.direction == Direction.INCOMING:
            args = [node.id, self.node_model.id]
        return self.relationship_model.objects.create(*args, **properties)

    def remove_relationship(self):
        pass

    def has_relationship(self):
        pass

    def update_relationship(self):
        pass


def create_node_relationship_manager(node_model, relationship_model, direction, cardinality=None):
    if not issubclass(node_model, (str, NodeModel)):
        raise ValueError(f'model must be a NodeModel or str; got {repr(node_model)}')

    if not issubclass(relationship_model, (RelationshipModel,)):
        raise ValueError(f'relationship_model must be a RelationshipModel instance; got {repr(relationship_model)}')

    return NodeRelationshipQuerySet(node_model, relationship_model, direction, cardinality=cardinality)


RelationshipTo = lambda node_model, relationship_model, cardinality=None: create_node_relationship_manager(node_model,
                                                                                                           relationship_model,
                                                                                                           Direction.OUTGOING,
                                                                                                           cardinality)

RelationshipFrom = lambda node_model, relationship_model, cardinality=None: create_node_relationship_manager(node_model,
                                                                                                             relationship_model,
                                                                                                             Direction.INCOMING,
                                                                                                             cardinality)

RelationshipUndirected = lambda node_model, relationship_model, cardinality=None: create_node_relationship_manager(
    node_model,
    relationship_model,
    Direction.UNDIRECTED,
    cardinality)
