import json
from geometry.point import Point
from geometry.segments.line import Line
from geometry.segments.polyline import Polyline


class HeFile():

    @staticmethod
    def saveFile(_shell, _filename):

        # get topological entities
        vertices = _shell.vertices
        edges = _shell.edges
        faces = _shell.faces

        # create/ open a file
        split_name = _filename.split('.')
        if split_name[-1] == 'json':
            file = open(f"{_filename}", "w")
        else:
            file = open(f"{_filename}.json", "w")

        # save the vertices
        vertices_list = []
        for vertex in vertices:
            vertex_dict = {
                'type': 'VERTEX',
                'ID': vertex.ID,
                'point': (vertex.point.getX(), vertex.point.getY())
            }
            vertices_list.append(vertex_dict)

        # save the edges
        edges_list = []
        for edge in edges:

            edge_pts = edge.segment.getPoints()
            pts = []
            for pt in edge_pts:
                pts.append([pt.getX(), pt.getY()])

            edge_dict = {
                'type': 'EDGE',
                'subtype': f'{edge.segment.getType()}',
                'ID': edge.ID,
                'points': pts
            }

            edges_list.append(edge_dict)

        entities = {
            'vertices': vertices_list,
            'edges': edges_list
        }

        json.dump(entities, file, indent=4)
        file.close()

    @staticmethod
    def loadFile(_file):
        with open(_file, 'r') as file:
            input = json.load(file)

        vertices = input['vertices']
        edges = input['edges']

        points_list = []
        for vertex in vertices:
            pt = vertex['point']
            points_list.append(Point(pt[0], pt[1]))

        segments_list = []
        for edge in edges:
            edge_pts = edge['points']
            pts = []
            for pt in edge_pts:
                pts.append(Point(pt[0], pt[1]))

            type = edge['subtype']

            if type == 'LINE':
                segment = Line(pts[0], pts[1])
            elif type == 'POLYLINE':
                segment = Polyline(pts)

            segments_list.append(segment)

        return points_list, segments_list
