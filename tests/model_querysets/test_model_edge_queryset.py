from invana_py import InvanaGraph
from invana_py.ogm.fields import StringProperty, IntegerProperty, DateTimeProperty
from invana_py.ogm.models import EdgeModel, VertexModel
from invana_py.serializer.element_structure import Node, RelationShip
from datetime import datetime

gremlin_url = "ws://megamind-ws:8182/gremlin"
graph = InvanaGraph(gremlin_url)


class Project(VertexModel):
    graph = graph
    properties = {
        'name': StringProperty(max_length=30, trim_whitespaces=True),
        'description': StringProperty(allow_null=True, min_length=10),
        'created_at': DateTimeProperty(default=lambda: datetime.now())
    }


class Person(VertexModel):
    graph = graph

    properties = {
        'first_name': StringProperty(min_length=5, trim_whitespaces=True),
        'last_name': StringProperty(allow_null=True),
        'username': StringProperty(default="rrmerugu"),
        'member_since': IntegerProperty(),

    }


class Organisation(VertexModel):
    graph = graph

    properties = {
        'name': StringProperty(min_length=3, trim_whitespaces=True),
    }


class Authored(EdgeModel):
    graph = graph

    properties = {
        'name': StringProperty(min_length=3, trim_whitespaces=True),
        'created_at': DateTimeProperty(default=lambda: datetime.now())
    }


class TestEdgeModelQuerySet:

    def test_create(self):
        graph.g.V().drop().iterate()
        person = Person.objects.create(first_name="Ravi Raja", last_name="Merugu", member_since=2000)
        project = Project.objects.create(name="invana-engine")
        authored_single = Authored.objects.create(person.id, project.id, name=f"link-for-invana-engine")
        assert isinstance(person, Node)
        assert isinstance(project, Node)
        assert isinstance(authored_single, RelationShip)
        graph.g.V().drop().iterate()

    def test_search(self):
        graph.g.V().drop().iterate()
        person = Person.objects.create(first_name="Ravi Raja", last_name="Merugu", member_since=2000)
        for project_name in ["invana-engine", "invana-studio"]:
            project = Project.objects.create(name=project_name)
            authored_single = Authored.objects.create(person.id, project.id, name=f"link-for-{project_name}")
            assert isinstance(person, Node)
            assert isinstance(project, Node)
            assert isinstance(authored_single, RelationShip)

        authored_list = Authored.objects.search(has__name="link-for-invana-studio").value_list()
        for authored_item in authored_list:
            assert authored_item.properties.name == "link-for-invana-studio"
        graph.g.V().drop().iterate()

    def test_update(self):
        graph.g.V().drop().iterate()
        person = Person.objects.create(first_name="Ravi Raja", last_name="Merugu", member_since=2000)
        project = Project.objects.create(name="invana-engine")
        Authored.objects.create(person.id, project.id, name=f"link-for-invana-engine")
        updated_authored = Authored.objects.search(has__name="link-for-invana-studio").update(
            name="link-for-invana-studio-updated")

        for authored_item in updated_authored:
            assert authored_item.properties.name == "link-for-invana-studio-updated"
        graph.g.V().drop().iterate()

    def test_delete(self):
        graph.g.V().drop().iterate()
        person = Person.objects.create(first_name="Ravi Raja", last_name="Merugu", member_since=2000)
        for project_name in ["invana-engine", "invana-studio"]:
            project = Project.objects.create(name=project_name)
            authored_single = Authored.objects.create(person.id, project.id, name=f"link-for-{project_name}")
            assert isinstance(person, Node)
            assert isinstance(project, Node)
            assert isinstance(authored_single, RelationShip)

        Authored.objects.delete(has__name="link-for-invana-studio")
        authored_list = Authored.objects.search(has__name="link-for-invana-studio").to_list()
        assert authored_list.__len__() == 0
        authored_list = Authored.objects.search().to_list()
        assert authored_list.__len__() > 0
        graph.g.V().drop().iterate()
