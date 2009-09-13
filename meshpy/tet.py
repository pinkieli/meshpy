from meshpy.common import MeshInfoBase, dump_array
import meshpy._tetgen as internals




class MeshInfo(internals.MeshInfo, MeshInfoBase):
    def set_facets(self, facets, markers=None):
        """Set a list of simple, single-polygon factes. Unlike L{set_facets_ex},
        C{set_facets} does not allow hole and only lets you use a single
        polygon per facet.

        @param facets: a list of facets, where each facet is a single 
          polygons, represented by a list of point indices.
        @param markers: Either None or a list of integers of the same
          length as C{facets}. Each integer is the facet marker assigned
          to its corresponding facet.

        @note: When the above says "list", any repeatable iterable 
          also accepted instead.
        """

        if markers:
            assert len(markers) == len(facets)

        self.facets.resize(len(facets))

        for i, vlist in enumerate(facets):
            facet = self.facets[i]
            polys = facet.polygons
            polys.resize(1)
            poly = facet.polygons[0]
            poly.vertices.resize(len(vlist))
            for j, pt_idx in enumerate(vlist):
                poly.vertices[j] = pt_idx

        if markers:
            self.facet_markers.setup()
            for i, mark in enumerate(markers):
                self.facet_markers[i] = mark

    def set_facets_ex(self, facets, facet_holestarts=None, markers=None):
        """Set a list of complicated factes. Unlike L{set_facets},
        C{set_facets_ex()} allows holes and multiple polygons per
        facet.

        @param facets: a list of facets, where each facet is a list
          of polygons, and each polygon is represented by a list
          of point indices.
        @param facet_holestarts: Either None or a list of hole starting points
          for each facet. Each facet may have several hole starting points.
          The mesh generator starts "eating" a hole into the facet at each 
          starting point and continues until it hits a polygon specified
          in this facet's record in C{facets}.
        @param markers: Either None or a list of integers of the same
          length as C{facets}. Each integer is the facet marker assigned
          to its corresponding facet.

        @note: When the above says "list", any repeatable iterable 
          also accepted instead.
        """

        if markers:
            assert len(markers) == len(facets)
        if facet_holestarts is not None:
            assert len(facet_holestarts) == len(facets)

        self.facets.resize(len(facets))
        for i_facet, poly_list in enumerate(facets):
            facet = self.facets[i_facet]
            polys = facet.polygons

            polys.resize(len(poly_list))
            for i_poly, vertex_list in enumerate(poly_list):
                poly = facet.polygons[i_poly]

                poly.vertices.resize(len(vertex_list))
                for i_point, point in enumerate(vertex_list):
                    poly.vertices[i_point] = point

            if facet_holestarts is not None:
                hole_list = facet_holestarts[i_facet]
                facet_holes = facet.holes
                facet_holes.resize(len(hole_list))
                for i_hole, hole_start in enumerate(hole_list):
                    for i_coordinate, co_value in enumerate(hole_start):
                        facet_holes[i_hole, i_coordinate] = co_value

        if markers:
            self.facet_markers.setup()
            for i, mark in enumerate(markers):
                self.facet_markers[i] = mark

    def dump(self):
        for name in ["points"]:
            dump_array(name, getattr(self, name))
        for ifacet, facet in enumerate(self.faces):
            print "facet %d:" % ifacet
            for ipolygon, polygon in enumerate(facet.polygons):
                print "  polygon %d: vertices [%s]" % \
                        (ipolygon, ",".join(str(vi) for vi in polygon.vertices))

    def write_vtk(self, filename):
        import pyvtk
        vtkelements = pyvtk.VtkData(
            pyvtk.UnstructuredGrid(
              self.points, 
              tetra=self.elements),
            "Mesh")
        vtkelements.tofile(filename)

    def set_elements(self, elements):
        self.elements.resize(len(elements))
        
        for i, element in enumerate(elements):
            self.elements[i] = element
            
    def set_element_constraints(self, element_constraints):
        self.element_volumes.setup()
        
        for i in xrange(len(self.element_volumes)):
            if i in element_constraints:
                self.element_volumes[i] = element_constraints[i]
            else:
                self.element_volumes[i] = -1




class Options(internals.Options):
    def __init__(self, switches, **kwargs):
        internals.Options.__init__(self)
        if len(switches) == 0:
            from warnings import warn
            warn("Recommend non-empty 'switches' for crash-free meshing")
        self.parse_switches(switches)
        self.quiet = 1

        for k, v in kwargs.iteritems():
            try:
                getattr(self, k)
            except AttributeError:
                raise ValueError, "invalid option: %s" % k
            else:
                setattr(self, k, v)





def _PBCGroup_get_transmat(self):
    import numpy
    return numpy.array(
            [[self.get_transmat_entry(i,j) 
                for j in xrange(4)]
                for i in xrange(4)])




def _PBCGroup_set_transmat(self, matrix):
    for i in xrange(4):
        for j in xrange(4):
            self.set_transmat_entry(i, j, matrix[i,j])




def _PBCGroup_set_transform(self, matrix=None, translation=None):
    for i in xrange(4):
        for j in xrange(4):
            self.set_transmat_entry(i, j, 0)

    self.set_transmat_entry(3, 3, 1)

    if matrix is not None:
        for i in xrange(3):
            for j in xrange(3):
                self.set_transmat_entry(i, j, matrix[i][j])
    else:
        for i in xrange(3):
            self.set_transmat_entry(i, i, 1)

    if translation is not None:
        for i in xrange(3):
            self.set_transmat_entry(i, 3, translation[i])


    

internals.PBCGroup.matrix = property(
        _PBCGroup_get_transmat,
        _PBCGroup_set_transmat)
internals.PBCGroup.set_transform = _PBCGroup_set_transform




def tetrahedralize(mesh_info, options):
    mesh = MeshInfo()
    internals.tetrahedralize(options, mesh_info, mesh)
    return mesh



def build(mesh_info, options=Options("pq"), verbose=False, 
        attributes=False, volume_constraints=False, max_volume=None,
        diagnose=False):
    if not verbose:
        options.quiet = 1

    if attributes:
        options.regionattrib = 1
    if volume_constraints:
        options.varvolume = 1
    if max_volume:
        options.fixedvolume = 1
        options.maxvolume = max_volume
    if diagnose:
        options.diagnose = 1

    return tetrahedralize(mesh_info, options)

