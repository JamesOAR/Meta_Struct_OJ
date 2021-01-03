import cProfile
import io
import pstats

import numexpr as ne
import numpy as np
from hilbertcurve.hilbertcurve import HilbertCurve
from scipy.spatial import Voronoi, Delaunay, ConvexHull
from sklearn.neighbors import NearestNeighbors

from Objects.Shapes.Cube import Cube
from Objects.Shapes.Line import Line
from Objects.Shapes.Shape import Shape


def profile(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return wrapper


class StrutLattice(Shape):
    def __init__(self, designSpace, r=0.02, point_cloud=None, blend=0):
        super().__init__(designSpace)
        self.r = r
        self.n_lines = 0
        self.lines = []
        self.blend = blend

        if point_cloud is not None:
            if point_cloud.points == []:
                raise ValueError('Point cloud has no points.')
            self.point_cloud = point_cloud
            self.points = self.point_cloud.points

    def generateLattice(self):

        self.n_lines = len(self.lines)

        try:

            initial_line = Line(self.designSpace, self.lines[0][0], self.lines[0][1], r=self.r)

        except IndexError:

            print('No line points found.')

            raise

        print(f'Generating Lattice with {self.n_lines} lines...')

        initial_line.evaluateGrid(verbose=False)

        self.evaluatedGrid = initial_line.evaluatedGrid

        for line in self.lines:
            self.evaluatedGrid = next(self.newGrid(line))

    def newGrid(self, line):

        line = Line(self.designSpace, line[0], line[1], r=self.r)

        line.evaluateGrid(verbose=False)

        line_grid = line.evaluatedGrid

        grid = self.evaluatedGrid

        if self.blend == 0:

            yield ne.evaluate('where(grid<line_grid, grid, line_grid)')

        else:
            b = self.blend
            yield ne.evaluate(
                '-log(where((exp(-b*line_grid) + exp(-b*grid))>0.000, exp(-b*line_grid) + exp(-b*grid), 0.000))/b')


class RandomLattice(StrutLattice):

    def __init__(self, designSpace, point_cloud, num_neighbours=4, radius=None, r=0.02):
        super().__init__(designSpace, r, point_cloud)

        self.num_neighbours = num_neighbours
        self.radius = radius

        self.xLims = [min(self.points[:, 0]), max(self.points[:, 0])]
        self.yLims = [min(self.points[:, 1]), max(self.points[:, 1])]
        self.zLims = [min(self.points[:, 2]), max(self.points[:, 2])]

        if self.num_neighbours is not None:

            self.neighbours = NearestNeighbors(n_neighbors=self.num_neighbours).fit(self.points)

            _, self.node_list = self.neighbours.kneighbors(self.points)

            self.node_list = np.array(self.node_list)

        else:

            self.neighbours = NearestNeighbors(radius=self.radius).fit(self.points)

            _, self.node_list = self.neighbours.radius_neighbors(self.points)

        nodes_dict = {i: [] for i in range(len(self.node_list))}

        for i in range(len(self.node_list)):

            for other_node in range(1, len(self.node_list[i])):
                nodes_dict[i].append(self.node_list[i][other_node])

        for node in nodes_dict.keys():

            for element in nodes_dict[node]:

                if node in nodes_dict[element]:
                    nodes_dict[element].remove(node)

        for node in nodes_dict.keys():

            p1 = self.points[node]

            for other_node in nodes_dict[node]:

                p2 = self.points[other_node]

                if (p1 != p2).any():
                    self.lines.append([p1, p2])

        self.generateLattice()


class Hilbert(StrutLattice):

    def __init__(self, designSpace, cube: Cube, n_dims: int = 3, iterations: int = 2, r: float = 0.02):
        super().__init__(designSpace, r)
        self.n_dims = n_dims
        self.iterations = iterations
        self.xLims = cube.xLims
        self.yLims = cube.yLims
        self.zLims = cube.zLims

        self.hilbert_curve = HilbertCurve(self.iterations, self.n_dims)
        distances = np.array(range(2 ** (self.iterations * self.n_dims)))

        points = np.array(self.hilbert_curve.points_from_distances(distances)) / (2 ** (self.iterations))

        for i in range(len(points)):

            if i < len(points) - 1:
                self.lines.append([points[i], points[i + 1]])

        self.generateLattice()


class DelaunayLattice(StrutLattice):

    def __init__(self, designSpace, point_cloud=None, r=0.02):
        super().__init__(designSpace, r, point_cloud)

        self.designSpace = designSpace
        self.point_cloud = point_cloud
        self.delaunay = Delaunay(self.point_cloud.points, qhull_options='Qbb Qc Qx QJ')

        self.xLims = self.point_cloud.shape.xLims
        self.yLims = self.point_cloud.shape.yLims
        self.zLims = self.point_cloud.shape.zLims

        for simplex in self.delaunay.simplices:
            line1 = [self.delaunay.points[simplex[0]], self.delaunay.points[simplex[1]]]
            line2 = [self.delaunay.points[simplex[1]], self.delaunay.points[simplex[2]]]
            line3 = [self.delaunay.points[simplex[2]], self.delaunay.points[simplex[3]]]
            line4 = [self.delaunay.points[simplex[3]], self.delaunay.points[simplex[0]]]
            self.lines.append(line1)
            self.lines.append(line2)
            self.lines.append(line3)
            self.lines.append(line4)

        self.generateLattice()


class ConvexHullLattice(StrutLattice):

    def __init__(self, designSpace, point_cloud=None, r=0.02):
        super().__init__(designSpace, r, point_cloud)

        self.designSpace = designSpace
        self.point_cloud = point_cloud
        self.convex_hull = ConvexHull(self.point_cloud.points)

        self.xLims = self.point_cloud.shape.xLims
        self.yLims = self.point_cloud.shape.yLims
        self.zLims = self.point_cloud.shape.zLims

        self.flat_simplices = [item for simplex in self.convex_hull.simplices for item in simplex]

        for simplex in self.convex_hull.simplices:
            line1 = [self.convex_hull.points[simplex[0]], self.convex_hull.points[simplex[1]]]
            line2 = [self.convex_hull.points[simplex[1]], self.convex_hull.points[simplex[2]]]
            line3 = [self.convex_hull.points[simplex[2]], self.convex_hull.points[simplex[0]]]
            self.lines.append(line1)
            self.lines.append(line2)
            self.lines.append(line3)

        # TODO: Remove duplicate lines from self.lines

        self.generateLattice()


class VoronoiLattice(StrutLattice):

    def __init__(self, designSpace, point_cloud=None, r=0.02):
        super().__init__(designSpace, r, point_cloud)

        self.voronoi = Voronoi(self.point_cloud.points, qhull_options='Qbb Qc Qx')

        self.xLims = self.point_cloud.shape.xLims
        self.yLims = self.point_cloud.shape.yLims
        self.zLims = self.point_cloud.shape.zLims

        self.flat_ridges = [item for ridge in self.voronoi.ridge_vertices for item in ridge if item != -1]

        for i in range(len(self.flat_ridges)):
            p1 = self.voronoi.vertices[self.flat_ridges[i]]
            if i < len(self.flat_ridges) - 1:
                p2 = self.voronoi.vertices[self.flat_ridges[i + 1]]
            else:
                p2 = self.voronoi.vertices[self.flat_ridges[0]]
            self.lines.append([p1, p2])

        self.generateLattice()


class RegularStrutLattice(StrutLattice):

    def __init__(self, designSpace, n_cells=[1, 1, 1], shape=None, r=0.05):
        super().__init__(designSpace, r)
        self.shape = shape
        self.origin = np.array((min(self.shape.xLims), min(self.shape.yLims), min(self.shape.zLims)))
        self.n_cells = n_cells

        self.xLims = self.shape.xLims
        self.yLims = self.shape.yLims
        self.zLims = self.shape.zLims

        self.xScale = max(self.shape.xLims) - min(self.shape.xLims)
        self.yScale = max(self.shape.yLims) - min(self.shape.yLims)
        self.zScale = max(self.shape.zLims) - min(self.shape.zLims)

        self.generate_points()

    def generate_points(self):
        origin = self.origin
        dx = self.xScale / self.n_cells[0]
        dy = self.yScale / self.n_cells[1]
        dz = self.zScale / self.n_cells[2]

        cell = [
            origin,
            origin + np.array([dx, 0, 0]),
            origin + np.array([dx, dy, 0]),
            origin + np.array([0, dy, 0]),
            origin + np.array([0, 0, dz]),
            origin + np.array([dx, 0, dz]),
            origin + np.array([dx, dy, dz]),
            origin + np.array([0, dy, dz]),
            origin + np.array([dx / 2, dy / 2, dz / 2])
        ]

        p2 = cell[len(cell) - 1]

        for i in range(len(cell) - 1):
            p1 = cell[i]
            self.lines.append([p1, p2])

        self.generateLattice()
